# Elson TB2 - Implementation Action Plan

**Generated:** 2026-01-19
**Status:** Tool-First Architecture Complete - Ready for Deployment

---

## Executive Summary

This action plan implements the comprehensive analysis for Elson TB2, an AGI/ASI-grade financial platform designed to rival BlackRock Aladdin and Vanguard. The implementation includes:

- **Training Data Consolidation:** 40,993 Q&A pairs (exceeded 25,000 target)
- **Tool Integration:** OpenBB, FinanceToolkit, yfinance endpoints
- **Domain Packs:** Insurance (10K), Accounting (5K), Tool-Use (2.5K)
- **Evaluation Framework:** 431-question benchmark across 27 domains
- **Deployment Scripts:** L4/Spot with DoRA adapter support

---

## Implementation Completed

### 1. Training Data Pipeline

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/generate_tool_use_training_data.py` | Generate tool-use examples | `tool_use_training_data.json` (2,500) |
| `scripts/generate_insurance_training_data.py` | Generate insurance examples | `insurance_training_data.json` (10,000) |
| `scripts/generate_accounting_training_data.py` | Generate accounting examples | `accounting_training_data.json` (5,000) |
| `scripts/consolidate_training_data.py` | Merge all training sources | `final_training_data.json` (23,493) |

**Results:**
```
Total Q&A pairs: 40,993
Training Data Target: 25,000 ✅ EXCEEDED

By Source:
  final_training_data.json:      23,493 (57.3%)
  insurance_training_data.json:  10,000 (24.4%)
  accounting_training_data.json:  5,000 (12.2%)
  tool_use_training_data.json:    2,500 (6.1%)
```

### 2. H100 Training Pipeline (PRIMARY) - CURRICULUM METHOD

> **The H100 uses 3-PHASE CURRICULUM TRAINING for optimal model learning.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CURRICULUM TRAINING (3-PHASE)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   PHASE A: Domain Blocks (35% easy, 35% medium, 25% hard, 5% extreme)   │
│   └─→ Train one domain at a time for competence                         │
│                                                                          │
│   PHASE B: Mixed Curriculum (20% easy, 40% medium, 30% hard, 10% ext)   │
│   └─→ Cross-domain generalization, 15% domain cap                       │
│                                                                          │
│   PHASE C: Stress Epoch (10% easy, 25% medium, 35% hard, 30% extreme)   │
│   └─→ High-risk domains: compliance, securities, derivatives            │
│                                                                          │
│   Output: wealth-dora-elson14b-h100-v3 (curriculum trained)             │
│   Total time: ~45-60 min | Cost: ~$2-3                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

| Script | Purpose | GPU |
|--------|---------|-----|
| `scripts/curriculum_sampler.py` | Generate Phase A/B/C manifests | CPU |
| `scripts/domain_bucket_builder.py` | Organize data by domain/difficulty | CPU |
| `scripts/train-curriculum-h100.sh` | Run curriculum training pipeline | H100 80GB |
| `scripts/train-and-quantize-h100.sh` | Legacy flat training | H100 80GB |

**Curriculum Training Command (run on H100):**
```bash
# SSH into H100
gcloud compute instances start elson-h100-spot --zone=us-central1-a
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Pull latest and generate curriculum
cd ~/Elson-TB2 && git pull origin main
python scripts/curriculum_sampler.py --phase all --target-records 15000

# Run curriculum training pipeline
./scripts/train-curriculum-h100.sh

# Stop VM when done
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

**Domain Buckets Structure:**
```
backend/training_data/domain_buckets/
├── accounting/         (easy, medium, hard)
├── estate_planning/    (easy, medium, hard, extremely_complex)
├── federal_income_tax/ (easy, medium, hard)
├── compliance/         (medium, hard)
├── securities_regulation/ (medium, hard)
... (80+ domain buckets total)
```

**Training Hyperparameters (optimized for H100):**
| Parameter | Value | Notes |
|-----------|-------|-------|
| DoRA Rank (r) | 128 | Increased from 64 |
| Alpha | 256 | 2x rank |
| Batch Size | 16 | H100 can handle larger |
| Epochs | 5 | Better convergence |
| Precision | bfloat16 | H100 native |
| **Method** | **Curriculum (3-Phase)** | Phase A → B → C |

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
| `scripts/run_model_evaluation.py` | Run model comparison benchmark | `eval_results.json` |
| `scripts/domain_quiz_generator.py` | Generate domain-specific quizzes | `evaluation_quizzes/*.json` |
| `scripts/build_evaluation_benchmark.py` | Build full 431-question benchmark | `quiz_summary.json` |

