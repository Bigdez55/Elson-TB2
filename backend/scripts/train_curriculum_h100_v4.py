#!/usr/bin/env python3
"""
Elson TB2 - H100 Curriculum Training v4

CRITICAL FIXES IN V4:
1. Phase A: packing=False to restore optimizer steps
2. Warmup is step-based with guard rails (never ratio-based)
3. Scheduler dynamically selected based on step count
4. Diagnostic logging proves step integrity per phase
5. Guards against warmup_steps > total_steps
6. Auto-epoch increase or error if <50 optimizer steps
7. Domain balanced sampling for full corpus mode
8. Safety calibration filter for guaranteed/risk-free language
9. Output manifest for run comparison

Usage:
    # Curriculum mode (subset training)
    python -m backend.scripts.train_curriculum_h100_v4 --mode curriculum ...

    # Full corpus mode (40,993 with domain balancing)
    python -m backend.scripts.train_curriculum_h100_v4 --mode full ...
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math
import random

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
# CONSTANTS
# =============================================================================

# Minimum optimizer steps per phase (non-negotiable)
MIN_STEPS_PHASE_A = 50
MIN_STEPS_PHASE_B = 100
MIN_STEPS_PHASE_C = 50

# Scheduler thresholds
SCHEDULER_THRESHOLD_PHASE_B = 200
SCHEDULER_THRESHOLD_PHASE_C = 100

# Safety calibration patterns (enterprise compliance)
SAFETY_PATTERNS = [
    r'\bguaranteed?\b',
    r'\brisk[- ]?free\b',
    r'\bno[- ]?risk\b',
    r'\bsafe\s+investment\b',
    r'\bcannot\s+lose\b',
    r'\balways\s+profit\b',
    r'\b100%\s+safe\b',
    r'\bzero\s+risk\b',
]


# =============================================================================
# GIT UTILITIES
# =============================================================================

def get_git_commit_hash() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


# =============================================================================
# SAFETY CALIBRATION FILTER
# =============================================================================

def check_safety_violations(text: str) -> List[str]:
    """Check text for safety calibration violations."""
    violations = []
    text_lower = text.lower()
    for pattern in SAFETY_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(pattern)
    return violations


def filter_safety_violations(
    data: List[Dict],
    remove: bool = True
) -> Tuple[List[Dict], Dict]:
    """
    Filter or flag records with safety calibration violations.

    Returns (filtered_data, stats)
    """
    clean = []
    flagged = []
    violation_counts = defaultdict(int)

    for record in data:
        # Check instruction and output
        text = f"{record.get('instruction', '')} {record.get('output', '')}"
        violations = check_safety_violations(text)

        if violations:
            flagged.append(record)
            for v in violations:
                violation_counts[v] += 1
        else:
            clean.append(record)

    stats = {
        "total_records": len(data),
        "clean_records": len(clean),
        "flagged_records": len(flagged),
        "violation_counts": dict(violation_counts),
    }

    if remove:
        return clean, stats
    else:
        return data, stats


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
    warmup_steps: int,
    learning_rate: float,
    scheduler: str,
    max_samples: int = 200
) -> Dict:
    """
    Log comprehensive phase statistics to diagnose step count issues.

    REQUIRED OUTPUT (per other agent's acceptance criteria):
    1. records after filtering
    2. packing enabled true or false
    3. average tokens per example estimated from a sample
    4. estimated packed sequences when packing is true
    5. batches per epoch
    6. optimizer steps per epoch
    7. total optimizer steps expected for the phase
    8. warmup steps chosen and guard status
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
        examples_per_pack = max(1, int(max_length / avg_len))
        estimated_packed = max(1, n // examples_per_pack)
        sequences_per_epoch = estimated_packed
    else:
        sequences_per_epoch = n
        examples_per_pack = 1
        estimated_packed = n

    # Calculate steps
    batches_per_epoch = math.ceil(sequences_per_epoch / batch_size)
    optimizer_steps_per_epoch = max(1, batches_per_epoch // grad_accum)
    total_optimizer_steps = optimizer_steps_per_epoch * epochs

    # Warmup guard check
    warmup_guard_status = "OK"
    if warmup_steps >= total_optimizer_steps:
        warmup_guard_status = f"CAPPED (was {warmup_steps})"
        warmup_steps = max(1, total_optimizer_steps - 1)

    stats = {
        "records": n,
        "avg_tokens": round(avg_len, 1),
        "p50_tokens": p50,
        "p90_tokens": p90,
        "packing": packing,
        "examples_per_pack": examples_per_pack if packing else 1,
        "estimated_packed_sequences": estimated_packed,
        "sequences_per_epoch": sequences_per_epoch,
        "batches_per_epoch": batches_per_epoch,
        "optimizer_steps_per_epoch": optimizer_steps_per_epoch,
        "total_optimizer_steps": total_optimizer_steps,
        "effective_batch_size": effective_batch,
        "warmup_steps": warmup_steps,
        "warmup_guard_status": warmup_guard_status,
        "learning_rate": learning_rate,
        "scheduler": scheduler,
        "epochs": epochs,
    }

    # Print diagnostic output (REQUIRED FORMAT)
    print("\n" + "=" * 70)
    print(f"PHASE {phase_name} DIAGNOSTIC STATS")
    print("=" * 70)
    print(f"1. Records after filtering:        {n:,}")
    print(f"2. Packing enabled:                {packing}")
    print(f"3. Avg tokens (sampled {k}):       {avg_len:.1f} (p50={p50}, p90={p90})")
    print(f"4. Est. packed sequences:          {estimated_packed:,}" +
          (f" (~{examples_per_pack} examples/pack)" if packing else ""))
    print(f"5. Batches per epoch:              {batches_per_epoch:,}")
    print(f"6. Optimizer steps per epoch:      {optimizer_steps_per_epoch}")
    print(f"7. TOTAL OPTIMIZER STEPS:          {total_optimizer_steps}")
    print(f"8. Warmup steps:                   {warmup_steps} [{warmup_guard_status}]")
    print("-" * 70)
    print(f"   Learning rate:                  {learning_rate}")
    print(f"   Scheduler:                      {scheduler}")
    print(f"   Epochs:                         {epochs}")
    print(f"   Effective batch size:           {effective_batch}")
    print("=" * 70 + "\n")

    return stats


def validate_and_adjust_config(
    phase_name: str,
    total_steps: int,
    warmup_steps: int,
    min_steps: int,
    epochs: int,
    scheduler: str,
    scheduler_threshold: int,
) -> Tuple[int, int, str, bool]:
    """
    Validate and auto-adjust training configuration.

    Returns (adjusted_epochs, adjusted_warmup, adjusted_scheduler, is_valid)

    NON-NEGOTIABLE RULES:
    - If total_steps < min_steps, increase epochs to reach min_steps
    - warmup = min(configured, 10% of total_steps), floor=1, ceiling<total_steps
    - If total_steps < threshold, use constant_with_warmup
    """
    adjusted_epochs = epochs
    adjusted_warmup = warmup_steps
    adjusted_scheduler = scheduler
    issues = []

    # Rule 1: Ensure minimum steps (auto-increase epochs if needed)
    if total_steps < min_steps:
        # Calculate epochs needed
        steps_per_epoch = max(1, total_steps // epochs)
        needed_epochs = math.ceil(min_steps / steps_per_epoch)
        issues.append(
            f"Total steps ({total_steps}) < minimum ({min_steps}). "
            f"AUTO-INCREASING epochs: {epochs} → {needed_epochs}"
        )
        adjusted_epochs = needed_epochs
        total_steps = steps_per_epoch * needed_epochs

    # Rule 2: Warmup guard rails
    # warmup = min(configured, 10% of total_steps), floor=1, ceiling<total_steps
    warmup_10pct = max(1, int(total_steps * 0.1))
    adjusted_warmup = min(warmup_steps, warmup_10pct)
    adjusted_warmup = max(1, adjusted_warmup)  # Floor of 1
    adjusted_warmup = min(adjusted_warmup, total_steps - 1)  # Ceiling < total

    if adjusted_warmup != warmup_steps:
        issues.append(
            f"Warmup adjusted: {warmup_steps} → {adjusted_warmup} "
            f"(10% of {total_steps} steps = {warmup_10pct})"
        )

    # Rule 3: Scheduler based on step count
    if total_steps < scheduler_threshold and scheduler in ["cosine", "linear"]:
        adjusted_scheduler = "constant_with_warmup"
        issues.append(
            f"Scheduler changed: {scheduler} → constant_with_warmup "
            f"(steps {total_steps} < threshold {scheduler_threshold})"
        )

    if issues:
        print(f"\n{'!'*70}")
        print(f"PHASE {phase_name} CONFIGURATION ADJUSTMENTS")
        print('!'*70)
        for issue in issues:
            print(f"  → {issue}")
        print('!'*70 + "\n")

    return adjusted_epochs, adjusted_warmup, adjusted_scheduler, True


# =============================================================================
# DATA LOADING
# =============================================================================

def load_training_data(file_path: str) -> List[Dict]:
    """Load training data from JSON or JSONL file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Training file not found: {file_path}")

    data = []

    if path.suffix == '.jsonl' or 'jsonl' in str(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    else:
        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            if isinstance(loaded, list):
                data = loaded
            else:
                data = [loaded]

    return data


def load_full_corpus(data_dir: str) -> List[Dict]:
    """
    Load the full 40,993 training corpus from all 4 dataset files.
    """
    files = [
        ("final_training_data.json", 23493),
        ("insurance_training_data.json", 10000),
        ("accounting_training_data.json", 5000),
        ("tool_use_training_data.json", 2500),
    ]

    all_data = []
    data_path = Path(data_dir)

    print("\nLoading full corpus (40,993 target):")
    for filename, expected in files:
        filepath = data_path / filename
        if filepath.exists():
            file_data = load_training_data(str(filepath))
            print(f"  {filename}: {len(file_data):,} records " +
                  ("✓" if len(file_data) == expected else f"⚠ expected {expected}"))
            all_data.extend(file_data)
        else:
            print(f"  {filename}: MISSING ⚠")

    print(f"  TOTAL: {len(all_data):,} records")
    return all_data


def domain_balanced_sample(
    data: List[Dict],
    target_size: Optional[int] = None,
    seed: int = 42
) -> List[Dict]:
    """
    Sample data with domain balancing to prevent any domain from dominating.

    Uses inverse frequency weighting to boost underrepresented domains.
    """
    random.seed(seed)

    # Group by domain
    by_domain = defaultdict(list)
    for record in data:
        domain = record.get('category', record.get('domain', 'unknown'))
        by_domain[domain].append(record)

    domains = list(by_domain.keys())
    n_domains = len(domains)

    if target_size is None:
        target_size = len(data)

    # Calculate per-domain quota (equal distribution)
    base_quota = target_size // n_domains
    remainder = target_size % n_domains

    sampled = []
    for i, domain in enumerate(sorted(domains)):
        domain_data = by_domain[domain]
        quota = base_quota + (1 if i < remainder else 0)

        # Sample up to quota (with replacement if needed)
        if len(domain_data) >= quota:
            sampled.extend(random.sample(domain_data, quota))
        else:
            # Oversample small domains
            sampled.extend(domain_data)
            needed = quota - len(domain_data)
            sampled.extend(random.choices(domain_data, k=needed))

    random.shuffle(sampled)
    return sampled


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
# OUTPUT MANIFEST
# =============================================================================

def write_training_manifest(
    output_dir: str,
    base_model: str,
    rank: int,
    alpha: int,
    mode: str,
    dataset_files: Dict[str, int],
    phase_stats: Dict[str, Dict],
    safety_stats: Dict,
    total_training_time: float,
) -> str:
    """
    Write training manifest JSON for run comparison.

    Contains all metadata needed to compare runs months later.
    """
    manifest = {
        "version": "v4",
        "timestamp": datetime.now().isoformat(),
        "git_commit": get_git_commit_hash(),

        # Model config
        "base_model": base_model,
        "adapter_method": "DoRA",
        "rank": rank,
        "alpha": alpha,

        # Training mode
        "mode": mode,

        # Dataset info
        "dataset_files": dataset_files,
        "total_records": sum(dataset_files.values()),

        # Safety calibration
        "safety_filter_enabled": safety_stats.get("flagged_records", 0) > 0,
        "records_filtered_by_safety": safety_stats.get("flagged_records", 0),
        "safety_violations": safety_stats.get("violation_counts", {}),

        # Per-phase stats
        "phases": {},

        # Output
        "output_path": output_dir,
        "total_training_time_seconds": total_training_time,
    }

    for phase_name, stats in phase_stats.items():
        manifest["phases"][phase_name] = {
            "records": stats.get("records"),
            "packing": stats.get("packing"),
            "epochs": stats.get("epochs"),
            "total_optimizer_steps": stats.get("total_optimizer_steps"),
            "warmup_steps": stats.get("warmup_steps"),
            "learning_rate": stats.get("learning_rate"),
            "scheduler": stats.get("scheduler"),
            "final_loss": stats.get("final_loss"),
        }

    manifest_path = Path(output_dir) / "training_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nTraining manifest written to: {manifest_path}")
    return str(manifest_path)


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
    scheduler_threshold: int,
    log_every: int = 1,
) -> Tuple[float, Dict]:
    """
    Train a single phase of the curriculum.

    Returns (final_loss, training_stats)
    """
    print(f"\n{'='*70}")
    print(f"PHASE {phase_name} TRAINING")
    print(f"{'='*70}")

    # Log diagnostic stats FIRST
    stats = log_phase_stats(
        phase_name=phase_name,
        dataset=dataset,
        tokenizer=tokenizer,
        packing=packing,
        max_length=max_length,
        batch_size=batch_size,
        grad_accum=grad_accum,
        epochs=epochs,
        warmup_steps=warmup_steps,
        learning_rate=learning_rate,
        scheduler=scheduler,
    )

    total_steps = stats["total_optimizer_steps"]

    # Validate and auto-adjust configuration
    adjusted_epochs, adjusted_warmup, adjusted_scheduler, is_valid = validate_and_adjust_config(
        phase_name=phase_name,
        total_steps=total_steps,
        warmup_steps=warmup_steps,
        min_steps=min_steps,
        epochs=epochs,
        scheduler=scheduler,
        scheduler_threshold=scheduler_threshold,
    )

    # Update stats with adjustments
    if adjusted_epochs != epochs:
        stats["epochs"] = adjusted_epochs
        stats["epochs_auto_adjusted"] = True
        # Recalculate total steps
        stats["total_optimizer_steps"] = stats["optimizer_steps_per_epoch"] * adjusted_epochs

    stats["warmup_steps"] = adjusted_warmup
    stats["scheduler"] = adjusted_scheduler

    print(f"Output directory: {output_dir}")
    print(f"Final config: epochs={adjusted_epochs}, lr={learning_rate}, "
          f"warmup={adjusted_warmup}, scheduler={adjusted_scheduler}")

    # Create training arguments (NO warmup_ratio - step-based only!)
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=adjusted_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_steps=adjusted_warmup,  # STEP-BASED, NEVER RATIO
        lr_scheduler_type=adjusted_scheduler,
        logging_steps=log_every,
        save_steps=100,
        save_total_limit=2,
        bf16=True,
        gradient_checkpointing=True,
        optim="adamw_torch_fused",
        report_to="none",
        max_grad_norm=0.3,
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        max_length=max_length,
        dataset_text_field="text",
        packing=packing,
    )

    # Print actual dataloader length for verification
    if hasattr(trainer, 'get_train_dataloader'):
        try:
            dl = trainer.get_train_dataloader()
            actual_batches = len(dl)
            actual_steps = (actual_batches // grad_accum) * adjusted_epochs
            print(f"\n[VERIFICATION] Actual dataloader: {actual_batches} batches")
            print(f"[VERIFICATION] Actual total steps: {actual_steps}")
            stats["actual_batches_per_epoch"] = actual_batches
            stats["actual_total_steps"] = actual_steps
        except Exception as e:
            print(f"[VERIFICATION] Could not verify dataloader: {e}")

    # Train
    print(f"\n{'='*50}")
    print(f"Starting Phase {phase_name} training...")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    start_time = datetime.now()
    train_result = trainer.train()
    end_time = datetime.now()

    final_loss = train_result.training_loss
    training_time = (end_time - start_time).total_seconds()

    print(f"\n{'='*50}")
    print(f"Phase {phase_name} training complete!")
    print(f"Final loss: {final_loss:.4f}")
    print(f"Training time: {training_time:.1f}s ({training_time/60:.1f} min)")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Save checkpoint
    print(f"Saving Phase {phase_name} checkpoint...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Update stats
    stats["final_loss"] = final_loss
    stats["training_time_seconds"] = training_time
    stats["timestamp"] = datetime.now().isoformat()

    # Save phase metadata
    metadata = {
        "phase": phase_name,
        "model": "Elson-Finance-Trading-14B",
        "method": "Curriculum DoRA v4",
        "stats": stats,
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

    # Training mode
    parser.add_argument("--mode", type=str, default="curriculum",
                       choices=["curriculum", "full"],
                       help="Training mode: curriculum (subset) or full (40,993)")

    # Phase data files (for curriculum mode)
    parser.add_argument("--phase_a_file", type=str, default="",
                       help="Phase A training data file")
    parser.add_argument("--phase_b_file", type=str, default="",
                       help="Phase B training data file")
    parser.add_argument("--phase_c_file", type=str, default="",
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

    # Safety calibration
    parser.add_argument("--enable_safety_filter", action="store_true",
                       help="Filter records with guaranteed/risk-free language")

    # Execution config
    parser.add_argument("--phases", type=str, default="all",
                       help="Which phases to run: all, A, B, C")
    parser.add_argument("--log_every", type=int, default=1,
                       help="Log every N steps")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for domain balancing")

    args = parser.parse_args()

    # Parse boolean strings
    packing_a = args.packing_a.lower() == "true"
    packing_b = args.packing_b.lower() == "true"
    packing_c = args.packing_c.lower() == "true"

    # Parse learning rates
    lr_a = float(args.lr_a)
    lr_b = float(args.lr_b)
    lr_c = float(args.lr_c)

    # Validate learning rate ordering (lr_a > lr_b > lr_c)
    if not (lr_a >= lr_b >= lr_c):
        print(f"WARNING: Learning rates should decrease: lr_a={lr_a} >= lr_b={lr_b} >= lr_c={lr_c}")

    print("\n" + "=" * 70)
    print("ELSON TB2 - CURRICULUM TRAINING V4")
    print("=" * 70)
    print(f"Mode: {args.mode.upper()}")
    print(f"Base model: {args.base_model}")
    print(f"Output dir: {args.output_dir}")
    print(f"Git commit: {get_git_commit_hash()}")
    print(f"Safety filter: {'ENABLED' if args.enable_safety_filter else 'DISABLED'}")
    print("=" * 70 + "\n")

    # Track overall stats
    all_phase_stats = {}
    dataset_files = {}
    safety_stats = {"flagged_records": 0, "violation_counts": {}}
    training_start = datetime.now()

    # Determine which phases to run
    phases_to_run = []
    if args.phases.lower() == "all":
        phases_to_run = ["A", "B", "C"]
    else:
        phases_to_run = [args.phases.upper()]

    # Load tokenizer
    tokenizer = load_tokenizer(args.base_model)

    # Prepare data based on mode
    if args.mode == "full":
        print("\n" + "=" * 70)
        print("FULL CORPUS MODE (40,993 with domain balancing)")
        print("=" * 70)

        # Load all data
        all_data = load_full_corpus(args.data_dir)
        dataset_files = {
            "final_training_data.json": 23493,
            "insurance_training_data.json": 10000,
            "accounting_training_data.json": 5000,
            "tool_use_training_data.json": 2500,
        }

        # Apply safety filter
        if args.enable_safety_filter:
            all_data, safety_stats = filter_safety_violations(all_data, remove=True)
            print(f"\nSafety filter: {safety_stats['flagged_records']} records removed")
            for pattern, count in safety_stats['violation_counts'].items():
                print(f"  {pattern}: {count}")

        # Domain balanced sampling
        print("\nApplying domain-balanced sampling...")
        all_data = domain_balanced_sample(all_data, seed=args.seed)

        # For full mode, use all data for each phase (or split as needed)
        phase_data = {
            "A": all_data,
            "B": all_data,
            "C": all_data,
        }
    else:
        # Curriculum mode - load phase-specific files
        phase_data = {}
        for phase in phases_to_run:
            if phase == "A":
                data_file = args.phase_a_file
            elif phase == "B":
                data_file = args.phase_b_file
            else:
                data_file = args.phase_c_file

            print(f"\nLoading Phase {phase} data from {data_file}...")
            data = load_training_data(data_file)
            dataset_files[data_file] = len(data)

            # Apply safety filter
            if args.enable_safety_filter:
                data, phase_safety = filter_safety_violations(data, remove=True)
                print(f"Safety filter: {phase_safety['flagged_records']} records removed")
                safety_stats["flagged_records"] += phase_safety["flagged_records"]
                for k, v in phase_safety["violation_counts"].items():
                    safety_stats["violation_counts"][k] = \
                        safety_stats["violation_counts"].get(k, 0) + v

            phase_data[phase] = data

    # Load or create model
    model = None

    for phase in phases_to_run:
        # Get phase config
        if phase == "A":
            epochs = args.phase_a_epochs
            lr = lr_a
            warmup = args.warmup_steps_a
            scheduler = args.scheduler_a
            packing = packing_a
            min_steps = args.min_steps_a
            scheduler_threshold = 100  # Phase A always uses constant_with_warmup
        elif phase == "B":
            epochs = args.phase_b_epochs
            lr = lr_b
            warmup = args.warmup_steps_b
            scheduler = args.scheduler_b
            packing = packing_b
            min_steps = args.min_steps_b
            scheduler_threshold = SCHEDULER_THRESHOLD_PHASE_B
        else:
            epochs = args.phase_c_epochs
            lr = lr_c
            warmup = args.warmup_steps_c
            scheduler = args.scheduler_c
            packing = packing_c
            min_steps = args.min_steps_c
            scheduler_threshold = SCHEDULER_THRESHOLD_PHASE_C

        phase_output_dir = f"{args.output_dir}/phase_{phase}"
        os.makedirs(phase_output_dir, exist_ok=True)

        # Prepare dataset
        dataset = prepare_dataset(phase_data[phase])
        print(f"\nPhase {phase}: {len(dataset):,} training examples")

        # Load model (continue from previous phase if available)
        prev_phase = {"B": "A", "C": "B"}.get(phase)
        prev_checkpoint = f"{args.output_dir}/phase_{prev_phase}" if prev_phase else None

        if prev_checkpoint and os.path.exists(prev_checkpoint) and prev_phase in phases_to_run:
            print(f"\nContinuing from Phase {prev_phase} checkpoint...")
            # Model already loaded and trained, continue
        else:
            if model is None:
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
            scheduler_threshold=scheduler_threshold,
            log_every=args.log_every,
        )

        all_phase_stats[phase] = stats
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

    # Calculate total training time
    training_end = datetime.now()
    total_time = (training_end - training_start).total_seconds()

    # Write training manifest
    manifest_path = write_training_manifest(
        output_dir=args.output_dir,
        base_model=args.base_model,
        rank=args.rank,
        alpha=args.alpha,
        mode=args.mode,
        dataset_files=dataset_files,
        phase_stats=all_phase_stats,
        safety_stats=safety_stats,
        total_training_time=total_time,
    )

    # Print final summary
    print("\n" + "=" * 70)
    print("CURRICULUM TRAINING V4 COMPLETE")
    print("=" * 70)
    print(f"Mode: {args.mode.upper()}")
    print(f"Total training time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"Model saved to: {args.output_dir}")
    print(f"Manifest: {manifest_path}")
    print("\nPer-phase summary:")
    for phase, stats in all_phase_stats.items():
        print(f"  Phase {phase}: loss={stats.get('final_loss', 'N/A'):.4f}, "
              f"steps={stats.get('total_optimizer_steps')}, "
              f"packing={stats.get('packing')}")
    if safety_stats["flagged_records"] > 0:
        print(f"\nSafety calibration: {safety_stats['flagged_records']} records filtered")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
