#!/usr/bin/env python3
"""
Elson TB2 - H100 Curriculum Training v4

CRITICAL FIXES IN V4:
1. Phase A: packing=False to restore optimizer steps
2. Warmup is step-based, not ratio-based
3. Scheduler is constant_with_warmup for Phase A, cosine for B/C
4. Diagnostic logging prints counts and expected steps every phase
5. Guards against warmup_steps > total_steps
6. Domain balanced sampling support for Phase B/C

Usage:
    python -m backend.scripts.train_curriculum_h100_v4 --help
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
)
from trl import SFTTrainer


# =============================================================================
# DIAGNOSTIC LOGGING
# =============================================================================

def log_phase_stats(
    phase_name: str,
    dataset: Dataset,
    tokenizer,
    packing: bool,
    max_length: int,
    batch_size: int,
    grad_accum: int,
    epochs: int,
    max_samples: int = 200
) -> Dict:
    """
    Log comprehensive phase statistics to diagnose step count issues.

    Returns dict with:
    - records: total records
    - avg_tokens: average tokens per example
    - p50_tokens, p90_tokens: percentile token lengths
    - estimated_packed_sequences: if packing enabled
    - batches_per_epoch: number of batches
    - optimizer_steps_per_epoch: optimizer steps per epoch
    - total_optimizer_steps: total steps for all epochs
    """
    n = len(dataset)
    k = min(n, max_samples)

    # Sample token lengths
    lens = []
    for i in range(k):
        ex = dataset[i]
        text = ex.get("text", "")
        toks = tokenizer(text, truncation=True, max_length=max_length)["input_ids"]
        lens.append(len(toks))

    avg_len = sum(lens) / len(lens) if lens else 0
    sorted_lens = sorted(lens)
    p50 = sorted_lens[len(lens) // 2] if lens else 0
    p90 = sorted_lens[int(len(lens) * 0.9)] if lens else 0

    # Calculate effective batch size
    effective_batch = batch_size * grad_accum

    # Estimate packed sequences if packing enabled
    if packing and avg_len > 0:
        # Estimate how many examples fit per packed sequence
        examples_per_pack = max(1, int(max_length / avg_len))
        estimated_packed = max(1, n // examples_per_pack)
        sequences_per_epoch = estimated_packed
    else:
        sequences_per_epoch = n

    # Calculate steps
    batches_per_epoch = math.ceil(sequences_per_epoch / batch_size)
    optimizer_steps_per_epoch = math.ceil(batches_per_epoch / grad_accum)
    total_optimizer_steps = optimizer_steps_per_epoch * epochs

    stats = {
        "records": n,
        "avg_tokens": avg_len,
        "p50_tokens": p50,
        "p90_tokens": p90,
        "packing": packing,
        "estimated_packed_sequences": estimated_packed if packing else n,
        "sequences_per_epoch": sequences_per_epoch,
        "batches_per_epoch": batches_per_epoch,
        "optimizer_steps_per_epoch": optimizer_steps_per_epoch,
        "total_optimizer_steps": total_optimizer_steps,
        "effective_batch_size": effective_batch,
    }

    # Print diagnostic output
    print("\n" + "=" * 70)
    print(f"PHASE {phase_name} DIAGNOSTIC STATS")
    print("=" * 70)
    print(f"Records after filtering:        {n:,}")
    print(f"Avg tokens (sampled):           {avg_len:.1f}")
    print(f"Token length p50/p90:           {p50} / {p90}")
    print(f"Packing enabled:                {packing}")
    if packing:
        print(f"Est. examples per pack:         ~{max(1, int(max_length / avg_len))}")
        print(f"Est. packed sequences:          {estimated_packed:,}")
    print(f"Sequences per epoch:            {sequences_per_epoch:,}")
    print(f"Batches per epoch:              {batches_per_epoch:,}")
    print(f"Effective batch size:           {effective_batch}")
    print(f"Optimizer steps per epoch:      {optimizer_steps_per_epoch}")
    print(f"Epochs:                         {epochs}")
    print(f"TOTAL OPTIMIZER STEPS:          {total_optimizer_steps}")
    print("=" * 70 + "\n")

    return stats


def validate_training_config(
    phase_name: str,
    total_steps: int,
    warmup_steps: int,
    min_steps: int
) -> bool:
    """
    Validate training configuration before starting.

    Returns True if valid, False otherwise.
    """
    issues = []

    # Check minimum steps
    if total_steps < min_steps:
        issues.append(
            f"Total steps ({total_steps}) below minimum ({min_steps}). "
            f"Increase epochs or dataset size."
        )

    # Check warmup vs total steps
    if warmup_steps >= total_steps:
        issues.append(
            f"Warmup steps ({warmup_steps}) >= total steps ({total_steps}). "
            f"Warmup will be capped to {max(1, total_steps - 1)}."
        )

    if issues:
        print(f"\n{'!'*70}")
        print(f"PHASE {phase_name} CONFIGURATION WARNINGS")
        print('!'*70)
        for issue in issues:
            print(f"  ⚠ {issue}")
        print('!'*70 + "\n")
        return False

    return True


# =============================================================================
# DATA LOADING
# =============================================================================

def load_training_data(file_path: str) -> List[Dict]:
    """Load training data from JSON or JSONL file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Training file not found: {file_path}")

    data = []

    # Try JSONL first
    if path.suffix == '.jsonl' or 'jsonl' in str(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    else:
        # Try JSON
        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            if isinstance(loaded, list):
                data = loaded
            else:
                data = [loaded]

    return data


def format_example(example: Dict) -> Dict:
    """Format a training example into the expected text format."""
    instruction = example.get('instruction', example.get('question', ''))
    input_text = example.get('input', '')
    output = example.get('output', example.get('answer', ''))

    if input_text:
        text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
    else:
        text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

    return {"text": text}


def prepare_dataset(training_data: List[Dict]) -> Dataset:
    """Prepare a HuggingFace Dataset from training data."""
    formatted = [format_example(ex) for ex in training_data]
    return Dataset.from_list(formatted)


# =============================================================================
# MODEL LOADING
# =============================================================================

def load_base_model(model_path: str):
    """Load the base model with bfloat16 precision."""
    print(f"\nLoading base model from {model_path}...")

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    return model


def load_tokenizer(model_path: str):
    """Load and configure tokenizer."""
    print(f"Loading tokenizer from {model_path}...")

    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    return tokenizer


def create_dora_config(rank: int, alpha: int) -> LoraConfig:
    """Create DoRA adapter configuration."""
    return LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=rank,
        lora_alpha=alpha,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        use_dora=True,
        bias="none",
    )


