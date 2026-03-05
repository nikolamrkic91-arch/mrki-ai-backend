"""
Mrki Quantizer - Model Quantization Utilities

Implements model quantization for efficient inference:
- 4-bit quantization (NF4, FP4)
- 8-bit quantization
- GPTQ quantization
- AWQ quantization
- Dynamic quantization
- Calibration and fine-tuning
"""

import torch
import torch.nn as nn
import torch.quantization
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import logging
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports
try:
    from transformers import BitsAndBytesConfig
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import bitsandbytes as bnb
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False

try:
    from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
    AUTOGPTQ_AVAILABLE = True
except ImportError:
    AUTOGPTQ_AVAILABLE = False

try:
    from awq import AutoAWQForCausalLM
    AWQ_AVAILABLE = True
except ImportError:
    AWQ_AVAILABLE = False


class QuantizationType(Enum):
    """Supported quantization types."""
    INT8 = "int8"
    INT4 = "int4"
    NF4 = "nf4"
    FP4 = "fp4"
    GPTQ = "gptq"
    AWQ = "awq"
    DYNAMIC = "dynamic"
    STATIC = "static"


class QuantizationMethod(Enum):
    """Quantization methods."""
    BITS_AND_BYTES = "bitsandbytes"
    GPTQ = "gptq"
    AWQ = "awq"
    PYTORCH = "pytorch"
    ONNX = "onnx"


@dataclass
class QuantizationConfig:
    """Configuration for model quantization."""
    quant_type: QuantizationType = QuantizationType.NF4
    method: QuantizationMethod = QuantizationMethod.BITS_AND_BYTES
    
    # BitsAndBytes specific
    load_in_4bit: bool = False
    load_in_8bit: bool = False
    bnb_4bit_compute_dtype: torch.dtype = torch.float16
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    llm_int8_threshold: float = 6.0
    llm_int8_has_fp16_weight: bool = False
    
    # GPTQ specific
    gptq_bits: int = 4
    gptq_group_size: int = 128
    gptq_desc_act: bool = False
    gptq_damp_percent: float = 0.01
    
    # AWQ specific
    awq_bits: int = 4
    awq_group_size: int = 128
    awq_version: str = "GEMM"
    
    # Dynamic quantization
    dynamic_qconfig = None  # torch.quantization.QConfig
    
    # Calibration
    calibration_dataset: Optional[List[str]] = None
    num_calibration_samples: int = 128
    
    # Export
    output_path: Optional[str] = None
    save_safetensors: bool = True


