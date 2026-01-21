"""
Elson Financial AI - Advanced Fine-Tuning & Model Soup

This module provides utilities for:
1. LoRA fine-tuning on proprietary Elson trading data
2. Model Soup - averaging multiple fine-tuned variants
3. Continuous learning with new data

These techniques make the model TRULY proprietary by encoding
YOUR trading patterns, YOUR users' preferences, and YOUR strategies.

Copyright (c) 2024 Elson Wealth. All rights reserved.
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

logger = logging.getLogger(__name__)


@dataclass
class FineTuningConfig:
    """Configuration for LoRA fine-tuning."""

    # LoRA parameters
    lora_r: int = 16  # Rank of the low-rank matrices
    lora_alpha: int = 32  # Scaling factor
    lora_dropout: float = 0.05
    target_modules: List[str] = None  # Which layers to adapt

    # Training parameters
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    warmup_ratio: float = 0.1
    max_seq_length: int = 2048

    # Output
    output_dir: str = "./elson-finance-finetuned"

    def __post_init__(self):
        if self.target_modules is None:
            # Default: adapt attention and MLP layers
            self.target_modules = [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ]


class ElsonFineTuner:
    """
    Fine-tune Elson-Finance model on proprietary trading data.

    This creates LoRA adapters that encode YOUR trading knowledge,
    making the model truly proprietary.

    Usage:
        tuner = ElsonFineTuner("./elson-finance-trading-14b")
        tuner.prepare_training_data(trading_examples)
        tuner.fine_tune(config)
        tuner.save_adapter("./elson-finance-proprietary")
    """

    def __init__(self, base_model_path: str):
        """
        Initialize fine-tuner with base model.

        Args:
            base_model_path: Path to merged Elson model
        """
        self.base_model_path = base_model_path
        self.model = None
        self.tokenizer = None
        self.dataset = None

        logger.info(f"ElsonFineTuner initialized with base: {base_model_path}")

    def load_model(self, load_in_4bit: bool = True) -> None:
        """
        Load base model for fine-tuning.

        Args:
            load_in_4bit: Use 4-bit quantization to reduce memory
        """
        logger.info("Loading base model for fine-tuning...")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with quantization for memory efficiency
        if load_in_4bit:
            from transformers import BitsAndBytesConfig

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            self.model = prepare_model_for_kbit_training(self.model)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )

        logger.info("Base model loaded successfully")

    def prepare_training_data(
        self, examples: List[Dict[str, str]], system_prompt: Optional[str] = None
    ) -> None:
        """
        Prepare training data from trading examples.

        Args:
            examples: List of {"input": ..., "output": ...} dicts
            system_prompt: Optional system prompt to prepend

        Example input:
            [
                {
                    "input": "Analyze AAPL: RSI 25, MACD bullish, sentiment +0.3",
                    "output": "ACTION: BUY\\nCONFIDENCE: 75%\\nREASONING: ..."
                },
                ...
            ]
        """
        system = (
            system_prompt
            or """You are Elson-Finance-Trading, analyzing markets
