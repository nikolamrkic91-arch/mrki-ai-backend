"""
Mrki Local Inference - GPU-Accelerated Local Model Execution

Implements local inference with support for:
- CUDA (NVIDIA GPUs)
- Metal (Apple Silicon)
- ROCm (AMD GPUs)
- CPU fallback with optimizations
- Batch inference
- Streaming generation
- KV-cache management
"""

import torch
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Iterator, Callable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
from contextlib import contextmanager
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Supported device types."""
    CUDA = "cuda"
    METAL = "mps"  # Metal Performance Shaders
    ROCM = "rocm"
    CPU = "cpu"


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    device: str = "auto"
    dtype: torch.dtype = torch.float16
    max_batch_size: int = 16
    max_sequence_length: int = 8192
    max_new_tokens: int = 512
    
    # Generation parameters
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.0
    
    # Performance
    use_cache: bool = True
    use_flash_attention: bool = True
    compile_model: bool = False
    
    # Memory
    max_memory_mb: int = 16384
    enable_memory_efficient_attention: bool = True
    
    # Streaming
    stream_interval: int = 4


@dataclass
class GenerationResult:
    """Result of text generation."""
    text: str
    tokens: List[int]
    generation_time_ms: float
    tokens_per_second: float
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


@dataclass
class BatchGenerationResult:
    """Result of batch text generation."""
    results: List[GenerationResult]
    total_time_ms: float
    total_tokens: int
    throughput_tps: float


class KVCacheManager:
    """
    Manages KV cache for efficient inference.
    
    Implements:
    - Cache allocation and reuse
    - Cache eviction strategies
    - Multi-sequence cache management
    """
    
    def __init__(
        self,
        num_layers: int,
        num_heads: int,
        head_dim: int,
        max_batch_size: int = 16,
        max_seq_len: int = 8192,
        dtype: torch.dtype = torch.float16
    ):
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.max_batch_size = max_batch_size
        self.max_seq_len = max_seq_len
        self.dtype = dtype
        
        self._cache: Dict[str, Tuple[torch.Tensor, torch.Tensor]] = {}
        self._cache_seq_lengths: Dict[str, int] = {}
        self._lock = threading.Lock()
        
    def allocate_cache(self, cache_key: str, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Allocate or retrieve cache for a sequence."""
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Allocate new cache
            k_cache = torch.zeros(
                batch_size, self.num_heads, self.max_seq_len, self.head_dim,
                dtype=self.dtype
            )
            v_cache = torch.zeros(
                batch_size, self.num_heads, self.max_seq_len, self.head_dim,
                dtype=self.dtype
            )
            
            self._cache[cache_key] = (k_cache, v_cache)
            self._cache_seq_lengths[cache_key] = 0
            
            return k_cache, v_cache
    
    def get_cache(self, cache_key: str) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
        """Get existing cache."""
        with self._lock:
            return self._cache.get(cache_key)
    
    def update_seq_length(self, cache_key: str, new_length: int):
        """Update sequence length for cache."""
        with self._lock:
            self._cache_seq_lengths[cache_key] = new_length
    
    def get_seq_length(self, cache_key: str) -> int:
        """Get current sequence length for cache."""
        with self._lock:
            return self._cache_seq_lengths.get(cache_key, 0)
    
    def free_cache(self, cache_key: str):
        """Free cache for a sequence."""
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                del self._cache_seq_lengths[cache_key]
    
    def clear_all(self):
        """Clear all caches."""
        with self._lock:
            self._cache.clear()
            self._cache_seq_lengths.clear()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage of caches."""
        total_elements = 0
        for k_cache, v_cache in self._cache.values():
            total_elements += k_cache.numel() + v_cache.numel()
        
        bytes_per_element = 2 if self.dtype == torch.float16 else 4
        memory_mb = (total_elements * bytes_per_element) / (1024 ** 2)
        
        return {
            "num_caches": len(self._cache),
            "memory_mb": memory_mb,
            "total_elements": total_elements
        }


class DeviceManager:
    """
    Manages device detection and optimization.
    """
    
    def __init__(self):
        self.device = self._detect_device()
        self.device_type = self._get_device_type()
        
    def _detect_device(self) -> str:
        """Detect the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _get_device_type(self) -> DeviceType:
        """Get device type enum."""
        if self.device == "cuda":
            if torch.version.hip:
                return DeviceType.ROCM
            return DeviceType.CUDA
        elif self.device == "mps":
            return DeviceType.METAL
        return DeviceType.CPU
    
    def get_optimal_dtype(self) -> torch.dtype:
        """Get optimal dtype for the device."""
        if self.device_type == DeviceType.CUDA:
            # Check if bfloat16 is supported
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16
        elif self.device_type == DeviceType.METAL:
            return torch.float16
        return torch.float32
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        info = {
            "device": self.device,
            "device_type": self.device_type.value,
        }
        
        if self.device_type == DeviceType.CUDA:
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory_mb"] = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
            info["cuda_version"] = torch.version.cuda
            info["num_gpus"] = torch.cuda.device_count()
        elif self.device_type == DeviceType.ROCM:
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["rocm_version"] = torch.version.hip
        elif self.device_type == DeviceType.METAL:
            info["backend"] = "Metal Performance Shaders"
        
        return info
    
    def optimize_for_device(self, model: torch.nn.Module) -> torch.nn.Module:
        """Apply device-specific optimizations."""
        if self.device_type == DeviceType.CUDA:
            # Enable TF32 for better performance on Ampere+
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            
            # Enable cudnn benchmarking
            torch.backends.cudnn.benchmark = True
            
        elif self.device_type == DeviceType.METAL:
            # Metal-specific optimizations
            pass
            
        elif self.device_type == DeviceType.CPU:
            # Enable MKL-DNN optimizations
            torch.set_num_threads(torch.get_num_threads())
        
        return model


