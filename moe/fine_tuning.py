"""
Mrki Fine-Tuning Pipeline - Custom Expert Training

Implements fine-tuning for custom expert models:
- LoRA (Low-Rank Adaptation)
- QLoRA (Quantized LoRA)
- Full fine-tuning
- Instruction tuning
- DPO (Direct Preference Optimization)
- Multi-GPU training
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from tqdm import tqdm
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports
try:
    from peft import (
        LoraConfig, get_peft_model, prepare_model_for_kbit_training,
        TaskType, PeftModel
    )
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    logger.warning("peft not available")

try:
    from transformers import (
        TrainingArguments, Trainer, DataCollatorForLanguageModeling,
        AutoModelForCausalLM, AutoTokenizer
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available")

try:
    from trl import DPOTrainer, SFTTrainer
    TRL_AVAILABLE = True
except ImportError:
    TRL_AVAILABLE = False
    logger.warning("trl not available")


class FineTuningMethod(Enum):
    """Supported fine-tuning methods."""
    LORA = "lora"
    QLORA = "qlora"
    FULL = "full"
    PREFIX_TUNING = "prefix_tuning"
    PROMPT_TUNING = "prompt_tuning"
    P_TUNING = "p_tuning"


class DatasetFormat(Enum):
    """Supported dataset formats."""
    INSTRUCTION = "instruction"  # {instruction, input, output}
    CONVERSATION = "conversation"  # {messages: [{role, content}]}
    PREFERENCE = "preference"  # {prompt, chosen, rejected}
    RAW = "raw"  # {text}


@dataclass
class LoRAConfig:
    """Configuration for LoRA fine-tuning."""
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "v_proj", "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    use_rslora: bool = False  # Rank-stabilized LoRA


@dataclass
class TrainingConfig:
    """Configuration for training."""
    # Method
    method: FineTuningMethod = FineTuningMethod.LORA
    lora_config: Optional[LoRAConfig] = None
    
    # Training hyperparameters
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    
    # Sequence length
    max_seq_length: int = 2048
    
    # Optimization
    optimizer: str = "adamw_torch"
    lr_scheduler: str = "cosine"
    fp16: bool = False
    bf16: bool = True
    
    # Checkpointing
    output_dir: str = "./checkpoints"
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 10
    save_total_limit: int = 3
    
    # Evaluation
    evaluation_strategy: str = "steps"
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    
    # Multi-GPU
    ddp_find_unused_parameters: bool = False
    deepspeed: Optional[str] = None
    
    # Custom
    seed: int = 42
    report_to: List[str] = field(default_factory=lambda: ["tensorboard"])


@dataclass
class ExpertTrainingData:
    """Training data for expert fine-tuning."""
    train_dataset: Dataset
    eval_dataset: Optional[Dataset] = None
    data_collator: Optional[Any] = None


class InstructionDataset(Dataset):
    """Dataset for instruction fine-tuning."""
    
    def __init__(
        self,
        data: List[Dict[str, str]],
        tokenizer: Any,
        max_length: int = 2048,
        template: Optional[str] = None
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.template = template or self._default_template()
    
    def _default_template(self) -> str:
        return """### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        
        text = self.template.format(
            instruction=item.get("instruction", ""),
            input=item.get("input", ""),
            output=item.get("output", "")
        )
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze()
        }


class ConversationDataset(Dataset):
    """Dataset for conversation fine-tuning."""
    
    def __init__(
        self,
        data: List[Dict[str, List]],
        tokenizer: Any,
        max_length: int = 2048
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        messages = item.get("messages", [])
        
        # Format as chat
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze()
        }


