# Elson TB2 - Implementation Action Plan

**Generated:** 2026-01-18
**Status:** Implementation Complete - Ready for Execution

---

## Executive Summary

This action plan implements the comprehensive analysis for Elson TB2, an AGI/ASI-grade financial platform designed to rival BlackRock Aladdin and Vanguard. The implementation includes:

- **Training Data Consolidation:** 950 Q&A pairs (target: 1,200)
- **URL Categorization:** 830+ URLs categorized (from 11% to 89%)
- **Strategic Q&A Extraction:** 205 pairs from technical documents
- **Deployment Scripts:** L4/Spot/2xT4 with DoRA adapter support
- **Evaluation Framework:** 100-question benchmark with automated scoring

---

## Implementation Completed

### 1. Training Data Pipeline

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/categorize_training_urls.py` | Categorize 830+ uncategorized URLs | `master_training_resources_categorized.csv` |
| `scripts/extract_qa_from_docs.py` | Extract Q&A from strategic docs | `strategic_qa_pairs.json`, `strategic_qa_alpaca.json` |
| `scripts/consolidate_training_data.py` | Merge all training sources | `consolidated_training_data.json/jsonl` |

**Results:**
```
Total Q&A pairs: 950
Training Data Target: 1,200
Gap: 250 pairs needed

By Source:
  training_data_final: 643
  Comprehensive Trading Knowledge: 104
  resource_catalog: 102
  Building AGI_ASI Investment System: 101
```

### 2. H100 Training Pipeline (PRIMARY)

> **The H100 is our primary training infrastructure for both DoRA and QDoRA.**

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

| Script | Purpose | GPU |
|--------|---------|-----|
| `scripts/train-and-quantize-h100.sh` | Complete DoRA + QDoRA pipeline | H100 80GB |

**Training Command (run on H100):**
```bash
# SSH into H100
gcloud compute instances start elson-h100-spot --zone=us-central1-a
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Run full pipeline
cd ~/Elson-TB2 && git pull origin main
./scripts/train-and-quantize-h100.sh

# Stop VM when done
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

**Training Hyperparameters (optimized for H100):**
| Parameter | Value | Notes |
|-----------|-------|-------|
| DoRA Rank (r) | 128 | Increased from 64 |
| Alpha | 256 | 2x rank |
| Batch Size | 16 | H100 can handle larger |
| Epochs | 5 | Better convergence |
| Precision | bfloat16 | H100 native |

### 3. Deployment Infrastructure

> **IMPORTANT:** Only DoRA/QDoRA adapters are production-ready. LoRA is deprecated.

| Script | Purpose | Modes |
|--------|---------|-------|
| `scripts/deploy-vllm-dora.sh` | Deploy vLLM with DoRA/QDoRA adapters | l4, spot, 2xt4, quantized |
| `scripts/deploy-model.sh` | Original deployment script | l4, 2xt4, quantized |
| `scripts/gcp_cleanup.sh` | Cloud Shell disk cleanup | --dry-run supported |

**Deployment Commands (after H100 training):**
```bash
# Deploy QDoRA on L4 (recommended for production)
./scripts/deploy-vllm-dora.sh l4 qdora

# Or Spot VM for cost savings
./scripts/deploy-vllm-dora.sh spot qdora
```

> **Note:** LoRA adapters (lora-v1, lora-v2) are deprecated and will show an error if used.

### 4. Evaluation Framework

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/run_evaluation_benchmark.py` | Run 100-question benchmark | `benchmark_results.json` |

**Usage:**
```bash
# Run benchmark against deployed model
python scripts/run_evaluation_benchmark.py --api-url http://EXTERNAL_IP:8000

# Dry run to test setup
python scripts/run_evaluation_benchmark.py --dry-run
```

---

## Immediate Action Items (This Week)

### Priority 0: Unblock vLLM Deployment

**Step 1: Request L4 GPU Quota**
```
1. Go to: https://console.cloud.google.com/iam-admin/quotas?project=elson-33a95
2. Filter: "NVIDIA_L4_GPUS"
3. Select region: us-central1
4. Request: 1 GPU
5. Justification: "AI model inference for financial services application"
6. Expected approval: 24-48 hours
```

**Step 2: Clean GCP Cloud Shell (if needed)**
```bash
./scripts/gcp_cleanup.sh --dry-run  # Preview
./scripts/gcp_cleanup.sh            # Execute
```

**Step 3: Deploy vLLM**
```bash
# After quota approval
./scripts/deploy-vllm-dora.sh l4 dora

# Or use Spot VM for 65% cost savings
./scripts/deploy-vllm-dora.sh spot qdora
```

### Priority 1: Validate Model Quality

**Run Evaluation Benchmark:**
```bash
# Wait for vLLM to be ready (10-15 min after deployment)
curl http://EXTERNAL_IP:8000/v1/models

# Run full benchmark
python scripts/run_evaluation_benchmark.py \
  --api-url http://EXTERNAL_IP:8000 \
  --output benchmark_results.json
