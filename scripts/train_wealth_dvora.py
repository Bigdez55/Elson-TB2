#!/usr/bin/env python3
"""
Wealth Management DVoRA/QDoRA Fine-Tuning Script

Fine-tunes the Elson-Finance-Trading model with DVoRA (Weight-Decomposed LoRA)
for comprehensive wealth management advisory capabilities.

Features:
- DVoRA: Weight decomposition for better learning (ICML 2024)
- QDoRA: 4-bit quantization + DoRA for production deployment
- 70+ professional roles encoded through training data
- 5 service tiers with role-specific expertise

Usage:
    # DVoRA training (full precision)
    python train_wealth_dvora.py --mode dvora --output ./wealth-dvora

    # QDoRA training (4-bit quantized)
    python train_wealth_dvora.py --mode qdora --output ./wealth-qdora

    # Dry run (validate setup)
    python train_wealth_dvora.py --dry-run
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import torch
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DVoRA Configuration (from GitHub agent architecture)
# ============================================================================

WEALTH_MANAGEMENT_DVORA_CONFIG = {
    "r": 16,                    # Base rank (DVoRA adapts per-layer conceptually)
    "lora_alpha": 32,           # Scaling factor
    "target_modules": [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": TaskType.CAUSAL_LM,
    "use_dora": True,           # Enable DoRA weight decomposition
}

WEALTH_MANAGEMENT_QDORA_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": torch.bfloat16,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_use_double_quant": True,
}

TRAINING_ARGS = {
    "num_train_epochs": 3,
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 8,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "bf16": True,
    "logging_steps": 10,
    "save_steps": 100,
    "save_total_limit": 3,
    "gradient_checkpointing": True,
    "optim": "paged_adamw_8bit",
    "lr_scheduler_type": "cosine",
    "max_grad_norm": 0.3,
}


# ============================================================================
# Wealth Management Training Data (sample for testing)
# ============================================================================

def get_sample_training_data() -> List[Dict[str, str]]:
    """
    Sample training data covering key wealth management domains.
    In production, this would load from the full knowledge base.
    """
    return [
        # Family Office Structure
        {
            "instruction": "What are the key responsibilities of a Family Office CEO?",
            "input": "",
            "output": "The Family Office CEO serves as the strategic integrator and 'connective tissue' across all functions. Key responsibilities include: 1) Strategic planning and vision alignment with family goals, 2) Coordinating between investment (CIO), financial (CFO), operational (COO), legal (General Counsel), and risk (CRO) functions, 3) Serving as primary interface between the family and professional staff, 4) Overseeing governance frameworks and family council operations, 5) Managing external advisor relationships, 6) Ensuring alignment between family values and office operations."
        },
        {
            "instruction": "Explain the role of a Trust Protector in estate planning.",
            "input": "",
            "output": "A Trust Protector serves as oversight to the trustee, functioning like a 'board of directors' for the trust. Key powers include: 1) Removing and replacing trustees who fail to administer properly, 2) Approving or vetoing significant investment decisions, 3) Amending trust terms for unforeseen circumstances or tax law changes, 4) Changing trust situs (jurisdiction) for tax or legal advantages, 5) Resolving disputes between trustees and beneficiaries, 6) Exercising decanting authority to move assets to a new trust. Trust protectors should be independent professionals (attorneys, CPAs) rather than family members to avoid conflicts of interest."
        },
        # Professional Credentials
        {
            "instruction": "What is required to become a Certified Financial Planner (CFP)?",
            "input": "",
            "output": "CFP certification requires: 1) Education: Bachelor's degree plus completion of a CFP Board-registered education program covering 70+ integrated financial planning topics, 2) Examination: Passing the 170-question CFP exam (6 hours), covering professional conduct, financial planning process, risk management, investments, tax planning, retirement planning, and estate planning, 3) Experience: 6,000 hours of professional experience (or 4,000 hours in apprenticeship), 4) Ethics: Background check and commitment to CFP Board's Code of Ethics. Study typically requires 300+ hours. The CFP serves as the 'quarterback' coordinating other advisors in comprehensive wealth management."
        },
        {
            "instruction": "Compare the CFA and CFP designations.",
            "input": "",
            "output": "CFA (Chartered Financial Analyst) vs CFP (Certified Financial Planner): 1) Focus: CFA specializes in investment analysis, portfolio management, and financial modeling; CFP provides comprehensive financial planning across all areas. 2) Study hours: CFA requires 2,000+ hours across 3 levels; CFP requires 300+ hours. 3) Exams: CFA has 3 progressive exams over 2-4 years; CFP has one comprehensive exam. 4) Experience: CFA requires 4,000 hours investment-related; CFP requires 6,000 hours financial planning. 5) Best for: CFA for investment management roles; CFP for comprehensive wealth advisory. In family offices, CFAs typically serve in CIO/investment teams while CFPs serve as primary client advisors."
        },
        # Estate Planning
        {
            "instruction": "What are the key documents in a comprehensive estate plan?",
            "input": "",
            "output": "A comprehensive estate plan includes: 1) Last Will and Testament: Directs asset distribution and names executor, 2) Revocable Living Trust: Avoids probate, provides incapacity planning, maintains privacy, 3) Durable Power of Attorney: Designates financial decision-maker if incapacitated, 4) Healthcare Power of Attorney: Designates medical decision-maker, 5) Living Will/Advance Directive: Documents end-of-life care preferences, 6) HIPAA Authorization: Allows designated persons to access medical records, 7) Beneficiary Designations: For retirement accounts, insurance, TOD accounts, 8) Letter of Intent: Non-binding guidance to fiduciaries. Review every 3-5 years or after major life events."
        },
        # Business Succession
        {
            "instruction": "Who should be on a business succession planning team?",
            "input": "",
            "output": "The ideal business succession 'Dream Team' includes: 1) CFP as 'quarterback' - defines personal financial objectives and coordinates team, 2) M&A Attorney - structures transaction, drafts purchase agreements, manages legal risks, 3) CPA - optimizes tax structure, performs due diligence, plans post-transaction finances, 4) Business Valuation Expert (CVA/ASA) - provides objective pricing, defends against tax challenges, 5) Estate Planning Attorney - updates estate plan, structures seller notes, adjusts trusts, 6) Wealth Manager - manages post-transaction investment strategy, tax-loss harvesting. This team approach ensures comprehensive coverage of legal, tax, financial, and strategic considerations."
        },
        # Tax Planning
        {
            "instruction": "What are key tax planning strategies for high-net-worth individuals?",
            "input": "",
            "output": "Key HNW tax strategies include: 1) Income timing - accelerate/defer income based on rate expectations, 2) Charitable giving - DAFs, CRTs, private foundations for deductions and legacy, 3) Qualified Opportunity Zones - defer/reduce capital gains, 4) Tax-loss harvesting - offset gains with strategic losses, 5) Roth conversions - optimize lifetime tax brackets, 6) Installment sales - spread gain recognition over time, 7) Grantor trusts (IDGTs, GRATs) - transfer appreciation tax-free, 8) Family limited partnerships - valuation discounts for gift/estate purposes, 9) Qualified Small Business Stock (QSBS) - up to $10M exclusion under Section 1202, 10) State tax planning - residency optimization for state income tax savings."
        },
        # Investment Governance
        {
            "instruction": "What should be included in a family office Investment Policy Statement?",
            "input": "",
            "output": "A comprehensive IPS includes: 1) Investment Objectives - return targets, risk tolerance, time horizon, liquidity needs, 2) Asset Allocation - target ranges for each asset class with rebalancing triggers, 3) Investment Guidelines - permitted/prohibited investments, concentration limits, leverage restrictions, 4) Manager Selection Criteria - due diligence process, performance benchmarks, fee expectations, 5) Risk Management - VaR limits, stress testing requirements, hedging policies, 6) Governance - Investment Committee charter, decision authority, voting procedures, 7) Monitoring & Reporting - performance measurement, attribution analysis, reporting frequency, 8) ESG/Impact Considerations - family values alignment, exclusion lists, impact measurement, 9) Review Process - annual IPS review, amendment procedures."
        },
        # Compliance
        {
            "instruction": "What are the 5 pillars of AML/KYC compliance?",
            "input": "",
            "output": "The 5 pillars of AML (Anti-Money Laundering) / KYC (Know Your Customer) compliance are: 1) Customer Identification Program (CIP) - verify identity using documents, non-documentary methods, and risk assessment, 2) Customer Due Diligence (CDD) - understand customer relationships, beneficial ownership, expected transaction patterns, 3) Enhanced Due Diligence (EDD) - additional scrutiny for high-risk customers including PEPs (Politically Exposed Persons), 4) Ongoing Monitoring - transaction surveillance, periodic reviews, suspicious activity detection, 5) Suspicious Activity Reporting (SAR) - file SARs for transactions over $10,000 or suspicious patterns. Family offices must implement these pillars under BSA requirements, with the CCO typically overseeing compliance."
        },
        # Service Tiers
        {
            "instruction": "How should financial advice differ for someone just starting vs high-net-worth?",
            "input": "",
            "output": "ELSON uses 5 service tiers with progressively sophisticated advice: 1) Foundation ($0-10K): Full CFP-level financial literacy, budgeting, emergency fund building, debt payoff strategies, credit building - everyone deserves quality advice from day one, 2) Builder ($10K-75K): Add CPA for tax optimization, retirement account selection (401k vs IRA), insurance fundamentals, first investment portfolio, 3) Growth ($75K-500K): Add CFA for portfolio construction, estate basics, tax-loss harvesting, real estate considerations, 4) Affluent ($500K-5M): Full team access - trust structures, multi-entity planning, business succession, family governance, 5) HNW/UHNW ($5M+): CPWA specialists, family office setup, philanthropy strategy, multi-generational planning, alternative investments. Quality of advice is consistent - only complexity of implementation differs."
        },
        # Fiduciary Duties
        {
            "instruction": "What fiduciary duties does a trustee owe to beneficiaries?",
            "input": "",
            "output": "Trustees owe three core fiduciary duties: 1) Duty of Care - manage trust assets as a prudent investor would, diversify investments, consider risk/return appropriate for beneficiaries, document decisions, 2) Duty of Loyalty - act solely in beneficiaries' interests, avoid self-dealing, disclose conflicts of interest, never benefit personally from trustee position, 3) Duty of Good Faith - administer trust honestly and fairly, balance interests of current vs. remainder beneficiaries, follow trust terms, keep accurate records. Additional duties include: duty to inform (keep beneficiaries reasonably informed), duty to account (provide regular accountings), duty to preserve (protect and maintain trust property). Breach of fiduciary duty can result in personal liability."
        },
        # Alternative Financing
        {
            "instruction": "What are the main alternative financing options for businesses?",
            "input": "",
            "output": "Alternative financing options include: 1) Revenue-Based Financing - repayment as % of monthly revenue (typically 1-9%), no equity dilution, 2) Invoice Factoring - sell receivables at 70-90% advance rate, immediate cash flow, 3) Venture Debt - debt for VC-backed companies, extends runway between equity rounds, 4) Convertible Notes - debt converting to equity at future round with discount (typically 15-25%) and valuation cap, 5) SAFE (Simple Agreement for Future Equity) - similar to convertible note but simpler terms, 6) Equipment Financing - asset-backed loans for machinery/equipment, 7) SBA Loans - government-backed (7(a) up to $5M, CDC/504 for real estate), 8) Merchant Cash Advances - advance on future credit card sales (high cost). Choose based on growth stage, asset base, and equity preservation goals."
        },
    ]


def format_for_training(examples: List[Dict[str, str]], tokenizer) -> Dataset:
    """Format training examples into the Alpaca instruction format."""

    def format_prompt(instruction: str, input_text: str, output: str) -> str:
        if input_text:
            return f"""### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
        else:
            return f"""### Instruction:
{instruction}

### Response:
{output}"""

    formatted = []
    for ex in examples:
        text = format_prompt(ex["instruction"], ex.get("input", ""), ex["output"])
        formatted.append({"text": text})

    dataset = Dataset.from_list(formatted)

    def tokenize(examples):
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            max_length=2048,
            padding="max_length",
        )
        # Set labels equal to input_ids for causal LM training
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    return dataset.map(tokenize, batched=True, remove_columns=["text"])


