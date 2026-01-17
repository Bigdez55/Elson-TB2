#!/usr/bin/env python3
"""Elson 14B DoRA Fine-Tuning - Optimized for H100 80GB"""

import os
import json
import logging
from typing import Dict, List

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Optimized DoRA config for H100 80GB
DORA_CONFIG = {
    "r": 64,                      # 4x higher rank than L4
    "lora_alpha": 128,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],  # Full attention + MLP
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": TaskType.CAUSAL_LM,
    "use_dora": True,             # Real DoRA with magnitude learning!
}

def load_model(model_path: str):
    """Load model with 4-bit quantization"""
    logger.info(f"Loading model: {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization - still useful even on H100 for 14B model
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    logger.info(f"Model loaded: {model.config.model_type}")
    return model, tokenizer

def apply_dora(model):
    """Apply DoRA adapter"""
    logger.info(f"Applying DoRA...")
    logger.info(f"  Rank: {DORA_CONFIG['r']}, Alpha: {DORA_CONFIG['lora_alpha']}")
    logger.info(f"  Target: {DORA_CONFIG['target_modules']}")
    logger.info(f"  DoRA enabled: {DORA_CONFIG['use_dora']}")

    # Prepare model for k-bit training (required for quantized models)
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    model = get_peft_model(model, LoraConfig(**DORA_CONFIG))
    model.print_trainable_parameters()
    return model

def load_training_data(path: str) -> List[Dict]:
    """Load training data"""
    logger.info(f"Loading: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} samples")
    return data

def format_for_training(examples: List[Dict], tokenizer, max_length: int = 2048) -> Dataset:
    """Format Q&A pairs for training"""
    formatted = []
    for ex in examples:
        # Handle instruction/output format (Alpaca-style)
        if 'instruction' in ex and 'output' in ex:
            instruction = ex['instruction']
            if ex.get('input'):
                instruction = f"{instruction}\n{ex['input']}"
            text = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n{ex['output']}<|im_end|>"
        elif 'question' in ex and 'answer' in ex:
            text = f"<|im_start|>user\n{ex['question']}<|im_end|>\n<|im_start|>assistant\n{ex['answer']}<|im_end|>"
        elif 'prompt' in ex and 'response' in ex:
            text = f"<|im_start|>user\n{ex['prompt']}<|im_end|>\n<|im_start|>assistant\n{ex['response']}<|im_end|>"
        else:
            continue
        formatted.append({"text": text})

    logger.info(f"Formatted {len(formatted)} training examples")
    dataset = Dataset.from_list(formatted)

    def tokenize(batch):
        tokens = tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    return dataset.map(tokenize, remove_columns=["text"])

def train(model, tokenizer, dataset, output_dir: str):
    """Run training with H100-optimized settings"""

    # H100 optimized training args
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=8,      # 8x larger than L4
        gradient_accumulation_steps=4,       # Effective batch size: 32
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_steps=25,                       # Checkpoint every 25 steps for Spot safety
        save_total_limit=3,
        bf16=True,
        gradient_checkpointing=False,  # Already enabled in prepare_model_for_kbit_training
        optim="adamw_torch",
        report_to="none",
        dataloader_num_workers=4,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8),
    )

    logger.info(f"Training {len(dataset)} samples, {training_args.num_train_epochs} epochs")
    logger.info(f"Batch size: {training_args.per_device_train_batch_size} x {training_args.gradient_accumulation_steps} = {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
    logger.info(f"Checkpoints every {training_args.save_steps} steps")

    trainer.train()

    # Save final model
    logger.info(f"Saving to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    return trainer

def main():
    logger.info("=" * 60)
    logger.info("Elson 14B DoRA Fine-Tuning (H100 80GB)")
    logger.info("=" * 60)

    # Check GPU
    if torch.cuda.is_available():
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({gpu_mem:.1f} GB)")

    # Paths
    model_path = os.path.expanduser("~/base_model/final")
    data_path = os.path.expanduser("~/Elson-TB2/backend/training_data/training_data_complete.json")
    output_dir = os.path.expanduser("~/wealth-dora-elson14b")

    # Load model
    model, tokenizer = load_model(model_path)

    # Apply DoRA
    model = apply_dora(model)

    # Load and format data
    data = load_training_data(data_path)
    dataset = format_for_training(data, tokenizer)

    # Train
    train(model, tokenizer, dataset, output_dir)

    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info(f"Model saved to: {output_dir}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