```

**Target Metrics:**
- Overall accuracy: >80%
- Per-category accuracy: >70%
- Average latency: <2000ms

---

## Short-Term Action Items (Next 2 Weeks)

### Phase 2A: Expand Training Data

**Generate 250 more Q&A pairs to reach 1,200 target:**

1. **Additional strategic docs extraction:**
   - BLACKROCK & VANGUARD RIVALRY MASTER PLAN.txt
   - FINANCIAL PROJECTIONS & INVESTOR PRESENTATION.txt
   - ENTERPRISE API ARCHITECTURE.txt

2. **Manual curation from knowledge base:**
   - Review 16 JSON files in `backend/app/knowledge_base/wealth_management/data/`
   - Extract additional Q&A pairs from structured content

3. **Domain expert review:**
   - Have SMEs create edge case Q&A pairs
   - Focus on compliance and regulatory scenarios

### Phase 2B: Extended Training

**Retrain DoRA with 1,200+ pairs:**
```bash
# On H100 GPU
python backend/scripts/train_elson_dora_h100.py \
  --data backend/training_data/consolidated_training_data.json \
  --output wealth-dora-elson14b-v2 \
  --epochs 3

# Upload to GCS
gsutil -m cp -r wealth-dora-elson14b-v2 gs://elson-33a95-elson-models/
```

### Phase 2C: Backend Integration

**Connect vLLM to Cloud Run backend:**

1. Update `backend/app/services/advisor.py` with vLLM endpoint
2. Configure environment variable: `VLLM_API_URL`
3. Redeploy backend to Cloud Run
4. Run integration tests

---

## Medium-Term Action Items (Next Month)

### Phase 3: Production Deployment

1. **Deploy QDoRA model:**
   - Best balance of accuracy and efficiency
   - 4-bit quantization for ~5GB memory usage
   - L4 GPU with vLLM

2. **Set up monitoring:**
   - Latency metrics (P50, P95, P99)
   - Accuracy tracking via periodic benchmark runs
   - Cost monitoring for GPU usage

3. **Implement auto-scaling:**
   - Scale vLLM pods based on request queue
   - Scale-to-zero for cost optimization
   - Consider Cloud Run GPU when available

4. **Begin pilot customer onboarding:**
   - Identify 3-5 beta testers
   - Collect feedback on model responses
   - Iterate on training data

---

## Cost Analysis

| Deployment Option | Hourly Cost | Monthly (Always-On) | Recommended For |
|-------------------|-------------|---------------------|-----------------|
| L4 On-Demand | $0.70 | $504 | Production |
| L4 Spot | $0.25 | $180 | Development/Testing |
| 2x T4 On-Demand | $1.50 | $1,080 | Fallback option |
| T4 Quantized | $0.50 | $360 | Budget production |

**Recommended Strategy:**
- Development: L4 Spot (~$180/month)
- Production: L4 On-Demand with scale-to-zero
- Target: $50-100/month with smart scheduling

---

## File Reference

### New Scripts Created

| File | Description |
|------|-------------|
| `scripts/categorize_training_urls.py` | URL categorization with domain/subdomain |
| `scripts/extract_qa_from_docs.py` | Q&A extraction from strategic documents |
| `scripts/consolidate_training_data.py` | Training data consolidation and analysis |
| `scripts/run_evaluation_benchmark.py` | 100-question benchmark runner |
| `scripts/deploy-vllm-dora.sh` | Enhanced deployment with DoRA support |
| `scripts/gcp_cleanup.sh` | GCP Cloud Shell cleanup utility |

### New Data Files Generated

| File | Description |
|------|-------------|
| `Elson FAN/master_training_resources_categorized.csv` | 929 categorized URLs |
| `backend/training_data/strategic_qa_pairs.json` | 205 Q&A from strategic docs |
| `backend/training_data/strategic_qa_alpaca.json` | Alpaca format for fine-tuning |
| `backend/training_data/consolidated_training_data.json` | 950 consolidated Q&A pairs |
| `backend/training_data/consolidated_training_data.jsonl` | JSONL format for streaming |
| `backend/training_data/training_statistics.json` | Data quality metrics |

---

## Success Criteria

### Training Data
- [x] URL categorization >85% complete (achieved: 89%)
- [x] Q&A pairs >800 (achieved: 950)
- [ ] Q&A pairs >1,200 (need 250 more)
- [ ] Evaluation accuracy >80%

### Deployment
- [ ] L4 GPU quota approved
- [ ] vLLM server deployed and healthy
- [ ] Benchmark run completed
- [ ] Backend integration tested

### Production
- [ ] QDoRA model deployed
- [ ] Monitoring configured
- [ ] Auto-scaling enabled
- [ ] Pilot customers onboarded

---

## Next Steps (Immediate)

1. **Request L4 GPU quota** from GCP Console
2. **Run GCP cleanup** if Cloud Shell disk is full
3. **Deploy vLLM** with DoRA adapter once quota approved
4. **Run evaluation benchmark** to validate model quality
5. **Share benchmark results** and iterate on training data

---

*Generated by Elson TB2 Implementation Pipeline*
*Action Plan Version: 1.1.0*

> **Model Strategy:** Use DoRA (full quality) or QDoRA (cost-efficient) for all deployments. LoRA is deprecated.
