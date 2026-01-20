# Elson TB2 Training Plan

**Last Updated:** 2026-01-19
**Status:** Training Complete - Tool-First Architecture Deployed

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| Training Data | **40,993 Q&A pairs** | Consolidated from 7 sources |
| Tool Integration | **Complete** | OpenBB, FinanceToolkit, yfinance endpoints |
| Evaluation Benchmark | **431 questions** | Domain-specific quizzes across all categories |
| DoRA Training | **Complete** | Final loss: 0.4063, 25 min runtime |
| Model Upload | **Complete** | 4.2 GB uploaded to GCS |
| H100 VM | **Stopped** | Cost savings |
| vLLM Deployment | **Ready** | Next step |

---

## Training Results (2026-01-18)

| Metric | Value |
|--------|-------|
| **Final Loss** | 0.4063 (down from 1.653) |
| **Runtime** | 24 min 59 sec |
| **Training Pairs** | 40,993 |
| **Method** | QDoRA (4-bit base + DoRA) |
| **Epochs** | 5 |
| **Model Size** | 4.2 GB |
| **GCS Location** | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` |

---

## Dataset Corpus: Source of Truth

> **The full Phase 2 training corpus is exactly 40,993 Q&A pairs.**

| Dataset File | Records | Purpose |
|--------------|---------|---------|
| `final_training_data.json` | 23,493 | Core financial planning backbone |
| `insurance_training_data.json` | 10,000 | Insurance domain competence |
| `accounting_training_data.json` | 5,000 | Accounting/GAAP/IFRS workflows |
| `tool_use_training_data.json` | 2,500 | Structured outputs and tool calling |
| **TOTAL** | **40,993** | **Full training corpus** |

### Why Curriculum Runs Use Subsets

Curriculum training sessions intentionally train on a **subset** of the full corpus per cycle (typically 15,000-20,000 examples) to stage learning by difficulty and domain. This is not a bug - it's the design.

- **Full corpus training** (40,993): Used for final production runs
- **Curriculum cycles** (15-20K): Used for iterative development and domain balancing

### Why Not One Giant File?

The corpus is split into four schema-compatible files to allow:
1. **Domain-weighted sampling** - Prevent general_finance from dominating
2. **Targeted competence building** - Train specific weaknesses
3. **Flexible curriculum design** - Mix and match for different training goals

---

## Training Data Summary

**Total: 40,993 Q&A pairs**

### By Source

| Source | Records | Percentage |
|--------|---------|------------|
| final_training_data.json | 23,493 | 57.3% |
| insurance_training_data.json | 10,000 | 24.4% |
| accounting_training_data.json | 5,000 | 12.2% |
| tool_use_training_data.json | 2,500 | 6.1% |

### By Category (Top 10)

| Category | Records |
|----------|---------|
| financial_planning | 15,100 |
| insurance | 10,000 |
| accounting | 5,000 |
| tool_use | 2,500 |
| retirement_planning | 1,499 |
| estate_planning | 403 |
| securities_regulation | 388 |
| federal_income_tax | 381 |
| portfolio_construction | 369 |
| fintech | 319 |

### Data Quality

| Metric | Value |
|--------|-------|
| Average instruction length | 87.7 chars |
| Average output length | 343.2 chars |
| Unique pairs | 100% (0 duplicates) |
| Validation checks passed | 4/5 |

---

## H100 Training Pipeline - CURRICULUM METHOD

> **The H100 uses 3-PHASE CURRICULUM TRAINING for optimal model learning.**

### Curriculum Training Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CURRICULUM TRAINING (3-PHASE)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   PHASE A: Domain Blocks                                                 │
│   ━━━━━━━━━━━━━━━━━━━━━━                                                │
│   • Train one domain at a time until competence                         │
│   • Tier mix: 35% easy, 35% medium, 25% hard, 5% extreme               │
│   • Output: Domain-specific competence                                   │
│                                                                          │
│   PHASE B: Mixed Curriculum                                              │
│   ━━━━━━━━━━━━━━━━━━━━━━━━                                              │
│   • Shuffle domains for cross-domain generalization                      │
│   • Tier mix: 20% easy, 40% medium, 30% hard, 10% extreme              │
│   • Domain cap: Max 15% per domain                                       │
│   • Output: Cross-domain reasoning ability                               │
│                                                                          │
│   PHASE C: Stress Epoch                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━                                                 │
│   • Heavy on complex scenarios and high-risk domains                     │
│   • Tier mix: 10% easy, 25% medium, 35% hard, 30% extreme              │
│   • Focus: compliance, securities_regulation, derivatives, estate       │
│   • Output: Robust handling of edge cases                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Domain Buckets Structure

```
backend/training_data/domain_buckets/
├── accounting/
│   ├── easy.jsonl
│   ├── medium.jsonl
│   └── hard.jsonl
├── estate_planning/
│   ├── easy.jsonl
│   ├── medium.jsonl
│   ├── hard.jsonl
│   └── extremely_complex.jsonl
├── federal_income_tax/
│   ├── medium.jsonl
│   └── hard.jsonl
├── compliance/
│   ├── medium.jsonl
│   └── hard.jsonl
├── securities_regulation/
│   ├── medium.jsonl
│   └── hard.jsonl
... (80+ domain buckets total)
```

### Training Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| DoRA Rank (r) | 128 | Increased from 64 |
| Alpha | 256 | 2x rank |
| Batch Size | 16 | H100 can handle larger |
| Gradient Accumulation | 4 | Effective batch: 64 |
| Epochs | 5 | Better convergence |
| Max Length | 2048 | Context length |
| Learning Rate | 2e-4 | Standard |
| Precision | bfloat16 | H100 native |
| **Training Method** | **Curriculum (3-Phase)** | Phase A → B → C |

### Curriculum Scripts

| Script | Purpose |
|--------|---------|
| `scripts/curriculum_sampler.py` | Generate Phase A/B/C training manifests |
| `scripts/domain_bucket_builder.py` | Organize data by domain and difficulty |
| `scripts/train-curriculum-h100.sh` | Run full curriculum training pipeline |
| `scripts/train-and-quantize-h100.sh` | Legacy flat training (still works) |

### Training Commands

```bash
# Start H100 VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# SSH into H100
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Pull latest code
cd ~/Elson-TB2 && git pull origin main