class PreferenceDataset(Dataset):
    """Dataset for DPO training."""
    
    def __init__(
        self,
        data: List[Dict[str, str]],
        tokenizer: Any,
        max_length: int = 2048
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        
        prompt = item.get("prompt", "")
        chosen = item.get("chosen", "")
        rejected = item.get("rejected", "")
        
        # Tokenize
        prompt_encoding = self.tokenizer(
            prompt,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )
        
        chosen_encoding = self.tokenizer(
            prompt + chosen,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )
        
        rejected_encoding = self.tokenizer(
            prompt + rejected,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "prompt_input_ids": prompt_encoding["input_ids"].squeeze(),
            "prompt_attention_mask": prompt_encoding["attention_mask"].squeeze(),
            "chosen_input_ids": chosen_encoding["input_ids"].squeeze(),
            "chosen_attention_mask": chosen_encoding["attention_mask"].squeeze(),
            "rejected_input_ids": rejected_encoding["input_ids"].squeeze(),
            "rejected_attention_mask": rejected_encoding["attention_mask"].squeeze(),
        }


class ExpertFineTuner:
    """
    Main fine-tuning pipeline for custom expert models.
    
    Supports:
    - LoRA/QLoRA efficient fine-tuning
    - Full fine-tuning
    - Instruction tuning
    - DPO for preference alignment
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model: Optional[nn.Module] = None
        self.tokenizer: Optional[Any] = None
        self.peft_model: Optional[PeftModel] = None
        
    def load_base_model(
        self,
        model_id: str,
        quantization_config: Optional[Any] = None
    ):
        """Load the base model for fine-tuning."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers not available")
        
        logger.info(f"Loading base model: {model_id}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.bfloat16 if self.config.bf16 else torch.float16,
            trust_remote_code=True
        )
        
        logger.info("Base model loaded")
    
    def prepare_model(self):
        """Prepare model for fine-tuning."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if self.config.method == FineTuningMethod.QLORA:
            if not PEFT_AVAILABLE:
                raise RuntimeError("peft not available")
            
            # Prepare for k-bit training
            self.model = prepare_model_for_kbit_training(self.model)
            
            # Apply LoRA
            lora_config = self._get_lora_config()
            self.peft_model = get_peft_model(self.model, lora_config)
            
            logger.info("Model prepared for QLoRA training")
            self.peft_model.print_trainable_parameters()
            
        elif self.config.method == FineTuningMethod.LORA:
            if not PEFT_AVAILABLE:
                raise RuntimeError("peft not available")
            
            # Apply LoRA
            lora_config = self._get_lora_config()
            self.peft_model = get_peft_model(self.model, lora_config)
            
            logger.info("Model prepared for LoRA training")
            self.peft_model.print_trainable_parameters()
            
        elif self.config.method == FineTuningMethod.FULL:
            self.peft_model = self.model
            logger.info("Model prepared for full fine-tuning")
            
        else:
            raise ValueError(f"Unsupported method: {self.config.method}")
    
    def _get_lora_config(self) -> LoraConfig:
        """Get LoRA configuration."""
        lora_config = self.config.lora_config or LoRAConfig()
        
        return LoraConfig(
            r=lora_config.r,
            lora_alpha=lora_config.lora_alpha,
            lora_dropout=lora_config.lora_dropout,
            target_modules=lora_config.target_modules,
            bias=lora_config.bias,
            task_type=TaskType.CAUSAL_LM,
            use_rslora=lora_config.use_rslora
        )
    
    def train(
        self,
        train_data: ExpertTrainingData,
        resume_from_checkpoint: Optional[str] = None
    ) -> str:
        """
        Train the expert model.
        
        Args:
            train_data: Training data
            resume_from_checkpoint: Checkpoint to resume from
            
        Returns:
            Path to saved model
        """
        if self.peft_model is None:
            raise RuntimeError("Model not prepared")
        
        # Create output directory
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_steps=self.config.warmup_steps,
            max_grad_norm=self.config.max_grad_norm,
            optim=self.config.optimizer,
            lr_scheduler_type=self.config.lr_scheduler,
            fp16=self.config.fp16,
            bf16=self.config.bf16,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            evaluation_strategy=self.config.evaluation_strategy,
            load_best_model_at_end=self.config.load_best_model_at_end,
            metric_for_best_model=self.config.metric_for_best_model,
            save_total_limit=self.config.save_total_limit,
            seed=self.config.seed,
            report_to=self.config.report_to,
            ddp_find_unused_parameters=self.config.ddp_find_unused_parameters,
            deepspeed=self.config.deepspeed,
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_data.train_dataset,
            eval_dataset=train_data.eval_dataset,
            data_collator=train_data.data_collator,
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)
        
        # Save final model
        final_path = output_dir / "final"
        trainer.save_model(str(final_path))
        self.tokenizer.save_pretrained(str(final_path))
        
        logger.info(f"Training complete. Model saved to {final_path}")
        return str(final_path)
    
    def train_instruction(
        self,
        instructions: List[Dict[str, str]],
        eval_split: float = 0.1
    ) -> str:
        """
        Train on instruction-formatted data.
        
        Args:
            instructions: List of instruction dicts
            eval_split: Fraction for evaluation
            
        Returns:
            Path to saved model
        """
        # Split data
        split_idx = int(len(instructions) * (1 - eval_split))
        train_data = instructions[:split_idx]
        eval_data = instructions[split_idx:] if eval_split > 0 else None
        
        # Create datasets
        train_dataset = InstructionDataset(
            train_data, self.tokenizer, self.config.max_seq_length
        )
        eval_dataset = None
        if eval_data:
            eval_dataset = InstructionDataset(
                eval_data, self.tokenizer, self.config.max_seq_length
            )
        
        # Create data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        expert_data = ExpertTrainingData(
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )
        
        return self.train(expert_data)
    
    def train_conversation(
        self,
        conversations: List[Dict[str, List]],
        eval_split: float = 0.1
    ) -> str:
        """
        Train on conversation-formatted data.
        
        Args:
            conversations: List of conversation dicts
            eval_split: Fraction for evaluation
            
        Returns:
            Path to saved model
        """
        if not TRL_AVAILABLE:
            raise RuntimeError("trl not available for SFT training")
        
        # Split data
        split_idx = int(len(conversations) * (1 - eval_split))
        train_data = conversations[:split_idx]
        eval_data = conversations[split_idx:] if eval_split > 0 else None
        
        # Use SFTTrainer
        trainer = SFTTrainer(
            model=self.peft_model,
            tokenizer=self.tokenizer,
            train_dataset=train_data,
            eval_dataset=eval_data,
            max_seq_length=self.config.max_seq_length,
            args=TrainingArguments(
                output_dir=self.config.output_dir,
                num_train_epochs=self.config.num_epochs,
                per_device_train_batch_size=self.config.batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                learning_rate=self.config.learning_rate,
                fp16=self.config.fp16,
                bf16=self.config.bf16,
                logging_steps=self.config.logging_steps,
                save_steps=self.config.save_steps,
            )
        )
        
        trainer.train()
        
        final_path = Path(self.config.output_dir) / "final"
        trainer.save_model(str(final_path))
        
        return str(final_path)
    
    def train_dpo(
        self,
        preferences: List[Dict[str, str]],
        ref_model: Optional[nn.Module] = None,
        beta: float = 0.1
    ) -> str:
        """
        Train with Direct Preference Optimization.
        
        Args:
            preferences: List of preference dicts (prompt, chosen, rejected)
            ref_model: Reference model (uses base if None)
            beta: DPO temperature parameter
            
        Returns:
            Path to saved model
        """
        if not TRL_AVAILABLE:
            raise RuntimeError("trl not available for DPO training")
        
        # Create dataset
        train_dataset = PreferenceDataset(
            preferences, self.tokenizer, self.config.max_seq_length
        )
        
        # DPO trainer
        trainer = DPOTrainer(
            model=self.peft_model,
            ref_model=ref_model or self.model,
            beta=beta,
            train_dataset=train_dataset,
            tokenizer=self.tokenizer,
            args=TrainingArguments(
                output_dir=self.config.output_dir,
                num_train_epochs=self.config.num_epochs,
                per_device_train_batch_size=self.config.batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                learning_rate=self.config.learning_rate,
                fp16=self.config.fp16,
                bf16=self.config.bf16,
                logging_steps=self.config.logging_steps,
                save_steps=self.config.save_steps,
            )
        )
        
        trainer.train()
        
        final_path = Path(self.config.output_dir) / "final"
        trainer.save_model(str(final_path))
        
        return str(final_path)
    
    def merge_and_save(self, output_path: str):
        """Merge LoRA weights with base model and save."""
        if self.peft_model is None:
            raise RuntimeError("No PEFT model to merge")
        
        logger.info("Merging LoRA weights with base model...")
        
        # Merge
        merged_model = self.peft_model.merge_and_unload()
        
        # Save
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        logger.info(f"Merged model saved to {output_path}")


class ExpertDatasetBuilder:
    """
    Builder for creating expert training datasets.
    """
    
    @staticmethod
    def from_jsonl(
        path: str,
        format: DatasetFormat = DatasetFormat.INSTRUCTION
    ) -> List[Dict]:
        """Load dataset from JSONL file."""
        data = []
        with open(path, 'r') as f:
            for line in f:
                data.append(json.loads(line))
        return data
    
    @staticmethod
    def from_huggingface(
        dataset_name: str,
        split: str = "train",
        format: DatasetFormat = DatasetFormat.INSTRUCTION,
        text_column: str = "text"
    ) -> List[Dict]:
        """Load dataset from HuggingFace."""
        try:
            from datasets import load_dataset
            
            dataset = load_dataset(dataset_name, split=split)
            
            if format == DatasetFormat.RAW:
                return [{"text": item[text_column]} for item in dataset]
            
            return list(dataset)
        except ImportError:
            logger.error("datasets library not available")
            return []
    
    @staticmethod
    def create_instruction_data(
        instructions: List[str],
        inputs: List[str],
        outputs: List[str]
    ) -> List[Dict[str, str]]:
        """Create instruction-formatted data."""
        return [
            {"instruction": inst, "input": inp, "output": out}
            for inst, inp, out in zip(instructions, inputs, outputs)
        ]
    
    @staticmethod
    def create_conversation_data(
        conversations: List[List[Dict[str, str]]]
    ) -> List[Dict[str, List]]:
        """Create conversation-formatted data."""
        return [{"messages": conv} for conv in conversations]
    
    @staticmethod
    def create_preference_data(
        prompts: List[str],
        chosen: List[str],
        rejected: List[str]
    ) -> List[Dict[str, str]]:
        """Create preference-formatted data."""
        return [
            {"prompt": p, "chosen": c, "rejected": r}
            for p, c, r in zip(prompts, chosen, rejected)
        ]


# Predefined training configurations
TRAINING_PRESETS = {
    "lora-default": TrainingConfig(
        method=FineTuningMethod.LORA,
        lora_config=LoRAConfig(r=16, lora_alpha=32),
        num_epochs=3,
        batch_size=4,
        learning_rate=2e-4
    ),
    "qlora-4bit": TrainingConfig(
        method=FineTuningMethod.QLORA,
        lora_config=LoRAConfig(r=64, lora_alpha=16),
        num_epochs=3,
        batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=1e-4,
        bf16=True
    ),
    "full-finetune": TrainingConfig(
        method=FineTuningMethod.FULL,
        num_epochs=3,
        batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=2e-5,
        bf16=True
    ),
    "dpo-default": TrainingConfig(
        method=FineTuningMethod.LORA,
        lora_config=LoRAConfig(r=8, lora_alpha=16),
        num_epochs=1,
        batch_size=2,
        learning_rate=5e-5
    ),
}


def create_fine_tuner(
    preset: Optional[str] = None,
    **kwargs
) -> ExpertFineTuner:
    """Factory function to create a fine-tuner."""
    if preset:
        if preset not in TRAINING_PRESETS:
            raise ValueError(f"Unknown preset: {preset}")
        config = TRAINING_PRESETS[preset]
    else:
        config = TrainingConfig(**kwargs)
    
    return ExpertFineTuner(config)


if __name__ == "__main__":
    # Test fine-tuner
    print("Available training presets:")
    for name in TRAINING_PRESETS.keys():
        print(f"  - {name}")
    
    # Example instruction data
    example_instructions = [
        {
            "instruction": "Explain quantum computing",
            "input": "",
            "output": "Quantum computing uses quantum bits (qubits) to perform calculations..."
        },
        {
            "instruction": "Write a Python function",
            "input": "Function to calculate factorial",
            "output": "def factorial(n):\\n    if n <= 1: return 1\\n    return n * factorial(n-1)"
        }
    ]
    
    print(f"\nExample instruction format:")
    print(json.dumps(example_instructions[0], indent=2))