def load_base_model(
    model_name: str,
    use_quantization: bool = False
) -> tuple:
    """Load base model with optional quantization."""

    logger.info(f"Loading model: {model_name}")

    # Quantization config for QDoRA
    quantization_config = None
    if use_quantization:
        logger.info("Enabling 4-bit quantization (QDoRA mode)")
        quantization_config = BitsAndBytesConfig(
            **WEALTH_MANAGEMENT_QDORA_CONFIG
        )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16 if not use_quantization else None,
    )

    # Prepare for k-bit training if quantized
    if use_quantization:
        model = prepare_model_for_kbit_training(model)

    return model, tokenizer


def create_dvora_model(model, config: Dict[str, Any]):
    """Apply DVoRA (DoRA) adapters to the model."""

    logger.info("Creating DVoRA (DoRA) adapters...")

    lora_config = LoraConfig(**config)

    # Get PEFT model
    model = get_peft_model(model, lora_config)

    # Log trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")

    return model


def train(
    model_name: str = "meta-llama/Llama-2-7b-hf",
    output_dir: str = "./wealth-dvora",
    mode: str = "dvora",
    max_samples: int = None,
    dry_run: bool = False
):
    """
    Run DVoRA/QDoRA fine-tuning.

    Args:
        model_name: Base model to fine-tune
        output_dir: Directory to save trained model
        mode: 'dvora' (full precision) or 'qdora' (4-bit quantized)
        max_samples: Limit training samples (for testing)
        dry_run: Just validate setup without training
    """
    logger.info("="*60)
    logger.info(f"Wealth Management {mode.upper()} Fine-Tuning")
    logger.info("="*60)

    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"GPU: {gpu_name} ({gpu_memory:.1f} GB)")
    else:
        logger.warning("No GPU available - training will be slow")

    # Load model
    use_quantization = (mode == "qdora")
    model, tokenizer = load_base_model(model_name, use_quantization)

    # Apply DVoRA adapters
    model = create_dvora_model(model, WEALTH_MANAGEMENT_DVORA_CONFIG)

    # Get training data
    logger.info("Preparing training data...")
    training_data = get_sample_training_data()

    if max_samples:
        training_data = training_data[:max_samples]

    logger.info(f"Training samples: {len(training_data)}")

    # Format dataset
    train_dataset = format_for_training(training_data, tokenizer)

    if dry_run:
        logger.info("Dry run complete - setup validated successfully")
        logger.info(f"Model: {model_name}")
        logger.info(f"Mode: {mode.upper()}")
        logger.info(f"Training samples: {len(training_data)}")
        logger.info(f"DoRA enabled: {WEALTH_MANAGEMENT_DVORA_CONFIG['use_dora']}")
        return

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        **TRAINING_ARGS,
        report_to="none",
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
    )

    # Train
    logger.info("Starting training...")
    trainer.train()

    # Save model
    logger.info(f"Saving model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    logger.info("="*60)
    logger.info("Training complete!")
    logger.info(f"Model saved to: {output_dir}")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Wealth Management DVoRA/QDoRA Fine-Tuning"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="meta-llama/Llama-2-7b-hf",
        help="Base model to fine-tune"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./wealth-dvora",
        help="Output directory for trained model"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["dvora", "qdora"],
        default="dvora",
        help="Training mode: dvora (full precision) or qdora (4-bit)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Limit training samples (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup without training"
    )

    args = parser.parse_args()

    train(
        model_name=args.model,
        output_dir=args.output,
        mode=args.mode,
        max_samples=args.max_samples,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