# Generate curriculum manifests (Phase A, B, C)
python scripts/curriculum_sampler.py --phase all --target-records 15000

# Run curriculum training pipeline
./scripts/train-curriculum-h100.sh

# OR for legacy flat training:
# ./scripts/train-and-quantize-h100.sh

# Stop VM when done (saves money!)
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

### Curriculum Run Outputs

```
backend/training_data/curriculum_runs/
├── manifest_phaseA_YYYYMMDD_HHMMSS.jsonl   # Phase A manifest
├── manifest_phaseB_YYYYMMDD_HHMMSS.jsonl   # Phase B manifest
├── manifest_phaseC_YYYYMMDD_HHMMSS.jsonl   # Phase C manifest
├── merged_phaseA_YYYYMMDD_HHMMSS.jsonl     # Phase A training data
├── merged_phaseB_YYYYMMDD_HHMMSS.jsonl     # Phase B training data
└── merged_phaseC_YYYYMMDD_HHMMSS.jsonl     # Phase C training data
```

---

## Model Strategy

### Production Models

| Model | GCS Path | Status | Use Case |
|-------|----------|--------|----------|
| **Base Model (14B)** | `elson-finance-trading-14b-final/` | Ready | Foundation |
| **DoRA v2** | `wealth-dora-elson14b-h100-v2/` | **Ready** | Full quality (4.2 GB) |
| **QDoRA** | `elson-finance-trading-wealth-14b-q4-v2/` | Pending | Efficient inference |

### Deprecated (Do Not Use)

| Model | Reason |
|-------|--------|
| wealth-lora-elson14b-vm1 | LoRA deprecated |
| wealth-lora-elson14b-vm2 | LoRA deprecated |

---

## Deployment Plan

### After Training Completes

1. **Deploy QDoRA on L4 (recommended)**
   ```bash
   ./scripts/deploy-vllm-dora.sh l4 qdora
   ```

2. **Or Spot VM for cost savings**
   ```bash
   ./scripts/deploy-vllm-dora.sh spot qdora
   ```

### Cost Analysis

| Deployment | Hourly Cost | Monthly (Always-On) |
|------------|-------------|---------------------|
| L4 On-Demand | $0.70 | $504 |
| L4 Spot | $0.25 | $180 |
| H100 Spot (training only) | $2.50 | N/A |

---

## Evaluation Framework

### Benchmark

- **Directory:** `backend/training_data/evaluation_quizzes/`
- **Size:** 431 questions across 27 domain-specific quizzes
- **Categories:** All major financial domains including tool-use

### Quiz Files

| Quiz | Questions |
|------|-----------|
| Federal Income Tax | 50+ |
| Retirement Planning | 50+ |
| Investment Basics | 40+ |
| Estate & Gift Tax | 35+ |
| Insurance | 35+ |
| Tool Use | 25+ |
| + 21 more domain quizzes | 196+ |

