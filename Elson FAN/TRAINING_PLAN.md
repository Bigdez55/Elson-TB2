# Elson TB2 Training Plan

**Last Updated:** 2026-01-18
**Status:** Training In Progress on H100

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| Training Data | **950 Q&A pairs** | Consolidated from 4 sources |
| URL Categorization | **89% complete** | 830+ URLs categorized across 18 domains |
| DoRA Training | **In Progress** | H100 GPU, 43% complete |
| LoRA | **Deprecated** | Do not use |
| vLLM Deployment | Pending | Awaiting training completion |

---

## Training Data Summary

**Total: 950 Q&A pairs** (Target: 1,200)

### By Source

| Source | Records | Percentage |
|--------|---------|------------|
| training_data_final | 643 | 68% |
| Comprehensive Trading Knowledge | 104 | 11% |
| resource_catalog | 102 | 11% |
| Building AGI_ASI Investment System | 101 | 10% |

### By Category (Top 10)

| Category | Records |
|----------|---------|
| retirement_planning | 269 |
| goal_planning | 76 |
| general_finance | 73 |
| professional_roles | 55 |
| college_planning | 53 |
| tax | 37 |
| high_frequency_trading | 30 |
| estate_planning | 26 |
| algorithmic_trading | 25 |
| quantitative_finance | 24 |

### Data Quality

| Metric | Value |
|--------|-------|
| Average output length | 614 chars |
| Empty outputs | 0 |
| Short outputs | 0 |
| Long outputs | 0 |

---

## H100 Training Pipeline

> **The H100 is our primary training infrastructure for DoRA and QDoRA.**

```
┌─────────────────────────────────────────────────────────┐
│                 H100 SESSION (~$2.50/hr)                │
├─────────────────────────────────────────────────────────┤
│  1. Train DoRA (950 pairs, r=128, α=256)                │
│     └─→ wealth-dora-elson14b-h100-v2                    │
│                                                         │
│  2. Quantize to QDoRA (4-bit AWQ)                       │
│     └─→ elson-finance-trading-wealth-14b-q4-v2          │
│                                                         │
│  3. Upload both to GCS                                  │
│                                                         │
│  Total time: ~15-20 min | Cost: ~$1-2                   │
└─────────────────────────────────────────────────────────┘
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

### Training Commands

```bash
# Start H100 VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# SSH into H100
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Run full pipeline
cd ~/Elson-TB2 && git pull origin main
./scripts/train-and-quantize-h100.sh

# Stop VM when done (saves money!)
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

---

## Model Strategy

### Production Models

| Model | GCS Path | Status | Use Case |
|-------|----------|--------|----------|
| **Base Model (14B)** | `elson-finance-trading-14b-final/` | Ready | Foundation |
| **DoRA** | `wealth-dora-elson14b-h100-v2/` | Training | Full quality |
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

- **File:** `backend/training_data/evaluation_benchmark.json`
- **Size:** 100 test cases
- **Categories:** All major financial domains

### Running Evaluation

```bash
# Run benchmark against deployed model
python scripts/run_evaluation_benchmark.py --api-url http://EXTERNAL_IP:8000

# Dry run
python scripts/run_evaluation_benchmark.py --dry-run
```

### Target Metrics

| Metric | Target |
|--------|--------|
| Overall accuracy | >80% |
| Per-category accuracy | >70% |
| Average latency | <2000ms |

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/train-and-quantize-h100.sh` | H100 DoRA + QDoRA pipeline |
| `scripts/deploy-vllm-dora.sh` | vLLM deployment with adapters |
| `scripts/run_evaluation_benchmark.py` | 100-question benchmark |
| `scripts/categorize_training_urls.py` | URL categorization |
| `scripts/extract_qa_from_docs.py` | Q&A extraction from docs |
| `scripts/consolidate_training_data.py` | Training data consolidation |

---

## Training Data Files

| File | Description |
|------|-------------|
| `backend/training_data/consolidated_training_data.json` | 950 Q&A pairs |
| `backend/training_data/consolidated_training_data.jsonl` | JSONL format |
| `backend/training_data/training_statistics.json` | Data quality metrics |
| `backend/training_data/strategic_qa_pairs.json` | 205 extracted pairs |
| `backend/training_data/evaluation_benchmark.json` | 100 test cases |

---

## Next Steps

### Immediate (After Training)

1. Verify DoRA model uploaded to GCS
2. Run QDoRA quantization
3. Deploy to vLLM on L4 GPU
4. Run 100-question benchmark

### Short-Term (Next Week)

1. Evaluate benchmark results
2. Expand training data to 1,200+ pairs
3. Retrain if needed
4. Production deployment

### Gap Analysis

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Q&A pairs | 950 | 1,200 | +250 |
| Benchmark accuracy | TBD | >80% | - |
| Inference latency | TBD | <2000ms | - |

---

## GCS Bucket Structure

```
gs://elson-33a95-elson-models/
├── elson-finance-trading-14b-final/     # 27.52GB base model
├── wealth-dora-elson14b-h100-v2/        # DoRA adapter (pending)
├── elson-finance-trading-wealth-14b-q4-v2/  # QDoRA (pending)
├── wealth-dora-elson14b-h100/           # Previous DoRA v1
└── elson-finance-trading-wealth-14b-q4/ # Previous QDoRA v1
```

---

*Generated: 2026-01-18*
*Version: 2.0.0*