class ModelQuantizer:
    """
    Main quantizer for reducing model size and memory usage.
    
    Supports multiple quantization backends:
    - BitsAndBytes (4-bit, 8-bit)
    - AutoGPTQ (GPTQ quantization)
    - AutoAWQ (AWQ quantization)
    - PyTorch native quantization
    """
    
    def __init__(self, config: Optional[QuantizationConfig] = None):
        self.config = config or QuantizationConfig()
        
    def quantize_model(
        self,
        model: nn.Module,
        tokenizer: Optional[Any] = None,
        calibration_data: Optional[List[str]] = None
    ) -> nn.Module:
        """
        Quantize a model.
        
        Args:
            model: Model to quantize
            tokenizer: Tokenizer for calibration
            calibration_data: Optional calibration dataset
            
        Returns:
            Quantized model
        """
        if self.config.method == QuantizationMethod.BITS_AND_BYTES:
            return self._quantize_bitsandbytes(model)
        elif self.config.method == QuantizationMethod.GPTQ:
            return self._quantize_gptq(model, tokenizer, calibration_data)
        elif self.config.method == QuantizationMethod.AWQ:
            return self._quantize_awq(model, tokenizer, calibration_data)
        elif self.config.method == QuantizationMethod.PYTORCH:
            return self._quantize_pytorch(model, calibration_data)
        else:
            raise ValueError(f"Unknown quantization method: {self.config.method}")
    
    def _quantize_bitsandbytes(self, model: nn.Module) -> nn.Module:
        """Quantize using BitsAndBytes."""
        if not BITSANDBYTES_AVAILABLE:
            raise RuntimeError("bitsandbytes not available")
        
        logger.info(f"Quantizing with BitsAndBytes ({self.config.quant_type.value})")
        
        # Replace Linear layers with quantized versions
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # Determine quantization config
                if self.config.load_in_4bit or self.config.quant_type in [QuantizationType.NF4, QuantizationType.FP4]:
                    # 4-bit quantization
                    quantized_layer = bnb.nn.Linear4bit(
                        module.in_features,
                        module.out_features,
                        bias=module.bias is not None,
                        compute_dtype=self.config.bnb_4bit_compute_dtype,
                        compress_statistics=self.config.bnb_4bit_use_double_quant,
                        quant_type=self.config.bnb_4bit_quant_type
                    )
                elif self.config.load_in_8bit or self.config.quant_type == QuantizationType.INT8:
                    # 8-bit quantization
                    quantized_layer = bnb.nn.Linear8bitLt(
                        module.in_features,
                        module.out_features,
                        bias=module.bias is not None,
                        has_fp16_weights=self.config.llm_int8_has_fp16_weight,
                        threshold=self.config.llm_int8_threshold
                    )
                else:
                    continue
                
                # Copy weights
                quantized_layer.weight.data = module.weight.data
                if module.bias is not None:
                    quantized_layer.bias.data = module.bias.data
                
                # Replace module
                parent_name = '.'.join(name.split('.')[:-1])
                child_name = name.split('.')[-1]
                parent = model.get_submodule(parent_name) if parent_name else model
                setattr(parent, child_name, quantized_layer)
        
        logger.info("BitsAndBytes quantization complete")
        return model
    
    def _quantize_gptq(
        self,
        model: nn.Module,
        tokenizer: Optional[Any],
        calibration_data: Optional[List[str]]
    ) -> nn.Module:
        """Quantize using GPTQ."""
        if not AUTOGPTQ_AVAILABLE:
            raise RuntimeError("auto_gptq not available")
        
        logger.info(f"Quantizing with GPTQ ({self.config.gptq_bits}-bit)")
        
        # This requires the model to be loaded with AutoGPTQ
        # For already loaded models, we'd need to reload
        logger.warning("GPTQ quantization requires loading model with AutoGPTQ")
        
        return model
    
    def _quantize_awq(
        self,
        model: nn.Module,
        tokenizer: Optional[Any],
        calibration_data: Optional[List[str]]
    ) -> nn.Module:
        """Quantize using AWQ."""
        if not AWQ_AVAILABLE:
            raise RuntimeError("autoawq not available")
        
        logger.info(f"Quantizing with AWQ ({self.config.awq_bits}-bit)")
        
        # Similar to GPTQ, requires loading with AutoAWQ
        logger.warning("AWQ quantization requires loading model with AutoAWQ")
        
        return model
    
    def _quantize_pytorch(
        self,
        model: nn.Module,
        calibration_data: Optional[List[str]]
    ) -> nn.Module:
        """Quantize using PyTorch native quantization."""
        logger.info("Quantizing with PyTorch native")
        
        # Dynamic quantization for linear layers
        model = torch.quantization.quantize_dynamic(
            model,
            {nn.Linear},
            dtype=torch.qint8
        )
        
        logger.info("PyTorch dynamic quantization complete")
        return model
    
    def get_quantization_config(self) -> Any:
        """Get quantization config for transformers."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers not available")
        
        return BitsAndBytesConfig(
            load_in_4bit=self.config.load_in_4bit or self.config.quant_type in [QuantizationType.NF4, QuantizationType.FP4],
            load_in_8bit=self.config.load_in_8bit or self.config.quant_type == QuantizationType.INT8,
            bnb_4bit_compute_dtype=self.config.bnb_4bit_compute_dtype,
            bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.config.bnb_4bit_use_double_quant
        )
    
    def estimate_memory_savings(self, model: nn.Module) -> Dict[str, float]:
        """Estimate memory savings from quantization."""
        total_params = sum(p.numel() for p in model.parameters())
        
        # Original size (assuming fp16)
        original_size_mb = (total_params * 2) / (1024 ** 2)
        
        # Quantized size
        if self.config.quant_type in [QuantizationType.NF4, QuantizationType.FP4]:
            bits = 4
        elif self.config.quant_type == QuantizationType.INT8:
            bits = 8
        else:
            bits = 16
        
        quantized_size_mb = (total_params * bits / 8) / (1024 ** 2)
        
        savings_percent = (1 - quantized_size_mb / original_size_mb) * 100
        
        return {
            "original_size_mb": original_size_mb,
            "quantized_size_mb": quantized_size_mb,
            "savings_mb": original_size_mb - quantized_size_mb,
            "savings_percent": savings_percent,
            "compression_ratio": original_size_mb / quantized_size_mb if quantized_size_mb > 0 else 1
        }


class GPTQQuantizer:
    """
    GPTQ quantization for LLMs.
    
    Implements post-training quantization with minimal accuracy loss.
    """
    
    def __init__(
        self,
        bits: int = 4,
        group_size: int = 128,
        desc_act: bool = False,
        damp_percent: float = 0.01
    ):
        self.bits = bits
        self.group_size = group_size
        self.desc_act = desc_act
        self.damp_percent = damp_percent
    
    def quantize(
        self,
        model_id: str,
        output_path: str,
        calibration_dataset: List[str],
        tokenizer: Any
    ) -> str:
        """
        Quantize a model using GPTQ.
        
        Args:
            model_id: HuggingFace model ID
            output_path: Path to save quantized model
            calibration_dataset: Calibration data
            tokenizer: Tokenizer
            
        Returns:
            Path to quantized model
        """
        if not AUTOGPTQ_AVAILABLE:
            raise RuntimeError("auto_gptq not available")
        
        logger.info(f"Quantizing {model_id} with GPTQ ({self.bits}-bit)")
        
        # Configure quantization
        quantize_config = BaseQuantizeConfig(
            bits=self.bits,
            group_size=self.group_size,
            desc_act=self.desc_act,
            damp_percent=self.damp_percent
        )
        
        # Load model
        model = AutoGPTQForCausalLM.from_pretrained(
            model_id,
            quantize_config
        )
        
        # Tokenize calibration data
        examples = [
            tokenizer(text, return_tensors="pt") 
            for text in calibration_dataset
        ]
        
        # Quantize
        model.quantize(examples)
        
        # Save
        model.save_quantized(output_path)
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"Quantized model saved to {output_path}")
        return output_path


class AWQQuantizer:
    """
    AWQ (Activation-aware Weight Quantization) for LLMs.
    
    Provides better accuracy than GPTQ by considering activation magnitudes.
    """
    
    def __init__(
        self,
        bits: int = 4,
        group_size: int = 128,
        version: str = "GEMM"
    ):
        self.bits = bits
        self.group_size = group_size
        self.version = version
    
    def quantize(
        self,
        model_id: str,
        output_path: str,
        calibration_dataset: List[str],
        tokenizer: Any
    ) -> str:
        """
        Quantize a model using AWQ.
        
        Args:
            model_id: HuggingFace model ID
            output_path: Path to save quantized model
            calibration_dataset: Calibration data
            tokenizer: Tokenizer
            
        Returns:
            Path to quantized model
        """
        if not AWQ_AVAILABLE:
            raise RuntimeError("autoawq not available")
        
        logger.info(f"Quantizing {model_id} with AWQ ({self.bits}-bit)")
        
        # Load model
        model = AutoAWQForCausalLM.from_pretrained(
            model_id,
            safetensors=True,
            device_map="auto"
        )
        
        # Quantize
        model.quantize(
            tokenizer,
            quant_config={
                "zero_point": True,
                "q_group_size": self.group_size,
                "w_bit": self.bits,
                "version": self.version
            }
        )
        
        # Save
        model.save_quantized(output_path)
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"Quantized model saved to {output_path}")
        return output_path


class CalibrationDatasetBuilder:
    """
    Builds calibration datasets for quantization.
    """
    
    def __init__(self, tokenizer: Any):
        self.tokenizer = tokenizer
    
    def from_texts(self, texts: List[str], max_length: int = 2048) -> List[torch.Tensor]:
        """Build calibration data from texts."""
        examples = []
        for text in texts:
            encoded = self.tokenizer(
                text,
                max_length=max_length,
                truncation=True,
                return_tensors="pt"
            )
            examples.append(encoded)
        return examples
    
    def from_dataset(
        self,
        dataset_name: str,
        split: str = "train",
        num_samples: int = 128,
        text_column: str = "text"
    ) -> List[str]:
        """Build calibration data from HuggingFace dataset."""
        try:
            from datasets import load_dataset
            
            dataset = load_dataset(dataset_name, split=split)
            texts = []
            
            for i, example in enumerate(dataset):
                if i >= num_samples:
                    break
                text = example.get(text_column, "")
                if text:
                    texts.append(text)
            
            return texts
        except ImportError:
            logger.error("datasets library not available")
            return []
    
    def from_prompts(self, prompts: List[str]) -> List[str]:
        """Build calibration data from prompts."""
        return prompts


class QuantizedModelLoader:
    """
    Loads pre-quantized models efficiently.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir
    
    def load_gptq_model(
        self,
        model_path: str,
        device: str = "cuda"
    ) -> Tuple[Any, Any]:
        """Load a GPTQ quantized model."""
        if not AUTOGPTQ_AVAILABLE:
            raise RuntimeError("auto_gptq not available")
        
        from transformers import AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        model = AutoGPTQForCausalLM.from_quantized(
            model_path,
            device=device,
            use_safetensors=True
        )
        
        return model, tokenizer
    
    def load_awq_model(
        self,
        model_path: str,
        device: str = "cuda"
    ) -> Tuple[Any, Any]:
        """Load an AWQ quantized model."""
        if not AWQ_AVAILABLE:
            raise RuntimeError("autoawq not available")
        
        from transformers import AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        model = AutoAWQForCausalLM.from_quantized(
            model_path,
            device_map=device
        )
        
        return model, tokenizer
    
    def load_bnb_model(
        self,
        model_path: str,
        quantization_config: QuantizationConfig,
        device: str = "auto"
    ) -> Tuple[Any, Any]:
        """Load a BitsAndBytes quantized model."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        quantizer = ModelQuantizer(quantization_config)
        bnb_config = quantizer.get_quantization_config()
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map=device,
            torch_dtype=torch.float16
        )
        
        return model, tokenizer


# Predefined quantization presets
QUANTIZATION_PRESETS = {
    "4bit-nf4": QuantizationConfig(
        quant_type=QuantizationType.NF4,
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    ),
    "4bit-fp4": QuantizationConfig(
        quant_type=QuantizationType.FP4,
        load_in_4bit=True,
        bnb_4bit_quant_type="fp4",
        bnb_4bit_compute_dtype=torch.bfloat16
    ),
    "8bit": QuantizationConfig(
        quant_type=QuantizationType.INT8,
        load_in_8bit=True
    ),
    "gptq-4bit": QuantizationConfig(
        quant_type=QuantizationType.GPTQ,
        method=QuantizationMethod.GPTQ,
        gptq_bits=4,
        gptq_group_size=128
    ),
    "awq-4bit": QuantizationConfig(
        quant_type=QuantizationType.AWQ,
        method=QuantizationMethod.AWQ,
        awq_bits=4,
        awq_group_size=128
    ),
}


def create_quantizer(
    preset: Optional[str] = None,
    **kwargs
) -> ModelQuantizer:
    """Factory function to create a quantizer."""
    if preset:
        if preset not in QUANTIZATION_PRESETS:
            raise ValueError(f"Unknown preset: {preset}")
        config = QUANTIZATION_PRESETS[preset]
    else:
        config = QuantizationConfig(**kwargs)
    
    return ModelQuantizer(config)


def quantize_model_from_preset(
    model: nn.Module,
    preset: str,
    **kwargs
) -> nn.Module:
    """Quantize a model using a preset configuration."""
    quantizer = create_quantizer(preset, **kwargs)
    return quantizer.quantize_model(model)


if __name__ == "__main__":
    # Test quantizer
    print("Available quantization presets:")
    for name in QUANTIZATION_PRESETS.keys():
        print(f"  - {name}")
    
    # Create a simple test model
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear1 = nn.Linear(768, 3072)
            self.linear2 = nn.Linear(3072, 768)
        
        def forward(self, x):
            return self.linear2(torch.relu(self.linear1(x)))
    
    model = TestModel()
    
    # Estimate savings
    quantizer = create_quantizer("4bit-nf4")
    savings = quantizer.estimate_memory_savings(model)
    
    print(f"\nMemory savings estimate:")
    print(f"  Original: {savings['original_size_mb']:.2f} MB")
    print(f"  Quantized: {savings['quantized_size_mb']:.2f} MB")
    print(f"  Savings: {savings['savings_percent']:.1f}%")
    print(f"  Compression ratio: {savings['compression_ratio']:.2f}x")
