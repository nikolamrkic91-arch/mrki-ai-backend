"""
Mrki Model Loader - Model Loading and Optimization

Handles loading and optimization of open-weights models including:
- HuggingFace Transformers models (Llama, Mistral, etc.)
- llama.cpp GGUF models
- vLLM models for high-throughput inference
- Model sharding and parallel loading
- Memory-efficient loading strategies
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import json
import logging
import gc
from contextlib import contextmanager
import tempfile
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports - handle gracefully if not available
try:
    from transformers import (
        AutoModel, AutoModelForCausalLM, AutoTokenizer, 
        AutoConfig, BitsAndBytesConfig
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available")

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama_cpp not available")

try:
    from vllm import LLM, SamplingParams
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    logger.warning("vllm not available")


class ModelBackend(Enum):
    """Supported model backends."""
    TRANSFORMERS = "transformers"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"
    CUSTOM = "custom"


class ModelFormat(Enum):
    """Supported model formats."""
    PYTORCH = "pytorch"
    SAFETENSORS = "safetensors"
    GGUF = "gguf"
    GGML = "ggml"
    ONNX = "onnx"


@dataclass
class ModelConfig:
    """Configuration for model loading."""
    model_id: str
    model_path: Optional[str] = None
    model_revision: Optional[str] = None
    backend: ModelBackend = ModelBackend.TRANSFORMERS
    format: ModelFormat = ModelFormat.SAFETENSORS
    device: str = "auto"
    dtype: torch.dtype = torch.float16
    trust_remote_code: bool = False
    use_auth_token: Optional[str] = None
    
    # Memory optimization
    low_cpu_mem_usage: bool = True
    offload_folder: Optional[str] = None
    offload_state_dict: bool = False
    
    # Quantization
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    bnb_4bit_compute_dtype: torch.dtype = torch.float16
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    
    # Sharding
    max_memory_per_gpu: Optional[Dict[int, str]] = None
    device_map: Union[str, Dict[str, int]] = "auto"
    
    # vLLM specific
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.9
    max_model_len: Optional[int] = None
    
    # llama.cpp specific
    n_ctx: int = 4096
    n_gpu_layers: int = -1  # -1 = all layers
    n_batch: int = 512
    verbose: bool = False
    
    # Custom parameters
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedModel:
    """Represents a loaded model with metadata."""
    model: Any
    tokenizer: Optional[Any] = None
    config: Optional[Any] = None
    backend: ModelBackend = ModelBackend.TRANSFORMERS
    device: str = "cpu"
    dtype: torch.dtype = torch.float32
    memory_footprint_mb: float = 0.0
    load_time_seconds: float = 0.0
    model_type: str = "unknown"
    num_parameters: int = 0
    
    def get_memory_footprint(self) -> Dict[str, float]:
        """Get detailed memory footprint."""
        if self.backend == ModelBackend.TRANSFORMERS:
            if hasattr(self.model, 'get_memory_footprint'):
                return self.model.get_memory_footprint()
        return {"total": self.memory_footprint_mb}


class ModelLoader:
    """
    Unified model loader supporting multiple backends and formats.
    
    Supports:
    - HuggingFace Transformers (Llama, Mistral, etc.)
    - llama.cpp for GGUF models
    - vLLM for high-throughput inference
    - Custom model loading
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "mrki" / "models"
        self.cache_dir = Path(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._loaded_models: Dict[str, LoadedModel] = {}
        self._model_locks: Dict[str, Any] = {}
        
    def load_model(self, config: ModelConfig) -> LoadedModel:
        """
        Load a model using the specified configuration.
        
        Args:
            config: Model loading configuration
            
        Returns:
            LoadedModel instance
        """
        start_time = time.time()
        
        # Determine backend if auto
        if config.backend == ModelBackend.TRANSFORMERS and config.format == ModelFormat.GGUF:
            config.backend = ModelBackend.LLAMA_CPP
            
        logger.info(f"Loading model {config.model_id} using {config.backend.value}")
        
        if config.backend == ModelBackend.TRANSFORMERS:
            loaded = self._load_transformers(config)
        elif config.backend == ModelBackend.LLAMA_CPP:
            loaded = self._load_llama_cpp(config)
        elif config.backend == ModelBackend.VLLM:
            loaded = self._load_vllm(config)
        elif config.backend == ModelBackend.CUSTOM:
            loaded = self._load_custom(config)
        else:
            raise ValueError(f"Unknown backend: {config.backend}")
        
        loaded.load_time_seconds = time.time() - start_time
        
        # Store in cache
        self._loaded_models[config.model_id] = loaded
        
        logger.info(
            f"Loaded {config.model_id} in {loaded.load_time_seconds:.2f}s, "
            f"memory: {loaded.memory_footprint_mb:.2f}MB"
        )
        
        return loaded
    
    def _load_transformers(self, config: ModelConfig) -> LoadedModel:
        """Load model using HuggingFace Transformers."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers library not available")
        
        # Build quantization config if needed
        quantization_config = None
        if config.load_in_4bit or config.load_in_8bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=config.load_in_4bit,
                load_in_8bit=config.load_in_8bit,
                bnb_4bit_compute_dtype=config.bnb_4bit_compute_dtype,
                bnb_4bit_quant_type=config.bnb_4bit_quant_type,
                bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
            )
        
        # Determine device map
        device_map = config.device_map
        if config.device == "auto":
            device_map = "auto"
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            config.model_path or config.model_id,
            revision=config.model_revision,
            trust_remote_code=config.trust_remote_code,
            use_auth_token=config.use_auth_token,
            cache_dir=self.cache_dir
        )
        
        # Set padding token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load config
        model_config = AutoConfig.from_pretrained(
            config.model_path or config.model_id,
            revision=config.model_revision,
            trust_remote_code=config.trust_remote_code,
            use_auth_token=config.use_auth_token,
            cache_dir=self.cache_dir
        )
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            config.model_path or config.model_id,
            revision=config.model_revision,
            config=model_config,
            torch_dtype=config.dtype,
            device_map=device_map,
            max_memory=config.max_memory_per_gpu,
            offload_folder=config.offload_folder,
            offload_state_dict=config.offload_state_dict,
            quantization_config=quantization_config,
            low_cpu_mem_usage=config.low_cpu_mem_usage,
            trust_remote_code=config.trust_remote_code,
            use_auth_token=config.use_auth_token,
            cache_dir=self.cache_dir
        )
        
        # Get memory footprint
        memory_mb = 0
        if hasattr(model, 'get_memory_footprint'):
            memory_mb = model.get_memory_footprint() / (1024 ** 2)
        else:
            # Estimate from parameters
            num_params = sum(p.numel() for p in model.parameters())
            bytes_per_param = 2 if config.dtype == torch.float16 else 4
            memory_mb = (num_params * bytes_per_param) / (1024 ** 2)
        
        # Get device
        device = next(model.parameters()).device
        if hasattr(model, 'device'):
            device = model.device
        
        return LoadedModel(
            model=model,
            tokenizer=tokenizer,
            config=model_config,
            backend=ModelBackend.TRANSFORMERS,
            device=str(device),
            dtype=config.dtype,
            memory_footprint_mb=memory_mb,
            model_type=model_config.model_type,
            num_parameters=sum(p.numel() for p in model.parameters())
        )
    
    def _load_llama_cpp(self, config: ModelConfig) -> LoadedModel:
        """Load model using llama.cpp."""
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError("llama_cpp library not available")
        
        model_path = config.model_path or config.model_id
        
        # Download if needed
        if not Path(model_path).exists() and not model_path.endswith('.gguf'):
            model_path = self._download_gguf(model_path)
        
        # Determine GPU layers
        n_gpu_layers = config.n_gpu_layers
        if n_gpu_layers == -1:
            # Auto-detect based on available VRAM
            if torch.cuda.is_available():
                n_gpu_layers = 1000  # Offload all possible layers
            else:
                n_gpu_layers = 0
        
        model = Llama(
            model_path=str(model_path),
            n_ctx=config.n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_batch=config.n_batch,
            verbose=config.verbose
        )
        
        # Estimate memory (llama.cpp doesn't expose this directly)
        memory_mb = 0
        if torch.cuda.is_available():
            memory_mb = torch.cuda.memory_allocated() / (1024 ** 2)
        
        return LoadedModel(
            model=model,
            tokenizer=None,  # llama.cpp has built-in tokenization
            config=None,
            backend=ModelBackend.LLAMA_CPP,
            device="cuda" if n_gpu_layers > 0 else "cpu",
            dtype=torch.float16,
            memory_footprint_mb=memory_mb,
            model_type="llama_cpp",
            num_parameters=0  # Not exposed by llama.cpp
        )
    
    def _load_vllm(self, config: ModelConfig) -> LoadedModel:
        """Load model using vLLM."""
        if not VLLM_AVAILABLE:
            raise RuntimeError("vllm library not available")
        
        model = LLM(
            model=config.model_path or config.model_id,
            tensor_parallel_size=config.tensor_parallel_size,
            gpu_memory_utilization=config.gpu_memory_utilization,
            max_model_len=config.max_model_len,
            dtype="float16" if config.dtype == torch.float16 else "bfloat16",
            trust_remote_code=config.trust_remote_code,
            download_dir=str(self.cache_dir)
        )
        
        # Get memory info from vLLM
        memory_mb = 0
        if torch.cuda.is_available():
            memory_mb = torch.cuda.memory_allocated() / (1024 ** 2)
        
        return LoadedModel(
            model=model,
            tokenizer=model.get_tokenizer(),
            config=None,
            backend=ModelBackend.VLLM,
            device="cuda",
            dtype=config.dtype,
            memory_footprint_mb=memory_mb,
            model_type="vllm",
            num_parameters=0
        )
    
    def _load_custom(self, config: ModelConfig) -> LoadedModel:
        """Load a custom model."""
        raise NotImplementedError("Custom model loading must be implemented by user")
    
    def _download_gguf(self, model_id: str) -> str:
        """Download GGUF model from HuggingFace."""
        from huggingface_hub import hf_hub_download, list_repo_files
        
        # List files in repo
        files = list_repo_files(model_id)
        gguf_files = [f for f in files if f.endswith('.gguf')]
        
        if not gguf_files:
            raise ValueError(f"No GGUF files found in {model_id}")
        
        # Prefer Q4_K_M quantized version
        preferred = [f for f in gguf_files if 'Q4_K_M' in f]
        if preferred:
            gguf_file = preferred[0]
        else:
            # Prefer smaller quantized versions
            gguf_file = sorted(gguf_files, key=lambda x: 'Q8' in x or 'Q6' in x)[0]
        
        logger.info(f"Downloading {gguf_file} from {model_id}")
        
        path = hf_hub_download(
            repo_id=model_id,
            filename=gguf_file,
            cache_dir=self.cache_dir,
            local_dir=str(self.cache_dir / "gguf")
        )
        
        return path
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model and free memory."""
        if model_id not in self._loaded_models:
            return False
        
        loaded = self._loaded_models[model_id]
        
        # Clear model
        del loaded.model
        if loaded.tokenizer:
            del loaded.tokenizer
        
        del self._loaded_models[model_id]
        
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info(f"Unloaded model {model_id}")
        return True
    
    def get_model(self, model_id: str) -> Optional[LoadedModel]:
        """Get a loaded model by ID."""
        return self._loaded_models.get(model_id)
    
    def list_loaded_models(self) -> List[str]:
        """List all loaded model IDs."""
        return list(self._loaded_models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model."""
        loaded = self.get_model(model_id)
        if not loaded:
            return None
        
        return {
            "model_id": model_id,
            "backend": loaded.backend.value,
            "device": loaded.device,
            "dtype": str(loaded.dtype),
            "memory_footprint_mb": loaded.memory_footprint_mb,
            "model_type": loaded.model_type,
            "num_parameters": loaded.num_parameters,
            "load_time_seconds": loaded.load_time_seconds
        }


class ShardedModelLoader:
    """
    Loads large models across multiple GPUs using sharding.
    """
    
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        
    def load_sharded(
        self,
        config: ModelConfig,
        num_gpus: Optional[int] = None
    ) -> LoadedModel:
        """
        Load a model sharded across multiple GPUs.
        
        Args:
            config: Model configuration
            num_gpus: Number of GPUs to use (auto-detect if None)
            
        Returns:
            LoadedModel with sharded model
        """
        if num_gpus is None:
            num_gpus = torch.cuda.device_count()
        
        if num_gpus <= 1:
            logger.warning("Only 1 GPU available, loading without sharding")
            return self.model_loader.load_model(config)
        
        logger.info(f"Loading model sharded across {num_gpus} GPUs")
        
        # Build device map for balanced sharding
        device_map = self._build_balanced_device_map(config, num_gpus)
        
        # Update config
        config.device_map = device_map
        config.backend = ModelBackend.TRANSFORMERS
        
        return self.model_loader.load_model(config)
    
    def _build_balanced_device_map(
        self, 
        config: ModelConfig, 
        num_gpus: int
    ) -> Dict[str, int]:
        """Build a balanced device map for model sharding."""
        # Load config to get layer names
        model_config = AutoConfig.from_pretrained(
            config.model_path or config.model_id,
            trust_remote_code=config.trust_remote_code
        )
        
        # Common layer patterns
        device_map = {}
        
        # Embeddings on GPU 0
        device_map["model.embed_tokens"] = 0
        device_map["embed_tokens"] = 0
        
        # Distribute layers evenly
        num_layers = getattr(model_config, 'num_hidden_layers', 
                           getattr(model_config, 'n_layer', 32))
        
        layers_per_gpu = num_layers // num_gpus
        for i in range(num_layers):
            gpu_id = min(i // layers_per_gpu, num_gpus - 1)
            device_map[f"model.layers.{i}"] = gpu_id
            device_map[f"transformer.h.{i}"] = gpu_id
        
        # Final layers on last GPU
        device_map["model.norm"] = num_gpus - 1
        device_map["norm"] = num_gpus - 1
        device_map["lm_head"] = num_gpus - 1
        
        return device_map


class ModelRegistry:
    """
    Registry for managing available models and their configurations.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = registry_path or Path.home() / ".mrki" / "model_registry.json"
        self.registry_path = Path(self.registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._models: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                self._models = json.load(f)
    
    def _save_registry(self):
        """Save registry to disk."""
        with open(self.registry_path, 'w') as f:
            json.dump(self._models, f, indent=2)
    
    def register_model(
        self,
        model_id: str,
        name: str,
        description: str = "",
        capabilities: List[str] = None,
        default_config: Dict[str, Any] = None
    ):
        """Register a model in the registry."""
        self._models[model_id] = {
            "name": name,
            "description": description,
            "capabilities": capabilities or [],
            "default_config": default_config or {},
            "registered_at": time.time()
        }
        self._save_registry()
        logger.info(f"Registered model: {model_id}")
    
    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model."""
        if model_id not in self._models:
            return False
        del self._models[model_id]
        self._save_registry()
        return True
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered model."""
        return self._models.get(model_id)
    
    def list_models(
        self,
        capability: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List registered models, optionally filtered by capability."""
        models = []
        for model_id, info in self._models.items():
            if capability is None or capability in info.get("capabilities", []):
                models.append({"model_id": model_id, **info})
        return models
    
    def find_models_by_capability(self, capability: str) -> List[str]:
        """Find models with a specific capability."""
        return [
            model_id for model_id, info in self._models.items()
            if capability in info.get("capabilities", [])
        ]


# Predefined model configurations
PRESET_MODELS = {
    "llama-3-8b": ModelConfig(
        model_id="meta-llama/Meta-Llama-3-8B-Instruct",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto"
    ),
    "llama-3-8b-4bit": ModelConfig(
        model_id="meta-llama/Meta-Llama-3-8B-Instruct",
        backend=ModelBackend.TRANSFORMERS,
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16
    ),
    "llama-3-70b": ModelConfig(
        model_id="meta-llama/Meta-Llama-3-70B-Instruct",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto"
    ),
    "mistral-7b": ModelConfig(
        model_id="mistralai/Mistral-7B-Instruct-v0.2",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto"
    ),
    "mixtral-8x7b": ModelConfig(
        model_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto"
    ),
    "phi-3-mini": ModelConfig(
        model_id="microsoft/Phi-3-mini-4k-instruct",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    ),
    "gemma-2b": ModelConfig(
        model_id="google/gemma-2b-it",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto"
    ),
    "gemma-7b": ModelConfig(
        model_id="google/gemma-7b-it",
        backend=ModelBackend.TRANSFORMERS,
        dtype=torch.bfloat16,
        device_map="auto"
    ),
}


def create_model_loader(cache_dir: Optional[str] = None) -> ModelLoader:
    """Factory function to create a ModelLoader."""
    return ModelLoader(cache_dir)


def load_preset_model(
    preset_name: str,
    cache_dir: Optional[str] = None,
    **overrides
) -> LoadedModel:
    """Load a preset model with optional config overrides."""
    if preset_name not in PRESET_MODELS:
        available = ", ".join(PRESET_MODELS.keys())
        raise ValueError(f"Unknown preset: {preset_name}. Available: {available}")
    
    config = PRESET_MODELS[preset_name]
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    loader = create_model_loader(cache_dir)
    return loader.load_model(config)


if __name__ == "__main__":
    # Test model loader
    loader = create_model_loader()
    
    # List presets
    print("Available presets:")
    for name in PRESET_MODELS.keys():
        print(f"  - {name}")
    
    # Test registry
    registry = ModelRegistry()
    registry.register_model(
        "test-model",
        "Test Model",
        description="A test model",
        capabilities=["test", "demo"]
    )
    
    print(f"\nRegistered models: {registry.list_models()}")
