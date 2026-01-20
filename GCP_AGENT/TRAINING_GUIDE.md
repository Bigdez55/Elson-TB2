# Elson TB2 - Comprehensive Training Guide

**Version:** 1.0.0
**Last Updated:** 2026-01-19
**Purpose:** Complete guide for training Elson-Finance-Trading-14B using curriculum learning

---

## Table of Contents

1. [Overview](#1-overview)
2. [Training Architecture](#2-training-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Training Data Structure](#4-training-data-structure)
5. [Curriculum Training Method](#5-curriculum-training-method)
6. [Step-by-Step Training Instructions](#6-step-by-step-training-instructions)
7. [Scripts Reference](#7-scripts-reference)
8. [Hyperparameters](#8-hyperparameters)
9. [Monitoring & Validation](#9-monitoring--validation)
10. [Troubleshooting](#10-troubleshooting)
11. [Post-Training Deployment](#11-post-training-deployment)

---

## 1. Overview

### What is Elson TB2?

Elson TB2 is an AGI/ASI-grade financial platform designed to rival BlackRock Aladdin. The core model is **Elson-Finance-Trading-14B**, a 14 billion parameter model created through a 3-stage merge:

```
Stage 1: SLERP Merge (Reasoning + Math)
├── Input: DeepSeek-R1-Distill-Qwen-14B (48 layers)
├── Input: Qwen2.5-Math-14B-Instruct (48 layers)
└── Output: elson-reason-math-14b

Stage 2: TIES Merge (Financial Domain)
├── Input: elson-reason-math-14b (60% weight)
├── Input: FinGPT/fingpt-mt_llama2-13b_lora (25% weight)
├── Input: FinGPT/FinLLaMA (15% weight)
└── Output: elson-finance-trading-14b

Stage 3: DARE Pruning (Refinement)
├── Input: elson-finance-trading-14b
├── Pruning: 20% small weight deltas dropped
└── Output: elson-finance-trading-14b-final ← BASE MODEL
```

### Training Method: 3-Phase Curriculum Learning

We use **curriculum learning** - training the model progressively from easy to hard examples across multiple phases. This is superior to flat training because:

1. **Better convergence** - Model builds foundational knowledge before tackling complex scenarios
2. **Domain competence** - Phase A ensures mastery of individual domains
3. **Cross-domain reasoning** - Phase B forces generalization
4. **Edge case robustness** - Phase C stress-tests with extreme scenarios

---

## 2. Training Architecture

### Infrastructure

| Component | Specification | Cost |
|-----------|--------------|------|
| **Training GPU** | NVIDIA H100 80GB HBM3 | ~$2.50/hr (Spot) |
| **VM Name** | `elson-h100-spot` | us-central1-a |
| **Base Model** | 27.52 GB (14B parameters) | GCS storage |
| **Training Method** | DoRA (Weight-Decomposed Low-Rank Adaptation) | - |
| **Quantization** | AWQ 4-bit (optional) | - |

### Training Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRICULUM TRAINING PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐   │
│   │  Domain Buckets  │────▶│ Curriculum       │────▶│ Training         │   │
│   │  (80+ domains)   │     │ Sampler          │     │ Manifests        │   │
│   │  easy/med/hard   │     │                  │     │ Phase A/B/C      │   │
│   └──────────────────┘     └──────────────────┘     └──────────────────┘   │
│                                                              │              │
│                                                              ▼              │
│   ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐   │
│   │  DoRA Adapter    │◀────│ H100 Training    │◀────│ Merged Training  │   │
│   │  (4.2 GB)        │     │ Phase A→B→C      │     │ Data (JSONL)     │   │
│   └──────────────────┘     └──────────────────┘     └──────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│   ┌──────────────────┐     ┌──────────────────┐                            │
│   │  Upload to GCS   │────▶│  Deploy vLLM     │                            │
│   │                  │     │  on L4 GPU       │                            │
│   └──────────────────┘     └──────────────────┘                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Prerequisites

### 3.1 GCP Setup

```bash
# Authenticate
gcloud auth login
gcloud config set project elson-33a95

# Verify H100 VM exists
gcloud compute instances list --filter="name~elson-h100"

# Expected output:
# NAME              ZONE           MACHINE_TYPE    STATUS
# elson-h100-spot   us-central1-a  a3-highgpu-1g   TERMINATED
```

### 3.2 Repository Setup

```bash
# Clone repository (if not already done)
git clone https://github.com/Bigdez55/Elson-TB2.git
cd Elson-TB2

# Pull latest changes (CRITICAL before training)
git pull origin main
```

### 3.3 Verify Training Data Exists

```bash
# Check domain buckets exist
ls -la backend/training_data/domain_buckets/

# Expected: 80+ subdirectories (accounting, banking, compliance, etc.)

# Check total bucket files
find backend/training_data/domain_buckets -name "*.jsonl" | wc -l

# Expected: 80+ files

# Check consolidated training data
ls -la backend/training_data/*.json

# Expected files:
# - final_training_data.json (23,493 pairs)
# - insurance_training_data.json (10,000 pairs)
# - accounting_training_data.json (5,000 pairs)
# - tool_use_training_data.json (2,500 pairs)
```

### 3.4 Verify Scripts Exist

```bash
# Check curriculum scripts
ls -la scripts/curriculum_sampler.py
ls -la scripts/domain_bucket_builder.py
ls -la scripts/train-curriculum-h100.sh

# Check all scripts are executable
chmod +x scripts/*.sh
```

---

## 4. Training Data Structure

### 4.1 Domain Buckets

Training data is organized into **domain buckets** with **difficulty tiers**:

```
backend/training_data/domain_buckets/
│
├── accounting/
│   ├── easy.jsonl          # Basic accounting concepts
│   ├── medium.jsonl        # Intermediate scenarios
│   └── hard.jsonl          # Complex multi-step problems
│
├── banking/
│   ├── easy.jsonl
│   └── hard.jsonl
│
├── compliance/
│   ├── medium.jsonl
│   └── hard.jsonl
│
├── derivatives/
│   └── hard.jsonl          # Derivatives are inherently complex
│
├── estate_planning/
│   ├── easy.jsonl
│   ├── medium.jsonl
│   ├── hard.jsonl
│   └── extremely_complex.jsonl
│
├── federal_income_tax/
│   ├── medium.jsonl
│   └── hard.jsonl
│
├── general_finance/
│   ├── easy.jsonl
│   ├── medium.jsonl
│   ├── hard.jsonl
│   └── extremely_complex.jsonl
│
├── insurance/
│   └── medium.jsonl
│
├── portfolio_management/
│   ├── easy.jsonl
│   └── medium.jsonl
│
├── retirement_planning/
│   └── easy.jsonl
│
├── securities_regulation/
│   ├── medium.jsonl
│   └── hard.jsonl
│
├── trust_administration/
│   └── medium.jsonl
│
└── ... (80+ domains total)
```

### 4.2 Difficulty Tier Definitions

| Tier | Description | Example |
|------|-------------|---------|
| **easy** | Single concept, direct answer | "What is a 401(k)?" |
| **medium** | Multiple concepts, some reasoning | "Compare Roth IRA vs Traditional IRA for a 35-year-old earning $80K" |
| **hard** | Complex scenario, multi-step reasoning | "Design a tax-efficient withdrawal strategy for a retiree with $2M in mixed accounts" |
| **extremely_complex** | Edge cases, multi-domain, compliance-heavy | "Structure a GRAT for a business owner with $50M estate, considering GST, state taxes, and succession" |

### 4.3 Data Format (JSONL)

Each line in a bucket file is a JSON object:

```json
{
  "instruction": "What are the contribution limits for a 401(k) in 2026?",
  "input": "",
  "output": "For 2026, the 401(k) contribution limit is $23,500 for employees under 50. Those 50 and older can make an additional catch-up contribution of $7,500, for a total of $31,000. Employer matching contributions do not count toward these limits. The total combined employee and employer contribution limit is $70,500 ($77,500 for those 50+).",
  "category": "retirement_planning",
  "difficulty": "easy",
  "source": "synthetic_domain"
}
```

### 4.4 Dataset Corpus: Source of Truth

> **The full Phase 2 training corpus is exactly 40,993 Q&A pairs.**

| Dataset File | Records | Purpose |
|--------------|---------|---------|
| `final_training_data.json` | 23,493 | Core financial planning backbone |
| `insurance_training_data.json` | 10,000 | Insurance domain competence |
| `accounting_training_data.json` | 5,000 | Accounting/GAAP/IFRS workflows |
| `tool_use_training_data.json` | 2,500 | Structured outputs and tool calling |
| **TOTAL** | **40,993** | **Full training corpus** |

#### Why Curriculum Runs Use Subsets

Curriculum training sessions intentionally train on a **subset** of the full corpus per cycle (typically 15,000-20,000 examples) to stage learning by difficulty and domain. This is not a bug - it's the design.

- **Full corpus training** (40,993): Used for final production runs
- **Curriculum cycles** (15-20K): Used for iterative development and domain balancing

#### Why Not One Giant File?

The corpus is split into four schema-compatible files to allow:
1. **Domain-weighted sampling** - Prevent general_finance from dominating
2. **Targeted competence building** - Train specific weaknesses
3. **Flexible curriculum design** - Mix and match for different training goals

### 4.5 Training Data Statistics (Summary)

| Source | Pairs | Description |
|--------|-------|-------------|
| **Domain Buckets** | 15,000+ | Organized by domain and difficulty |
| final_training_data.json | 23,493 | Core financial Q&A |
| insurance_training_data.json | 10,000 | Insurance workflows |
| accounting_training_data.json | 5,000 | Accounting integration |
| tool_use_training_data.json | 2,500 | Tool calling examples |
| **TOTAL** | **40,993** | Combined training corpus |

---

## 5. Curriculum Training Method

### 5.1 The 3-Phase Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   PHASE A: DOMAIN BLOCKS                                                     │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                              │
│   Purpose: Build domain-specific competence                                  │
│   Method:  Train one domain at a time until competence minimum               │
│                                                                              │
│   Difficulty Distribution:                                                   │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │  Easy: 35%  │  Medium: 35%  │  Hard: 25%  │  Extreme: 5%   │           │
│   └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│   Domain Quota: ~1,000 examples per domain                                   │
│   Output: Domain-specific competence in all 62+ domains                      │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PHASE B: MIXED CURRICULUM                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                              │
│   Purpose: Force cross-domain generalization                                 │
│   Method:  Shuffle all domains together, cap any single domain at 15%       │
│                                                                              │
│   Difficulty Distribution:                                                   │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │  Easy: 20%  │  Medium: 40%  │  Hard: 30%  │  Extreme: 10%  │           │
│   └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│   Target: 10,000 examples                                                    │
│   Domain Cap: Max 15% per domain (prevents overfitting)                      │
│   Output: Cross-domain reasoning and transfer learning                       │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PHASE C: STRESS EPOCH                                                      │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                              │
│   Purpose: Harden model against edge cases and high-risk scenarios           │
│   Method:  Prioritize complex, compliance-heavy, multi-domain examples       │
│                                                                              │
│   Difficulty Distribution:                                                   │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │  Easy: 10%  │  Medium: 25%  │  Hard: 35%  │  Extreme: 30%  │           │
│   └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│   Target: 5,000 examples                                                     │
│   Focus Domains:                                                             │
│   - compliance          - securities_regulation                              │
│   - aml_kyc             - federal_income_tax                                 │
│   - insurance           - derivatives                                        │
│   - estate_planning     - trade_execution                                    │
│                                                                              │
│   Output: Robust handling of edge cases and compliance scenarios             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Why Curriculum Learning Works

| Aspect | Flat Training | Curriculum Training |
|--------|--------------|---------------------|
| **Learning progression** | Random difficulty | Easy → Hard |
| **Domain coverage** | Unbalanced | Guaranteed per-domain competence |
| **Convergence** | Often unstable | Smoother, more stable |
| **Edge case handling** | Undertrained | Explicitly stress-tested |
| **Cross-domain reasoning** | Accidental | Explicitly trained in Phase B |

### 5.3 Phase Continuity

Training is **continuous across phases**:

```
Phase A checkpoint → Continue training → Phase B checkpoint → Continue → Phase C final
```

The model preserves learning from previous phases while adding new capabilities.

---

## 6. Step-by-Step Training Instructions

### 6.1 Pre-Training Checklist

```bash
# ═══════════════════════════════════════════════════════════════════════════
# PRE-TRAINING CHECKLIST (Run on local machine or GCP Cloud Shell)
# ═══════════════════════════════════════════════════════════════════════════

# 1. Pull latest code
cd ~/Elson-TB2
git pull origin main

# 2. Verify training data exists
echo "Checking domain buckets..."
BUCKET_COUNT=$(find backend/training_data/domain_buckets -name "*.jsonl" 2>/dev/null | wc -l)
echo "Domain bucket files: $BUCKET_COUNT (expected: 80+)"

# 3. Verify curriculum sampler exists
ls -la scripts/curriculum_sampler.py

# 4. Check GCP authentication
gcloud auth list
gcloud config get-value project  # Should show: elson-33a95

# 5. Verify H100 VM exists
gcloud compute instances list --filter="name=elson-h100-spot"
```

### 6.2 Generate Curriculum Manifests

```bash
# ═══════════════════════════════════════════════════════════════════════════
# GENERATE CURRICULUM MANIFESTS (Run before training)
# ═══════════════════════════════════════════════════════════════════════════

cd ~/Elson-TB2

# Generate all three phases at once
python3 scripts/curriculum_sampler.py --phase all --target-records 15000

# OR generate phases individually:
# python3 scripts/curriculum_sampler.py --phase A --target-records 5000
# python3 scripts/curriculum_sampler.py --phase B --target-records 10000
# python3 scripts/curriculum_sampler.py --phase C --target-records 5000

# Verify manifests were created
echo "Generated manifests:"
ls -la backend/training_data/curriculum_runs/

# Expected output:
# manifest_phaseA_YYYYMMDD_HHMMSS.jsonl
# manifest_phaseB_YYYYMMDD_HHMMSS.jsonl
# manifest_phaseC_YYYYMMDD_HHMMSS.jsonl
# merged_phaseA_YYYYMMDD_HHMMSS.jsonl
# merged_phaseB_YYYYMMDD_HHMMSS.jsonl
# merged_phaseC_YYYYMMDD_HHMMSS.jsonl
# manifest_stats_phaseA_YYYYMMDD_HHMMSS.json
# manifest_stats_phaseB_YYYYMMDD_HHMMSS.json
# manifest_stats_phaseC_YYYYMMDD_HHMMSS.json

# Check statistics
echo "Phase A stats:"
cat backend/training_data/curriculum_runs/manifest_stats_phaseA_*.json | head -20

echo "Phase B stats:"
cat backend/training_data/curriculum_runs/manifest_stats_phaseB_*.json | head -20

echo "Phase C stats:"
cat backend/training_data/curriculum_runs/manifest_stats_phaseC_*.json | head -20
```

### 6.3 Start H100 VM

```bash
# ═══════════════════════════════════════════════════════════════════════════
# START H100 VM
# ═══════════════════════════════════════════════════════════════════════════

# Start the H100 Spot VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# Wait for VM to be ready (takes 1-2 minutes)
echo "Waiting for VM to start..."
sleep 60

# Verify VM is running
gcloud compute instances list --filter="name=elson-h100-spot"
# STATUS should be: RUNNING

# SSH into the VM
gcloud compute ssh elson-h100-spot --zone=us-central1-a
```

### 6.4 Setup on H100 VM

```bash
# ═══════════════════════════════════════════════════════════════════════════
# SETUP ON H100 VM (Run after SSH)
# ═══════════════════════════════════════════════════════════════════════════

# Verify GPU is available
nvidia-smi

# Expected output:
# NVIDIA H100 80GB HBM3
# Memory: 80GB

# Clone or update repository
if [ -d "Elson-TB2" ]; then
    cd Elson-TB2
    git pull origin main
else
    git clone https://github.com/Bigdez55/Elson-TB2.git
    cd Elson-TB2
fi

# Verify we have the latest code
git log --oneline -3

# Check training script exists
ls -la scripts/train-curriculum-h100.sh
```

### 6.5 Run Curriculum Training

```bash
# ═══════════════════════════════════════════════════════════════════════════
# RUN CURRICULUM TRAINING (On H100 VM)
# ═══════════════════════════════════════════════════════════════════════════

cd ~/Elson-TB2

# Option 1: Dry run first (recommended)
./scripts/train-curriculum-h100.sh --dry-run

# This will:
# - Check GPU availability
# - Verify training data exists
# - Show what would be trained
# - NOT actually train

# Option 2: Run full curriculum training
./scripts/train-curriculum-h100.sh

# This will:
# 1. Install dependencies
# 2. Download base model from GCS (27.52 GB) - first run only
# 3. Run Phase A training (domain blocks)
# 4. Run Phase B training (mixed curriculum)
# 5. Run Phase C training (stress epoch)
# 6. Upload final model to GCS

# Option 3: Run specific phase only
./scripts/train-curriculum-h100.sh --phase A  # Domain blocks only
./scripts/train-curriculum-h100.sh --phase B  # Mixed curriculum only
./scripts/train-curriculum-h100.sh --phase C  # Stress epoch only

# ═══════════════════════════════════════════════════════════════════════════
# MONITORING TRAINING
# ═══════════════════════════════════════════════════════════════════════════

# In a separate terminal, monitor GPU usage:
watch -n 1 nvidia-smi

# Expected during training:
# - GPU Memory: 60-70 GB used
# - GPU Utilization: 90-100%
# - Temperature: 60-80°C

# Monitor training logs:
# Training output is printed to stdout
# Look for:
# - "Starting Phase X training..."
# - Loss values every 10 steps
# - "Phase X training complete! Final loss: X.XXXX"
```

### 6.6 Post-Training Steps

```bash
# ═══════════════════════════════════════════════════════════════════════════
# POST-TRAINING (On H100 VM)
# ═══════════════════════════════════════════════════════════════════════════

# Verify model was uploaded to GCS
gsutil ls -l gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/

# Expected files:
# - adapter_config.json
# - adapter_model.safetensors
# - training_metadata.json
# - tokenizer files

# Check model size
gsutil du -sh gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/

# Expected: ~4-5 GB

# ═══════════════════════════════════════════════════════════════════════════
# STOP H100 VM (CRITICAL - Saves money!)
# ═══════════════════════════════════════════════════════════════════════════

# Exit SSH session
exit

# Stop the VM from local machine or Cloud Shell
gcloud compute instances stop elson-h100-spot --zone=us-central1-a

# Verify VM is stopped
gcloud compute instances list --filter="name=elson-h100-spot"
# STATUS should be: TERMINATED
```

---

## 7. Scripts Reference

### 7.1 Curriculum Training Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/curriculum_sampler.py` | Generate Phase A/B/C training manifests | `python scripts/curriculum_sampler.py --phase all` |
| `scripts/domain_bucket_builder.py` | Organize raw data into domain/difficulty buckets | `python scripts/domain_bucket_builder.py` |
| `scripts/train-curriculum-h100.sh` | Run full 3-phase curriculum training on H100 | `./scripts/train-curriculum-h100.sh` |

### 7.2 Curriculum Sampler Options

```bash
python scripts/curriculum_sampler.py [OPTIONS]

Options:
  --phase {A,B,C,all}      Which phase to generate (default: B)
  --buckets-dir PATH       Domain buckets directory (default: backend/training_data/domain_buckets)
  --output-dir PATH        Output directory for manifests (default: backend/training_data/curriculum_runs)
  --target-records N       Target number of records (default: 10000)
  --domain DOMAIN          Specific domain for Phase A (optional)
  --seed N                 Random seed for reproducibility (default: 42)
  --config PATH            YAML config file (overrides other args)
  --no-merge               Don't merge data, only create manifest

Examples:
  # Generate all phases with 15K records each
  python scripts/curriculum_sampler.py --phase all --target-records 15000

  # Generate Phase A for specific domain
  python scripts/curriculum_sampler.py --phase A --domain federal_income_tax

  # Use custom config
  python scripts/curriculum_sampler.py --config curriculum_config.yaml
```

### 7.3 Training Data Generation Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/generate_synthetic_qa.py` | Generate synthetic Q&A pairs | 15,000+ pairs |
| `scripts/augment_training_data.py` | Paraphrase, difficulty scale, scenario inject | Multiplied dataset |
| `scripts/domain_classifier.py` | Classify Q&A into 62 domains | Categorized data |
| `scripts/merge_all_training_data.py` | Merge all sources, deduplicate | Final dataset |
| `scripts/validate_training_data.py` | Quality validation | Validation report |

### 7.4 Deployment Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/deploy-vllm-dora.sh` | Deploy model on L4 with vLLM | `./scripts/deploy-vllm-dora.sh l4 dora` |
| `scripts/run_model_evaluation.py` | Run 431-question benchmark | `python scripts/run_model_evaluation.py` |

---

## 8. Hyperparameters

### 8.1 DoRA Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `r` (rank) | 128 | LoRA rank - higher = more expressiveness |
| `lora_alpha` | 256 | Scaling factor (typically 2x rank) |
| `lora_dropout` | 0.05 | Regularization dropout |
| `use_dora` | True | Enable weight-decomposed adaptation |
| `target_modules` | q,k,v,o,gate,up,down_proj | All attention + MLP layers |
| `bias` | "none" | Don't train biases |

### 8.2 Training Arguments

| Parameter | Value | Description |
|-----------|-------|-------------|
| `per_device_train_batch_size` | 16 | Batch size per GPU |
| `gradient_accumulation_steps` | 4 | Effective batch = 16 × 4 = 64 |
| `num_train_epochs` | 2 per phase | 6 total across all phases |
| `learning_rate` | 2e-4 | Standard for LoRA/DoRA |
| `lr_scheduler_type` | "cosine" | Cosine decay with warmup |
| `warmup_ratio` | 0.03 | 3% of steps for warmup |
| `weight_decay` | 0.01 | L2 regularization |
| `max_grad_norm` | 0.3 | Gradient clipping |
| `bf16` | True | H100 native precision |
| `gradient_checkpointing` | True | Memory optimization |
| `optim` | "adamw_torch_fused" | Fast fused optimizer |
| `max_seq_length` | 2048 | Context window |
| `packing` | True | Pack short sequences |

### 8.3 Phase-Specific Settings

| Phase | Epochs | Learning Rate | Notes |
|-------|--------|---------------|-------|
| A | 2 | 2e-4 | Build domain competence |
| B | 2 | 2e-4 | Cross-domain transfer |
| C | 2 | 1e-4 | Lower LR for fine-tuning |

---

## 9. Monitoring & Validation

### 9.1 Training Metrics to Watch

```
During training, monitor these metrics:

Loss:
- Starting loss: ~1.5-2.0
- Phase A end: ~0.8-1.0
- Phase B end: ~0.5-0.7
- Phase C end: ~0.3-0.5

GPU Metrics:
- Memory usage: 60-70 GB of 80 GB
- Utilization: 90-100%
- Temperature: 60-80°C (normal for H100)

Time Estimates:
- Phase A: ~15-20 min
- Phase B: ~20-25 min
- Phase C: ~10-15 min
- Total: ~45-60 min
```

### 9.2 Validation Commands

```bash
# After training completes, run these validation checks:

# 1. Check model was saved
ls -la /workspace/wealth-dora-elson14b-h100-v3-curriculum/

# 2. Check training metadata
cat /workspace/wealth-dora-elson14b-h100-v3-curriculum/training_metadata.json

# 3. Verify GCS upload
gsutil ls gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/

# 4. Test inference (quick sanity check)
python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Load base + adapter
base = AutoModelForCausalLM.from_pretrained(
    "/workspace/base_model",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
model = PeftModel.from_pretrained(
    base,
    "/workspace/wealth-dora-elson14b-h100-v3-curriculum"
)
tokenizer = AutoTokenizer.from_pretrained("/workspace/wealth-dora-elson14b-h100-v3-curriculum")

# Test query
prompt = "### Instruction:\nWhat is a 401(k) retirement account?\n\n### Response:\n"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
EOF
```

### 9.3 Post-Training Evaluation

```bash
# Run the 431-question benchmark
python scripts/run_model_evaluation.py \
  --model gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum \
  --output benchmark_results.json

# Target metrics:
# - Overall accuracy: >80%
# - Per-domain accuracy: >70%
# - Tool-use accuracy: >95%
```

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No GPU detected" | Not on H100 VM | SSH into `elson-h100-spot` |
| OOM (Out of Memory) | Batch too large | Reduce `BATCH_SIZE` to 8 |
| "Training data not found" | Wrong directory | Run `git pull origin main` |
| "Manifest not found" | Curriculum not generated | Run `curriculum_sampler.py` |
| Slow training | CPU offloading | Verify GPU utilization with `nvidia-smi` |
| "Quota exceeded" | GCS storage full | Delete old model versions |
| VM preempted | Spot instance reclaimed | Restart VM and resume from checkpoint |

### 10.2 Recovery from Preemption

H100 Spot VMs can be preempted (stopped by Google). To recover:

```bash
# 1. Restart the VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# 2. SSH back in
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# 3. Check if checkpoints exist
ls -la /workspace/wealth-dora-elson14b-h100-v3-curriculum/phase_*/

# 4. Resume training from last completed phase
# If Phase A completed, run Phase B:
./scripts/train-curriculum-h100.sh --phase B

# If Phase B completed, run Phase C:
./scripts/train-curriculum-h100.sh --phase C
```

### 10.3 Debugging Commands

```bash
# Check GPU status
nvidia-smi

# Check disk space
df -h

# Check memory
free -h

# Check running processes
ps aux | grep python

# Kill stuck training
pkill -f train

# Check GCS connectivity
gsutil ls gs://elson-33a95-elson-models/

# Verify Python environment
pip list | grep -E "torch|transformers|peft"
```

---

## 11. Post-Training Deployment

### 11.1 Deploy to vLLM on L4

```bash
# After training completes and H100 is stopped:

# 1. Deploy vLLM with new model
./scripts/deploy-vllm-dora.sh l4 dora

# 2. Wait for deployment (10-15 minutes)

# 3. Get external IP
gcloud compute instances describe elson-vllm-l4 \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# 4. Test API
curl http://EXTERNAL_IP:8000/v1/models

# 5. Run evaluation
python scripts/run_evaluation_benchmark.py --api-url http://EXTERNAL_IP:8000
```

### 11.2 Model Versioning

```
GCS Model Structure:
gs://elson-33a95-elson-models/
├── elson-finance-trading-14b-final/     # Base model (27.52 GB)
├── wealth-dora-elson14b-h100/           # DoRA v1 (deprecated)
├── wealth-dora-elson14b-h100-v2/        # DoRA v2 (flat training)
├── wealth-dora-elson14b-h100-v3-curriculum/  # DoRA v3 (curriculum) ← LATEST
└── elson-finance-trading-wealth-14b-q4/ # QDoRA (quantized)
```

---

## Summary

### Quick Reference Commands

```bash
# ═══════════════════════════════════════════════════════════════════════════
# COMPLETE TRAINING WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

# Step 1: Pull latest code
cd ~/Elson-TB2 && git pull origin main

# Step 2: Generate curriculum manifests
python scripts/curriculum_sampler.py --phase all --target-records 15000

# Step 3: Start H100 VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# Step 4: SSH into VM
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Step 5: Run training (on VM)
cd ~/Elson-TB2 && git pull origin main
./scripts/train-curriculum-h100.sh

# Step 6: Stop VM (IMPORTANT!)
exit
gcloud compute instances stop elson-h100-spot --zone=us-central1-a

# Step 7: Deploy for inference
./scripts/deploy-vllm-dora.sh l4 dora
```

---

*Document Version: 1.0.0*
*Last Updated: 2026-01-19*
*Maintained by: Elson TB2 Development Team*