### Running Evaluation

```bash
# Run model comparison benchmark
python scripts/run_model_evaluation.py --model wealth-dora-elson14b-h100-v2

# Generate domain-specific quizzes
python scripts/domain_quiz_generator.py

# Build full evaluation benchmark
python scripts/build_evaluation_benchmark.py
```

### Target Metrics

| Metric | Target |
|--------|--------|
| Overall accuracy | >80% |
| Per-category accuracy | >70% |
| Tool-use accuracy | >95% |
| Average latency | <2000ms |

---

## Scripts Reference

### Curriculum Training Scripts (NEW)

| Script | Purpose |
|--------|---------|
| `scripts/curriculum_sampler.py` | Generate Phase A/B/C training manifests |
| `scripts/domain_bucket_builder.py` | Organize data by domain and difficulty tier |
| `scripts/train-curriculum-h100.sh` | Run full curriculum training on H100 |

### Training & Deployment Scripts

| Script | Purpose |
|--------|---------|
| `scripts/train-and-quantize-h100.sh` | H100 DoRA + QDoRA pipeline (legacy flat) |
| `scripts/deploy-vllm-dora.sh` | vLLM deployment with adapters |
| `scripts/run_model_evaluation.py` | Model comparison benchmark runner |
| `scripts/domain_quiz_generator.py` | Generate domain-specific quizzes |
| `scripts/build_evaluation_benchmark.py` | Build 431-question benchmark |

### Training Data Generation Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate_tool_use_training_data.py` | Generate 2,500 tool-use examples |
| `scripts/generate_insurance_training_data.py` | Generate 10,000 insurance examples |
| `scripts/generate_accounting_training_data.py` | Generate 5,000 accounting examples |
| `scripts/consolidate_training_data.py` | Training data consolidation |
| `scripts/augment_training_data.py` | Paraphrasing, difficulty scaling |
| `scripts/generate_synthetic_qa.py` | Synthetic Q&A generation |
| `scripts/domain_classifier.py` | Classify Q&A into 62 domains |
| `scripts/merge_all_training_data.py` | Merge all training sources |
| `scripts/validate_training_data.py` | Quality validation pipeline |

---

## Training Data Files

| File | Description |
|------|-------------|
| `backend/training_data/final_training_data.json` | 23,493 Q&A pairs |
| `backend/training_data/final_training_data_sft.json` | SFT format (renamed from alpaca) |
| `backend/training_data/insurance_training_data.json` | 10,000 insurance pairs |
| `backend/training_data/accounting_training_data.json` | 5,000 accounting pairs |
| `backend/training_data/tool_use_training_data.json` | 2,500 tool-use pairs |
| `backend/training_data/strategic_qa_sft.json` | Strategic Q&A in SFT format |
| `backend/training_data/evaluation_quizzes/` | 27 domain-specific quiz files |

---

## Tool Integration (NEW)

### Implemented Endpoints

| Endpoint | Tool | Purpose |
|----------|------|---------|
| `/tools/openbb/*` | OpenBB | Market data, quotes, fundamentals |
| `/tools/financetoolkit/*` | FinanceToolkit | 150+ financial ratios |
| `/tools/yfinance/*` | yfinance | Free market data alternative |

### Tool-Use Training

The model is trained to call tools for:
- Current pricing and market data
- Fundamentals and financial statements
- Portfolio analytics and ratios
- Any computation requiring auditability

---

## Next Steps

### Immediate

1. Deploy vLLM on L4 GPU with DoRA adapter
2. Run 431-question evaluation benchmark
3. Test tool-use accuracy

### Short-Term

1. Retrain with full 40,993 pairs
2. Evaluate benchmark results across all domains
3. Production deployment

### Status

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Q&A pairs | 40,993 | 25,000 | ✅ Exceeded |
| Evaluation questions | 431 | 500 | 86% |
| Tool endpoints | 15+ | 10 | ✅ Complete |
| Benchmark accuracy | TBD | >80% | Pending |

---

## GCS Bucket Structure

```
gs://elson-33a95-elson-models/
├── elson-finance-trading-14b-final/     # 27.52GB base model
├── wealth-dora-elson14b-h100-v2/        # DoRA v2 adapter (4.2 GB) ✅ READY
├── elson-finance-trading-wealth-14b-q4-v2/  # QDoRA v2 (pending)
├── wealth-dora-elson14b-h100/           # Previous DoRA v1
└── elson-finance-trading-wealth-14b-q4/ # Previous QDoRA v1
```

---

*Generated: 2026-01-19*
*Version: 3.0.0 - Tool-First Architecture*