for autonomous trading decisions. Provide structured recommendations."""
        )

        formatted_examples = []
        for ex in examples:
            # Format as chat conversation
            text = f"""<|system|>
{system}
<|user|>
{ex['input']}
<|assistant|>
{ex['output']}<|endoftext|>"""
            formatted_examples.append({"text": text})

        self.dataset = Dataset.from_list(formatted_examples)

        # Tokenize
        def tokenize(example):
            return self.tokenizer(
                example["text"],
                truncation=True,
                max_length=2048,
                padding="max_length",
            )

        self.dataset = self.dataset.map(tokenize, remove_columns=["text"])
        logger.info(f"Prepared {len(self.dataset)} training examples")

    def fine_tune(self, config: Optional[FineTuningConfig] = None) -> str:
        """
        Run LoRA fine-tuning.

        Args:
            config: Fine-tuning configuration

        Returns:
            Path to saved adapter
        """
        config = config or FineTuningConfig()

        if self.model is None:
            self.load_model()

        if self.dataset is None:
            raise ValueError("No training data. Call prepare_training_data first.")

        # Configure LoRA
        lora_config = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            target_modules=config.target_modules,
            lora_dropout=config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
        )

        # Apply LoRA to model
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        # Training arguments
        training_args = TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            learning_rate=config.learning_rate,
            warmup_ratio=config.warmup_ratio,
            logging_steps=10,
            save_strategy="epoch",
            fp16=False,
            bf16=True,
            optim="paged_adamw_8bit",
            report_to="none",
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        # Train
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.dataset,
            data_collator=data_collator,
        )

        logger.info("Starting fine-tuning...")
        trainer.train()

        # Save adapter
        self.model.save_pretrained(config.output_dir)
        self.tokenizer.save_pretrained(config.output_dir)

        logger.info(f"Fine-tuned adapter saved to {config.output_dir}")
        return config.output_dir

    def save_adapter(self, path: str) -> None:
        """Save the LoRA adapter weights."""
        if self.model is None:
            raise ValueError("No model loaded")
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)


class ModelSoup:
    """
    Average weights across multiple fine-tuned variants.

    Model Soup improves robustness by combining models fine-tuned on
    different data splits, hyperparameters, or tasks.

    Usage:
        soup = ModelSoup(base_model_path="./elson-finance-trading-14b")
        soup.add_variant("./variant-sentiment")
        soup.add_variant("./variant-technical")
        soup.add_variant("./variant-news")
        soup.create_soup("./elson-finance-soup")
    """

    def __init__(self, base_model_path: str):
        """
        Initialize Model Soup.

        Args:
            base_model_path: Path to base model for architecture reference
        """
        self.base_model_path = base_model_path
        self.variant_paths: List[str] = []

    def add_variant(self, variant_path: str) -> None:
        """Add a fine-tuned variant to the soup."""
        if not os.path.exists(variant_path):
            raise FileNotFoundError(f"Variant not found: {variant_path}")
        self.variant_paths.append(variant_path)
        logger.info(f"Added variant: {variant_path} (total: {len(self.variant_paths)})")

    def create_soup(
        self, output_path: str, weights: Optional[List[float]] = None
    ) -> str:
        """
        Create model soup by averaging variant weights.

        Args:
            output_path: Where to save the soup model
            weights: Optional weights for each variant (default: equal)

        Returns:
            Path to soup model
        """
        if len(self.variant_paths) < 2:
            raise ValueError("Need at least 2 variants for soup")

        # Default to equal weights
        if weights is None:
            weights = [1.0 / len(self.variant_paths)] * len(self.variant_paths)

        if len(weights) != len(self.variant_paths):
            raise ValueError("Number of weights must match number of variants")

        logger.info(f"Creating soup from {len(self.variant_paths)} variants...")

        # Load all variant state dicts
        state_dicts = []
        for path in self.variant_paths:
            model = AutoModelForCausalLM.from_pretrained(
                path,
                torch_dtype=torch.float32,  # Use float32 for averaging
            )
            state_dicts.append(model.state_dict())
            del model  # Free memory

        # Average weights
        avg_state_dict = {}
        for key in state_dicts[0].keys():
            stacked = torch.stack(
                [sd[key].float() * w for sd, w in zip(state_dicts, weights)]
            )
            avg_state_dict[key] = stacked.sum(dim=0)

        # Load base model and apply averaged weights
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.bfloat16,
        )
        base_model.load_state_dict(avg_state_dict)

        # Save soup model
        base_model.save_pretrained(output_path)

        # Save tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.variant_paths[0])
        tokenizer.save_pretrained(output_path)

        logger.info(f"Model soup saved to {output_path}")
        return output_path


def create_training_examples_from_backtests(
    backtest_results: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Convert backtesting results into training examples.

    Args:
        backtest_results: List of backtest records with:
            - symbol: Stock symbol
            - entry_price: Entry price
            - exit_price: Exit price
            - profit_pct: Profit percentage
            - indicators: Dict of indicator values at entry
            - news: List of relevant headlines

    Returns:
        Training examples for fine-tuning
    """
    examples = []

    for result in backtest_results:
        # Only learn from successful trades (profitable with good reasoning)
        if result.get("profit_pct", 0) < 0:
            continue

        indicators = result.get("indicators", {})
        news = result.get("news", [])

        # Build input
        input_text = f"""Analyze {result['symbol']}:
- Price: ${result['entry_price']:.2f}
- RSI: {indicators.get('rsi', 50):.1f}
- MACD: {'Bullish' if indicators.get('macd_bullish', False) else 'Bearish'}
- Sentiment: {indicators.get('sentiment', 0):.2f}
- Headlines: {'; '.join(news[:3]) if news else 'None'}
"""

        # Build output (what we want the model to learn)
        action = "BUY" if result["profit_pct"] > 0 else "SELL"
        confidence = min(95, 50 + result["profit_pct"])

        output_text = f"""ACTION: {action}
CONFIDENCE: {confidence:.0f}%
ENTRY_PRICE: ${result['entry_price']:.2f}
STOP_LOSS: ${result['entry_price'] * 0.95:.2f}
TAKE_PROFIT: ${result['exit_price']:.2f}
REASONING: Based on RSI of {indicators.get('rsi', 50):.1f} and {'bullish' if indicators.get('macd_bullish', False) else 'bearish'} MACD, with sentiment at {indicators.get('sentiment', 0):.2f}, this trade resulted in {result['profit_pct']:.1f}% profit."""

        examples.append({"input": input_text, "output": output_text})

    logger.info(f"Created {len(examples)} training examples from backtests")
    return examples