class LocalInferenceEngine:
    """
    Main inference engine for local model execution.
    
    Features:
    - Multi-device support (CUDA, Metal, ROCm, CPU)
    - Optimized generation with KV caching
    - Batch inference
    - Streaming generation
    - Memory-efficient attention
    """
    
    def __init__(self, config: Optional[InferenceConfig] = None):
        self.config = config or InferenceConfig()
        self.device_manager = DeviceManager()
        
        # Auto-configure device
        if self.config.device == "auto":
            self.config.device = self.device_manager.device
            self.config.dtype = self.device_manager.get_optimal_dtype()
        
        self.kv_cache_manager: Optional[KVCacheManager] = None
        self.model: Optional[torch.nn.Module] = None
        self.tokenizer: Optional[Any] = None
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_time_ms = 0.0
        
        logger.info(f"InferenceEngine initialized on {self.config.device}")
    
    def load_model(self, model: torch.nn.Module, tokenizer: Any):
        """Load a model for inference."""
        self.model = model.to(self.config.device)
        self.tokenizer = tokenizer
        
        # Apply device optimizations
        self.model = self.device_manager.optimize_for_device(self.model)
        
        # Initialize KV cache manager
        if hasattr(model.config, 'num_hidden_layers'):
            self.kv_cache_manager = KVCacheManager(
                num_layers=model.config.num_hidden_layers,
                num_heads=getattr(model.config, 'num_attention_heads', 32),
                head_dim=getattr(model.config, 'hidden_size', 4096) // 
                        getattr(model.config, 'num_attention_heads', 32),
                max_batch_size=self.config.max_batch_size,
                max_seq_len=self.config.max_sequence_length,
                dtype=self.config.dtype
            )
        
        # Compile model if requested (PyTorch 2.0+)
        if self.config.compile_model and hasattr(torch, 'compile'):
            logger.info("Compiling model with torch.compile...")
            self.model = torch.compile(self.model, mode="reduce-overhead")
        
        logger.info("Model loaded successfully")
    
    @torch.inference_mode()
    def generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        cache_key: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            stop_sequences: Sequences to stop generation
            cache_key: Key for KV cache reuse
            
        Returns:
            GenerationResult with generated text and metadata
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        # Use config defaults if not specified
        max_new_tokens = max_new_tokens or self.config.max_new_tokens
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p
        top_k = top_k if top_k is not None else self.config.top_k
        repetition_penalty = repetition_penalty or self.config.repetition_penalty
        
        # Tokenize prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.config.device)
        prompt_tokens = input_ids.shape[1]
        
        # Get or create cache
        past_key_values = None
        if cache_key and self.kv_cache_manager:
            cache = self.kv_cache_manager.get_cache(cache_key)
            if cache:
                # Use cached KV
                pass  # Implementation depends on model architecture
        
        # Generate
        generated_tokens = []
        finish_reason = "length"
        
        for i in range(max_new_tokens):
            # Forward pass
            outputs = self.model(
                input_ids if i == 0 else input_ids[:, -1:],
                past_key_values=past_key_values,
                use_cache=self.config.use_cache
            )
            
            logits = outputs.logits[:, -1, :]
            past_key_values = outputs.past_key_values if self.config.use_cache else None
            
            # Apply repetition penalty
            if repetition_penalty != 1.0:
                logits = self._apply_repetition_penalty(
                    logits, input_ids, repetition_penalty
                )
            
            # Sample
            next_token = self._sample_token(
                logits, temperature, top_p, top_k
            )
            
            generated_tokens.append(next_token.item())
            input_ids = torch.cat([input_ids, next_token.unsqueeze(0)], dim=1)
            
            # Check stop sequences
            if stop_sequences:
                current_text = self.tokenizer.decode(generated_tokens)
                for stop_seq in stop_sequences:
                    if stop_seq in current_text:
                        finish_reason = "stop"
                        break
                if finish_reason == "stop":
                    break
            
            # Check EOS
            if next_token.item() == self.tokenizer.eos_token_id:
                finish_reason = "eos"
                break
        
        # Decode
        generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        generation_time = (time.time() - start_time) * 1000
        completion_tokens = len(generated_tokens)
        tps = completion_tokens / (generation_time / 1000) if generation_time > 0 else 0
        
        # Update cache
        if cache_key and self.kv_cache_manager:
            self.kv_cache_manager.update_seq_length(cache_key, input_ids.shape[1])
        
        # Update metrics
        self._total_requests += 1
        self._total_tokens += completion_tokens
        self._total_time_ms += generation_time
        
        return GenerationResult(
            text=generated_text,
            tokens=generated_tokens,
            generation_time_ms=generation_time,
            tokens_per_second=tps,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason
        )
    
    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate text with streaming output.
        
        Yields:
            Generated text chunks
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")
        
        # Use config defaults
        max_new_tokens = max_new_tokens or self.config.max_new_tokens
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p
        top_k = top_k if top_k is not None else self.config.top_k
        
        # Tokenize
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.config.device)
        
        generated_text = ""
        past_key_values = None
        
        for i in range(max_new_tokens):
            # Forward pass
            with torch.inference_mode():
                outputs = self.model(
                    input_ids if i == 0 else input_ids[:, -1:],
                    past_key_values=past_key_values,
                    use_cache=True
                )
            
            logits = outputs.logits[:, -1, :]
            past_key_values = outputs.past_key_values
            
            # Sample
            next_token = self._sample_token(logits, temperature, top_p, top_k)
            
            # Decode and yield
            token_text = self.tokenizer.decode([next_token.item()], skip_special_tokens=True)
            generated_text += token_text
            
            if i % self.config.stream_interval == 0:
                yield generated_text
            
            # Update input
            input_ids = torch.cat([input_ids, next_token.unsqueeze(0)], dim=1)
            
            # Check EOS
            if next_token.item() == self.tokenizer.eos_token_id:
                break
        
        # Yield final result
        yield generated_text
    
    async def generate_async(
        self,
        prompt: str,
        **kwargs
    ) -> GenerationResult:
        """Async version of generate."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.generate, 
            prompt, 
            **kwargs
        )
    
    async def generate_stream_async(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming generation."""
        queue = asyncio.Queue()
        
        def generate_to_queue():
            for chunk in self.generate_stream(prompt, **kwargs):
                asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)
        
        loop = asyncio.get_event_loop()
        self._executor.submit(generate_to_queue)
        
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
    
    @torch.inference_mode()
    def generate_batch(
        self,
        prompts: List[str],
        max_new_tokens: Optional[int] = None,
        **kwargs
    ) -> BatchGenerationResult:
        """
        Generate text for multiple prompts in batch.
        
        Args:
            prompts: List of input prompts
            max_new_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            BatchGenerationResult with all results
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        # Process in batches
        batch_size = min(len(prompts), self.config.max_batch_size)
        all_results = []
        
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i + batch_size]
            batch_results = self._generate_batch_internal(
                batch_prompts, max_new_tokens, **kwargs
            )
            all_results.extend(batch_results)
        
        total_time = (time.time() - start_time) * 1000
        total_tokens = sum(r.completion_tokens for r in all_results)
        throughput = total_tokens / (total_time / 1000) if total_time > 0 else 0
        
        return BatchGenerationResult(
            results=all_results,
            total_time_ms=total_time,
            total_tokens=total_tokens,
            throughput_tps=throughput
        )
    
    def _generate_batch_internal(
        self,
        prompts: List[str],
        max_new_tokens: Optional[int] = None,
        **kwargs
    ) -> List[GenerationResult]:
        """Internal batch generation."""
        # Tokenize with padding
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.config.max_sequence_length - (max_new_tokens or self.config.max_new_tokens)
        ).to(self.config.device)
        
        # Generate
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens or self.config.max_new_tokens,
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
                top_k=kwargs.get('top_k', self.config.top_k),
                repetition_penalty=kwargs.get('repetition_penalty', self.config.repetition_penalty),
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode results
        results = []
        for i, prompt in enumerate(prompts):
            prompt_len = inputs['input_ids'][i].shape[0]
            generated_ids = outputs[i][prompt_len:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            results.append(GenerationResult(
                text=generated_text,
                tokens=generated_ids.tolist(),
                generation_time_ms=0,  # Calculated at batch level
                tokens_per_second=0,
                prompt_tokens=prompt_len,
                completion_tokens=len(generated_ids),
                finish_reason="eos" if generated_ids[-1] == self.tokenizer.eos_token_id else "length"
            ))
        
        return results
    
    def _sample_token(
        self,
        logits: torch.Tensor,
        temperature: float,
        top_p: float,
        top_k: int
    ) -> torch.Tensor:
        """Sample a token from logits."""
        # Apply temperature
        if temperature != 1.0:
            logits = logits / temperature
        
        # Top-k filtering
        if top_k > 0:
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = float('-inf')
        
        # Top-p filtering
        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
            
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = False
            
            indices_to_remove = sorted_indices_to_remove.scatter(
                -1, sorted_indices, sorted_indices_to_remove
            )
            logits[indices_to_remove] = float('-inf')
        
        # Sample
        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        
        return next_token.squeeze(-1)
    
    def _apply_repetition_penalty(
        self,
        logits: torch.Tensor,
        input_ids: torch.Tensor,
        penalty: float
    ) -> torch.Tensor:
        """Apply repetition penalty to logits."""
        score = torch.gather(logits, 1, input_ids)
        score = torch.where(score < 0, score * penalty, score / penalty)
        logits.scatter_(1, input_ids, score)
        return logits
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        avg_latency = (
            self._total_time_ms / self._total_requests 
            if self._total_requests > 0 else 0
        )
        avg_throughput = (
            self._total_tokens / (self._total_time_ms / 1000)
            if self._total_time_ms > 0 else 0
        )
        
        stats = {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_time_ms": self._total_time_ms,
            "avg_latency_ms": avg_latency,
            "avg_throughput_tps": avg_throughput,
            "device": self.config.device,
            "dtype": str(self.config.dtype),
        }
        
        if self.kv_cache_manager:
            stats["kv_cache"] = self.kv_cache_manager.get_memory_usage()
        
        return stats
    
    def reset_stats(self):
        """Reset performance statistics."""
        self._total_requests = 0
        self._total_tokens = 0
        self._total_time_ms = 0.0
    
    def clear_cache(self):
        """Clear all caches."""
        if self.kv_cache_manager:
            self.kv_cache_manager.clear_all()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def create_inference_engine(
    device: str = "auto",
    dtype: Optional[torch.dtype] = None,
    **kwargs
) -> LocalInferenceEngine:
    """Factory function to create an inference engine."""
    config = InferenceConfig(device=device, **kwargs)
    if dtype:
        config.dtype = dtype
    return LocalInferenceEngine(config)


if __name__ == "__main__":
    # Test inference engine
    engine = create_inference_engine()
    
    print("Device Info:")
    print(engine.device_manager.get_device_info())
    
    print(f"\nConfig:")
    print(f"  Device: {engine.config.device}")
    print(f"  Dtype: {engine.config.dtype}")