**Usage:**
```bash
# Run model comparison benchmark
python scripts/run_model_evaluation.py --model wealth-dora-elson14b-h100-v2

# Generate domain quizzes
python scripts/domain_quiz_generator.py

# Build evaluation benchmark
python scripts/build_evaluation_benchmark.py
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

### Phase 2A: Deploy with Full Training Data ✅ COMPLETE

Training data expanded to 40,993 pairs:
- Tool-use training: 2,500 examples ✅
- Insurance workflows: 10,000 examples ✅
- Accounting integration: 5,000 examples ✅
- Base training data: 23,493 examples ✅

### Phase 2B: Retrain with Expanded Data

**Retrain DoRA with 40,993 pairs:**
```bash
# On H100 GPU
gcloud compute instances start elson-h100-spot --zone=us-central1-a
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Run training with full dataset
cd ~/Elson-TB2 && git pull origin main
./scripts/train-and-quantize-h100.sh

# Stop VM when done
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

### Phase 2C: Backend Integration

**Connect vLLM to Cloud Run backend:**

1. Update `backend/app/services/advisor.py` with vLLM endpoint
2. Configure environment variable: `VLLM_API_URL`
3. Redeploy backend to Cloud Run
4. Run integration tests with tool endpoints

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
| `scripts/generate_tool_use_training_data.py` | Generate 2,500 tool-use examples |
| `scripts/generate_insurance_training_data.py` | Generate 10,000 insurance examples |
| `scripts/generate_accounting_training_data.py` | Generate 5,000 accounting examples |
| `scripts/run_model_evaluation.py` | Model comparison benchmark runner |
| `scripts/domain_quiz_generator.py` | Generate domain-specific quizzes |
| `scripts/build_evaluation_benchmark.py` | Build 431-question benchmark |
| `scripts/curriculum_sampler.py` | Curriculum training infrastructure |
| `scripts/deploy-vllm-dora.sh` | Enhanced deployment with DoRA support |

### New Data Files Generated

| File | Description |
|------|-------------|
| `backend/training_data/final_training_data.json` | 23,493 Q&A pairs |
| `backend/training_data/insurance_training_data.json` | 10,000 insurance pairs |
| `backend/training_data/accounting_training_data.json` | 5,000 accounting pairs |
| `backend/training_data/tool_use_training_data.json` | 2,500 tool-use pairs |
| `backend/training_data/strategic_qa_sft.json` | SFT format (renamed from alpaca) |
| `backend/training_data/evaluation_quizzes/` | 27 domain-specific quiz files |

---

## Success Criteria

### Training Data
- [x] URL categorization >85% complete (achieved: 89%)
- [x] Q&A pairs >25,000 (achieved: 40,993) ✅ EXCEEDED
- [x] Tool-use training data (achieved: 2,500) ✅
- [x] Insurance workflow pack (achieved: 10,000) ✅
- [x] Accounting integration (achieved: 5,000) ✅
- [ ] Evaluation accuracy >80%

### Tool Integration
- [x] OpenBB endpoints implemented ✅
- [x] FinanceToolkit endpoints implemented ✅
- [x] yfinance endpoints implemented ✅
- [x] 7 structured output schemas defined ✅

### Deployment
- [ ] vLLM server deployed and healthy
- [ ] 431-question benchmark run completed
- [ ] Backend integration tested
- [ ] Tool-use accuracy validated

### Production
- [ ] QDoRA model deployed with full 40,993 pairs
- [ ] Monitoring configured
- [ ] Auto-scaling enabled
- [ ] Pilot customers onboarded

---

## Next Steps (Immediate)

1. **Deploy vLLM** with DoRA adapter on L4 GPU
2. **Run 431-question evaluation benchmark** across all domains
3. **Test tool-use accuracy** with OpenBB/FinanceToolkit endpoints
4. **Retrain with full 40,993 pairs** if needed
5. **Production deployment** after benchmark validation

---

*Generated by Elson TB2 Implementation Pipeline*
*Action Plan Version: 2.0.0 - Tool-First Architecture*

> **Model Strategy:** Use DoRA (full quality) or QDoRA (cost-efficient) for all deployments. LoRA is deprecated.