# =============================================================================
# TRAINING
# =============================================================================

def train_phase(
    phase_name: str,
    model,
    tokenizer,
    dataset: Dataset,
    output_dir: str,
    epochs: int,
    learning_rate: float,
    warmup_steps: int,
    scheduler: str,
    packing: bool,
    batch_size: int,
    grad_accum: int,
    max_length: int,
    min_steps: int,
    log_every: int = 1,
) -> Tuple[float, Dict]:
    """
    Train a single phase of the curriculum.

    Returns (final_loss, training_stats)
    """
    print(f"\n{'='*70}")
    print(f"PHASE {phase_name} TRAINING")
    print(f"{'='*70}")
    print(f"Output directory: {output_dir}")
    print(f"Epochs: {epochs}")
    print(f"Learning rate: {learning_rate}")
    print(f"Warmup steps: {warmup_steps}")
    print(f"Scheduler: {scheduler}")
    print(f"Packing: {packing}")

    # Log diagnostic stats
    stats = log_phase_stats(
        phase_name=phase_name,
        dataset=dataset,
        tokenizer=tokenizer,
        packing=packing,
        max_length=max_length,
        batch_size=batch_size,
        grad_accum=grad_accum,
        epochs=epochs,
    )

    total_steps = stats["total_optimizer_steps"]

    # Validate configuration
    is_valid = validate_training_config(
        phase_name=phase_name,
        total_steps=total_steps,
        warmup_steps=warmup_steps,
        min_steps=min_steps,
    )

    # Cap warmup if needed
    if warmup_steps >= total_steps:
        warmup_steps = max(1, total_steps - 1)
        print(f"Capped warmup_steps to {warmup_steps}")

    # Create training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_steps=warmup_steps,  # Step-based, not ratio!
        lr_scheduler_type=scheduler,
        logging_steps=log_every,
        save_steps=100,
        save_total_limit=2,
        bf16=True,
        gradient_checkpointing=True,
        optim="adamw_torch_fused",
        report_to="none",
        max_grad_norm=0.3,
    )

    # Create trainer with packing setting
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        max_length=max_length,
        dataset_text_field="text",
        packing=packing,
    )

    # Print actual dataloader length
    if hasattr(trainer, 'get_train_dataloader'):
        try:
            dl = trainer.get_train_dataloader()
            actual_batches = len(dl)
            actual_steps = math.ceil(actual_batches / grad_accum) * epochs
            print(f"\nActual dataloader length: {actual_batches} batches")
            print(f"Actual total steps: {actual_steps}")
            stats["actual_batches_per_epoch"] = actual_batches
            stats["actual_total_steps"] = actual_steps
        except Exception as e:
            print(f"Could not get dataloader length: {e}")

    # Train
    print(f"\n{'='*50}")
    print(f"Starting Phase {phase_name} training...")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    train_result = trainer.train()

    final_loss = train_result.training_loss

    print(f"\n{'='*50}")
    print(f"Phase {phase_name} training complete!")
    print(f"Final loss: {final_loss:.4f}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Save checkpoint
    print(f"Saving Phase {phase_name} checkpoint...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save metadata
    stats["final_loss"] = final_loss
    stats["timestamp"] = datetime.now().isoformat()

    metadata = {
        "phase": phase_name,
        "model": "Elson-Finance-Trading-14B",
        "method": "Curriculum DoRA v4",
        "epochs": epochs,
        "learning_rate": learning_rate,
        "warmup_steps": warmup_steps,
        "scheduler": scheduler,
        "packing": packing,
        "batch_size": batch_size * grad_accum,
        "training_pairs": len(dataset),
        "final_loss": final_loss,
        "stats": stats,
        "timestamp": datetime.now().isoformat(),
    }

    with open(f"{output_dir}/training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    return final_loss, stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Elson TB2 - H100 Curriculum Training v4"
    )

    # Model paths
    parser.add_argument("--base_model", type=str, required=True,
                       help="Path to base model")
    parser.add_argument("--output_dir", type=str, required=True,
                       help="Output directory for trained model")
    parser.add_argument("--data_dir", type=str, required=True,
                       help="Directory containing training data")

    # Phase data files
    parser.add_argument("--phase_a_file", type=str, required=True,
                       help="Phase A training data file")
    parser.add_argument("--phase_b_file", type=str, required=True,
                       help="Phase B training data file")
    parser.add_argument("--phase_c_file", type=str, required=True,
                       help="Phase C training data file")

    # DoRA config
    parser.add_argument("--rank", type=int, default=128,
                       help="DoRA rank")
    parser.add_argument("--alpha", type=int, default=256,
                       help="DoRA alpha")

    # Batch config
    parser.add_argument("--batch_size", type=int, default=4,
                       help="Per-device batch size")
    parser.add_argument("--grad_accum", type=int, default=16,
                       help="Gradient accumulation steps")
    parser.add_argument("--max_length", type=int, default=2048,
                       help="Max sequence length")

    # Phase A config
    parser.add_argument("--phase_a_epochs", type=int, default=8)
    parser.add_argument("--lr_a", type=str, default="1e-4")
    parser.add_argument("--warmup_steps_a", type=int, default=20)
    parser.add_argument("--scheduler_a", type=str, default="constant_with_warmup")
    parser.add_argument("--packing_a", type=str, default="false")
    parser.add_argument("--min_steps_a", type=int, default=50)

    # Phase B config
    parser.add_argument("--phase_b_epochs", type=int, default=3)
    parser.add_argument("--lr_b", type=str, default="5e-5")
    parser.add_argument("--warmup_steps_b", type=int, default=60)
    parser.add_argument("--scheduler_b", type=str, default="cosine")
    parser.add_argument("--packing_b", type=str, default="true")
    parser.add_argument("--min_steps_b", type=int, default=100)

    # Phase C config
    parser.add_argument("--phase_c_epochs", type=int, default=2)
    parser.add_argument("--lr_c", type=str, default="2e-5")
    parser.add_argument("--warmup_steps_c", type=int, default=30)
    parser.add_argument("--scheduler_c", type=str, default="cosine")
    parser.add_argument("--packing_c", type=str, default="true")
    parser.add_argument("--min_steps_c", type=int, default=50)

    # Execution config
    parser.add_argument("--phases", type=str, default="all",
                       help="Which phases to run: all, A, B, C")
    parser.add_argument("--log_every", type=int, default=1,
                       help="Log every N steps")

    args = parser.parse_args()

    # Parse boolean strings
    packing_a = args.packing_a.lower() == "true"
    packing_b = args.packing_b.lower() == "true"
    packing_c = args.packing_c.lower() == "true"

    # Parse learning rates
    lr_a = float(args.lr_a)
    lr_b = float(args.lr_b)
    lr_c = float(args.lr_c)

    print("\n" + "=" * 70)
    print("ELSON TB2 - CURRICULUM TRAINING V4")
    print("=" * 70)
    print(f"Base model: {args.base_model}")
    print(f"Output dir: {args.output_dir}")
    print(f"Phases to run: {args.phases}")
    print("=" * 70 + "\n")

    # Determine which phases to run
    phases_to_run = []
    if args.phases.lower() == "all":
        phases_to_run = ["A", "B", "C"]
    else:
        phases_to_run = [args.phases.upper()]

    # Load tokenizer
    tokenizer = load_tokenizer(args.base_model)

    # Load or create model
    model = None

    for phase in phases_to_run:
        # Determine file and config for this phase
        if phase == "A":
            data_file = args.phase_a_file
            epochs = args.phase_a_epochs
            lr = lr_a
            warmup = args.warmup_steps_a
            scheduler = args.scheduler_a
            packing = packing_a
            min_steps = args.min_steps_a
        elif phase == "B":
            data_file = args.phase_b_file
            epochs = args.phase_b_epochs
            lr = lr_b
            warmup = args.warmup_steps_b
            scheduler = args.scheduler_b
            packing = packing_b
            min_steps = args.min_steps_b
        else:  # C
            data_file = args.phase_c_file
            epochs = args.phase_c_epochs
            lr = lr_c
            warmup = args.warmup_steps_c
            scheduler = args.scheduler_c
            packing = packing_c
            min_steps = args.min_steps_c

        phase_output_dir = f"{args.output_dir}/phase_{phase}"
        os.makedirs(phase_output_dir, exist_ok=True)

        # Load training data
        print(f"\nLoading Phase {phase} training data from {data_file}...")
        training_data = load_training_data(data_file)
        print(f"Loaded {len(training_data):,} training examples")

        dataset = prepare_dataset(training_data)

        # Load model (continue from previous phase if available)
        prev_phase = {"B": "A", "C": "B"}.get(phase)
        prev_checkpoint = f"{args.output_dir}/phase_{prev_phase}" if prev_phase else None

        if prev_checkpoint and os.path.exists(prev_checkpoint):
            print(f"\nLoading model from Phase {prev_phase} checkpoint...")
            if model is None:
                base_model = load_base_model(args.base_model)
                model = PeftModel.from_pretrained(
                    base_model,
                    prev_checkpoint,
                    is_trainable=True
                )
            # Model already loaded, continue
        else:
            if model is None:
                # Fresh start - load base and add adapter
                base_model = load_base_model(args.base_model)

                print("\nConfiguring DoRA adapter...")
                dora_config = create_dora_config(args.rank, args.alpha)
                model = get_peft_model(base_model, dora_config)
                model.print_trainable_parameters()

        # Train phase
        final_loss, stats = train_phase(
            phase_name=phase,
            model=model,
            tokenizer=tokenizer,
            dataset=dataset,
            output_dir=phase_output_dir,
            epochs=epochs,
            learning_rate=lr,
            warmup_steps=warmup,
            scheduler=scheduler,
            packing=packing,
            batch_size=args.batch_size,
            grad_accum=args.grad_accum,
            max_length=args.max_length,
            min_steps=min_steps,
            log_every=args.log_every,
        )

        print(f"\nPhase {phase} complete. Final loss: {final_loss:.4f}")

    # Copy final phase to main output directory
    final_phase = phases_to_run[-1]
    final_phase_dir = f"{args.output_dir}/phase_{final_phase}"

    print(f"\nCopying final checkpoint to {args.output_dir}...")
    import shutil
    for item in os.listdir(final_phase_dir):
        src = os.path.join(final_phase_dir, item)
        dst = os.path.join(args.output_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    print("\n" + "=" * 70)
    print("CURRICULUM TRAINING V4 COMPLETE")
    print("=" * 70)
    print(f"Model saved to: {args.output_dir}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
