# Elson Financial AI - GCP Agent Setup Guide

**Last Updated:** 2026-01-18
**Status:** ✅ TRAINING COMPLETE - DoRA v2 Ready for Deployment

---

## ⚠️ CRITICAL RULE - CHECK EXISTING VMs FIRST

> **ALWAYS run `gcloud compute instances list` BEFORE creating any new VM.**

```bash
# Run this FIRST before any VM operations:
gcloud compute instances list

# Only create a new VM if the one you need doesn't exist
```

This prevents duplicate VMs and wasted resources.

---

## ✅ TRAINING COMPLETE (2026-01-18)

| Metric | Value |
|--------|-------|
| **Final Loss** | 0.4063 (down from 1.653) |
| **Runtime** | 24 min 59 sec |
| **Training Pairs** | 950 |
| **Method** | QDoRA (4-bit base + DoRA) |
| **Epochs** | 5 |
| **Model Size** | 4.2 GB |
| **GCS Location** | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` |
| **H100 VM** | STOPPED (cost savings) |

**Next Step - Deploy to vLLM:**
```bash
./scripts/deploy-vllm-dora.sh l4 dora
```

---

## GCP AGENT - SOLE PURPOSE

> **This agent exists ONLY to train/enhance the model and manage GCP resources.**

### What GCP Agent DOES:
| Task | Examples |
|------|----------|
| **Train the Model** | DoRA/QDoRA fine-tuning, run training jobs, evaluate quality |
| **Manage GPU VMs** | Start/stop H100/L4 VMs, SSH into VMs, monitor GPU usage |
| **Manage GCS** | Upload/download models, check bucket contents |
| **Request Quotas** | GPU quota requests, resource allocation |
| **Run Inference** | Test model responses, run benchmarks |
| **Monitor Costs** | Track VM costs, optimize resource usage |

### What GCP Agent does NOT do:
- Write or edit code (GitHub Agent only)
- Create new scripts (GitHub Agent only)
- Update documentation (GitHub Agent only)
- Push to GitHub (GitHub Agent only)
- Frontend/backend development (GitHub Agent only)

### Model Information
| Attribute | Value |
|-----------|-------|
| **Name** | Elson-Finance-Trading-14B |
| **Size** | 27.52 GB (14B parameters) |
| **Location** | `gs://elson-33a95-elson-models/` |
| **Production Adapter** | DoRA (`wealth-dora-elson14b-h100`) |

---

This document tracks everything needed to restore the GCP environment after ephemeral session ends.

---

## 0. Model Specification (READ FIRST)

### Elson-Finance-Trading-14B (Base Model)

| Attribute | Value |
|-----------|-------|
| **Parameters** | 14 billion |
| **Size** | 27.52 GB (6 SafeTensors shards) |
| **Base Models** | DeepSeek-R1-Distill-Qwen-14B + Qwen2.5-14B-Instruct |
| **Merge Method** | SLERP + DARE-TIES pruning |
| **GCS Location** | `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/` |

### Production Adapters

| Adapter | GCS Path | Purpose | Status |
|---------|----------|---------|--------|
| **DoRA** | `wealth-dora-elson14b-h100` | Full quality training (loss: 0.14) | ✅ PRODUCTION |
| **QDoRA** | `elson-finance-trading-wealth-14b-q4` | Quantized for efficient inference | ✅ PRODUCTION |
| ~~LoRA~~ | `wealth-lora-elson14b-vm1/vm2` | Deprecated - do not use | ⚠️ ARCHIVED |

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INFERENCE PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Base Model (27.52GB)  +  DoRA Adapter (~96MB)             │
│            │                       │                         │
│            └───────────┬───────────┘                         │
│                        ▼                                     │
│              ┌──────────────────┐                            │
│              │   vLLM Server    │  ← High-performance LLM    │
│              │   (on L4 GPU)    │     inference engine       │
│              └────────┬─────────┘                            │
│                       ▼                                      │
│              REST API endpoint                               │
│              http://IP:8000/v1/completions                   │
│                       ▼                                      │
│              ┌──────────────────┐                            │
│              │  FastAPI Backend │                            │
│              └────────┬─────────┘                            │
│                       ▼                                      │
│              ┌──────────────────┐                            │
│              │    Frontend      │                            │
│              └──────────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Quick Deploy Command

```bash
# Deploy QDoRA model on L4 GPU (recommended)
./scripts/deploy-vllm-dora.sh l4 qdora

# Or for cost savings (Spot instance)
./scripts/deploy-vllm-dora.sh spot qdora
```

---

## H100 Training Pipeline (PRIMARY)

> **The H100 handles both DoRA training AND QDoRA quantization in a single session.**

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
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              L4 DEPLOYMENT (~$0.70/hr)                  │
│  Deploy QDoRA for production inference                  │
└─────────────────────────────────────────────────────────┘
```

### H100 Training Command

```bash
# 1. Start H100 VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# 2. Pull latest and run training pipeline
cd ~/Elson-TB2 && git pull origin main
./scripts/train-and-quantize-h100.sh

# 3. Stop VM when done (IMPORTANT - saves money!)
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

### Training Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| DoRA Rank (r) | 128 | Increased from 64 |
| Alpha | 256 | 2x rank |
| Batch Size | 16 | H100 can handle larger |
| Epochs | 5 | Better convergence |
| Precision | bfloat16 | H100 native |
| Training Data | 950 pairs | Consolidated dataset |

---

## 1. Environment Setup (Run First)

```bash
# Clone repository
git clone https://github.com/Bigdez55/Elson-TB2.git
cd Elson-TB2/backend

# Create Python virtual environment
python3 -m venv venv && source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Install ML/training dependencies
pip install transformers peft bitsandbytes accelerate
pip install sentence-transformers chromadb
```

---

## 2. Knowledge Base Ingestion (Required)

The ChromaDB vector database needs to be rebuilt on each new session:

```bash
cd backend
python scripts/ingest_knowledge.py
```

**Expected Output:**
- 17 knowledge base files found
- 1618 total documents indexed
- 5/5 retrieval quality tests pass

**Knowledge Base Files (17 total):**
- family_office_structure.json (76 chunks)
- professional_roles.json (129 chunks)
- certifications.json (94 chunks)
- study_materials.json (74 chunks)
- estate_planning.json (73 chunks)
- trust_administration.json (104 chunks)
- financial_advisors.json (71 chunks)
- governance.json (67 chunks)
- succession_planning.json (83 chunks)
- generational_wealth.json (101 chunks)
- credit_financing.json (93 chunks)
- treasury_banking.json (75 chunks)
- compliance_operations.json (89 chunks)
- financial_literacy_basics.json (135 chunks)
- **retirement_planning.json (122 chunks)** ← NEW
- **college_planning.json (105 chunks)** ← NEW
- **goal_tier_progression.json (127 chunks)** ← NEW

---

## 3. Verify API Endpoints

```bash
cd backend

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test endpoints:
curl -X POST http://localhost:8000/api/v1/wealth/advisory/retirement-planning \
  -H "Content-Type: application/json" \
  -d '{
    "current_age": 35,
    "target_retirement_age": 65,
    "annual_income": 100000,
    "current_retirement_savings": 150000,
    "employer_401k_match": 0.04,
    "risk_tolerance": "moderate"
  }'
```

---

## 4. DVoRA/QDoRA Model Training (PENDING)

### 4.1 Training Data Generation

Need to generate 2000+ Q&A pairs covering:
- [ ] Retirement planning scenarios (401k, IRA, Roth, FIRE)
- [ ] College planning scenarios (529, Coverdell, FAFSA)
- [ ] Goal-based tier progression scenarios
- [ ] All 70+ professional roles
- [ ] 5 wealth tiers (Foundation → HNW/UHNW)

**Script location:** `backend/scripts/generate_training_data.py` (TO CREATE)

### 4.2 GCS Bucket Location

```bash
# Check existing model artifacts
gsutil ls gs://elson-financial-ai/

# Expected structure:
# gs://elson-financial-ai/
#   ├── dvora_base_model/
#   ├── training_data/
#   └── fine_tuned_model/
```

### 4.3 GCP Quota Status (as of 2026-01-15)

**Available Resources:**

| Resource | Region | Quota |
|----------|--------|-------|
| Cloud Build CPUs | us-west1 | 12 |
| GPUs (on-demand) | all regions | 4 ✓ |

**Note:** Committed T4/A100 GPU requests were denied. Use L4 GPUs instead.

### 4.4 L4 GPU VM Options (Recommended)

| Script | Config | Cost/hr |
|--------|--------|---------|
| `create-l4-gpu-vm.sh` | 2x L4 (48GB VRAM) | ~$2.40 |
| `create-l4-gpu-vm-spot.sh` | 2x L4 Spot | ~$0.80 |
| `create-l4-single-gpu-vm.sh` | 1x L4 (24GB VRAM) | ~$0.70 |

**L4 vs A100 Comparison:**

| Spec | L4 (24GB) | A100 (40GB) |
|------|-----------|-------------|
| VRAM | 24GB | 40GB |
| Architecture | Ada Lovelace | Ampere |
| FP16 TFLOPS | ~242 | ~312 |
| Cost (2x) | ~$2.40/hr | ~$7.35/hr |

### 4.5 Create VM via Console UI (if gcloud crashes)

If Cloud Shell gcloud has issues (`TypeError: string indices must be integers`), create VM manually:

1. Go to: https://console.cloud.google.com/compute/instancesAdd?project=elson-33a95

2. Configure:
   - **Name:** `elson-dvora-training-l4`
   - **Region:** us-central1 → Zone: us-central1-a
   - **Machine type:** g2-standard-24 (2x L4 GPUs)
   - **Boot disk:** Change → Deep Learning on Linux → PyTorch 2.7
   - **Boot disk size:** 200GB SSD

3. Click "Create"

### 4.6 Fine-tuning Command

```bash
# Authenticate
gcloud auth login
gcloud config set project Elson

# Run fine-tuning using available GPU quota (us-west1)
python scripts/finetune_dvora.py \
  --base_model gs://elson-financial-ai/dvora_base_model \
  --training_data gs://elson-financial-ai/training_data \
  --output_dir gs://elson-financial-ai/fine_tuned_model \
  --region us-west1 \
  --epochs 3 \
  --batch_size 8
```

**Alternative: Use Vertex AI Training (recommended)**
```bash
gcloud ai custom-jobs create \
  --region=us-west1 \
  --display-name=elson-dvora-finetune \
  --worker-pool-spec=machine-type=n1-standard-8,accelerator-type=NVIDIA_TESLA_T4,accelerator-count=1 \
  --python-package-uris=gs://elson-financial-ai/training_package.tar.gz \
  --module-name=trainer.task
```

---

## 5. Deployment Checklist

### Backend API
- [x] FastAPI application structure
- [x] 13 advisory modes in RAG service
- [x] Compliance rules engine (17 rules)
- [x] All wealth advisory endpoints
- [x] Retirement planning endpoint
- [x] College planning endpoint
- [x] Goal planning endpoint

### Frontend
- [x] RTK Query API integration
- [x] WealthAdvisoryDashboard component
- [x] GoalPlanner component
- [x] RetirementCalculator component
- [x] CollegeSavingsPlanner component

### GCP Infrastructure
- [ ] Cloud Run deployment
- [ ] Vertex AI model endpoint
- [ ] Cloud SQL (if needed)
- [ ] Secret Manager for API keys
- [ ] Cloud CDN for frontend

---

## 6. API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/wealth/advisory/query` | POST | General wealth advisory |
| `/wealth/advisory/estate-planning` | POST | Estate planning guidance |
| `/wealth/advisory/succession-planning` | POST | Business succession |
| `/wealth/advisory/retirement-planning` | POST | **NEW** Retirement planning |
| `/wealth/advisory/college-planning` | POST | **NEW** College/529 planning |
| `/wealth/goals/create-plan` | POST | **NEW** Tier progression roadmap |
| `/wealth/team/coordinate` | POST | Professional team assembly |
| `/wealth/knowledge/stats` | GET | RAG statistics |

---

## 7. Service Tiers (Democratized Model)

Based on US average salary ($66,622/year):

| Tier | Asset Range | Access Level |
|------|-------------|--------------|
| Foundation | $0 - $10K | Full CFP access, financial literacy |
| Builder | $10K - $75K | ~1 year savings, achievable for most |
| Growth | $75K - $500K | CFA access for middle-class |
| Affluent | $500K - $5M | Full professional team |
| HNW/UHNW | $5M+ | Family office, specialists |

---

## 8. Quick Verification Tests

```bash
cd backend

# Test 1: RAG retrieval
python -c "
from app.services.knowledge_rag import WealthManagementRAG, AdvisoryMode
import asyncio

async def test():
    rag = WealthManagementRAG()
    results = await rag.query('401k vs Roth IRA', n_results=3, advisory_mode=AdvisoryMode.RETIREMENT_PLANNING)
    print(f'Results: {len(results)} documents')
    print(f'Category: {results[0].get(\"category\", \"N/A\")}')

asyncio.run(test())
"

# Test 2: Helper functions
python -c "
from app.api.api_v1.endpoints.wealth_advisory import _calculate_retirement_projections
from app.schemas.wealth_advisory import RetirementPlanningRequest

req = RetirementPlanningRequest(
    current_age=35, target_retirement_age=65, annual_income=100000,
    current_retirement_savings=150000, employer_401k_match=0.04, risk_tolerance='moderate'
)
calcs = _calculate_retirement_projections(req)
print(f'Target: \${calcs[\"target_savings\"]:,.0f}')
print(f'Projected: \${calcs[\"projected_savings\"]:,.0f}')
"
```

---

## 9. Files Modified/Created

### Session 2026-01-17 (Training Data Improvements)

| File | Changes |
|------|---------|
| `backend/scripts/generate_training_data_v2.py` | NEW - Enhanced generator with multi-turn, negative examples |
| `backend/scripts/generate_training_data_v3.py` | NEW - Comprehensive generator with 17 categories |
| `backend/scripts/expand_training_data.py` | NEW - Combines and balances all data |
| `backend/training_data/training_data_final.json` | NEW - 643 balanced Q&A pairs |
| `backend/training_data/evaluation_benchmark.json` | NEW - 100 test cases for model evaluation |

### Previous Session (API + Knowledge Base)

| File | Changes |
|------|---------|
| `backend/app/schemas/wealth_advisory.py` | Added response models for retirement, college, goal planning |
| `backend/app/api/api_v1/endpoints/wealth_advisory.py` | Added 3 new endpoints + helper functions |
| `backend/app/services/knowledge_rag.py` | Added 3 new AdvisoryModes + categories |
| `backend/app/knowledge_base/wealth_management/data/retirement_planning.json` | NEW - 122 chunks |
| `backend/app/knowledge_base/wealth_management/data/college_planning.json` | NEW - 105 chunks |
| `backend/app/knowledge_base/wealth_management/data/goal_tier_progression.json` | NEW - 127 chunks |

---

## 10. GCP Agent Instructions (DVoRA/QDoRA Training)

### CRITICAL: Correct Base Model

**DO NOT** use Mistral-7B, Phi-2, or any external models.
**USE** the merged Elson model: `elson-finance-trading-14b-final`

The Elson model was created via 3-stage merge:

```
Stage 1: SLERP Merge (Reasoning + Math)
├── Input: DeepSeek-R1-Distill-Qwen-14B (48 layers)
├── Input: Qwen2.5-Math-14B-Instruct (48 layers)
└── Output: ./checkpoints/elson-reason-math-14b

Stage 2: TIES Merge (Financial Domain)
├── Input: elson-reason-math-14b (60% weight)
├── Input: FinGPT/fingpt-mt_llama2-13b_lora (25% weight)
├── Input: FinGPT/FinLLaMA (15% weight)
└── Output: ./checkpoints/elson-finance-trading-14b

Stage 3: DARE Pruning (Refinement)
├── Input: elson-finance-trading-14b
├── Pruning: 20% small weight deltas dropped
└── Output: elson-finance-trading-14b-final ← PRODUCTION BASE

Stage 4: DVoRA/QDoRA Fine-Tuning (Wealth Management) ← CURRENT
├── Input: elson-finance-trading-14b-final
├── Training Data: 2000+ Q&A pairs from wealth management knowledge base
└── Output: elson-finance-trading-wealth-14b-q4
```

### GCS Model Locations

| Model | GCS Path | Status | Use |
|-------|----------|--------|-----|
| Base Model (14B) | `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/` | ✅ Ready | Foundation |
| **Wealth DoRA v2** | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` | ✅ **PRODUCTION** | Primary (4.2 GB) |
| Wealth DoRA v1 | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100/` | Archive | Previous version |
| QDoRA v1 (quantized) | `gs://elson-33a95-elson-models/elson-finance-trading-wealth-14b-q4/` | Archive | Previous version |
| ~~Wealth LoRA VM1~~ | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm1/` | ⚠️ Deprecated | Do not use |
| ~~Wealth LoRA VM2~~ | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm2/` | ⚠️ Deprecated | Do not use |

> **IMPORTANT:** LoRA models are deprecated. Always use **DoRA** or **QDoRA** for deployments.

### Training Results (2026-01-18) - DoRA v2

**PRODUCTION: DoRA v2 Training on H100 GPU**

| VM | GPU | Method | Loss | Data | Status |
|----|-----|--------|------|------|--------|
| elson-h100-spot | H100 (80GB) | QDoRA (4-bit + DoRA) | **0.4063** | 950 pairs | ✅ **PRODUCTION** |

- Method: QDoRA (4-bit base + DoRA adapter)
- GPU: NVIDIA H100 80GB HBM3 (Spot/Preemptible)
- Data: 950 Q&A pairs (up from 408)
- Runtime: ~25 minutes
- Output: `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` (4.2 GB)

**Previous DoRA v1 (Archive):**
- Data: 408 pairs, Loss: 0.14, Runtime: 6 min
- Location: `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100/`

**DEPRECATED: LoRA Training on L4 GPUs (Archive Only)**

| VM | GPU | Final Loss | Status |
|----|-----|-----------|--------|
| VM1 | L4 (24GB) | 0.0526 | ⚠️ Deprecated |
| VM2 | L4 (24GB) | 0.0532 | ⚠️ Deprecated |

- Method: 4-bit LoRA (r=16, α=32) - used when H100 wasn't available
- **Do not use for production** - DoRA provides better quality

**DoRA Inference Test Results (2026-01-17):**

| Question | Response Quality |
|----------|------------------|
| 401k allocation | Foundation tier guidance with action steps |
| College savings | Specific 529 plan advice with calculations |
| Tax minimization | Growth tier guidance with key considerations |
| Mortgage vs invest | Builder tier guidance with analysis framework |
| Estate planning | HNW/UHNW tier guidance with professional referrals |

Observations:
- Responses are structured with tier-appropriate guidance
- Includes specific action steps and recommendations
- Follows trained format with "Key considerations" and "Next Steps"

**Improved Training Data (v3):**
- Total: 643 Q&A pairs (vs 408 original)
- 18 categories with balanced distribution
- Multi-turn conversations (6 examples)
- Negative examples - what NOT to recommend (7 examples)
- Edge cases (5 examples)
- Compliance disclaimers on all responses
- Evaluation benchmark: 100 test cases

**To use the trained model:**
```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

# Load base model
base = AutoModelForCausalLM.from_pretrained("path/to/elson-finance-trading-14b-final")

# Load DoRA adapter (PRODUCTION)
model = PeftModel.from_pretrained(base, "path/to/wealth-dora-elson14b-h100/")

# DO NOT use LoRA adapters - they are deprecated
# model = PeftModel.from_pretrained(base, "path/to/wealth-lora-elson14b-vm1/")  # DEPRECATED
```

### Step 1: Pull Latest Code

```bash
cd ~/Elson-TB2
git pull origin main
```

### Step 2: Download Base Model from GCS

```bash
# Download the correct merged Elson model
gsutil -m cp -r gs://elson-33a95-elson-models/elson-finance-trading-14b-final/ ./base_model/
```

**Expected:** ~28GB download (14B parameter model)

### Step 3: Generate Training Data (2000+ Q&A Pairs)

```bash
cd ~/Elson-TB2/backend
source ../venv/bin/activate  # or wherever your venv is
python scripts/generate_training_data.py
```

**Expected Output:**

- `training_data/train.jsonl` (~1600 samples, 80%)
- `training_data/validation.jsonl` (~200 samples, 10%)
- `training_data/test.jsonl` (~200 samples, 10%)
- 11 categories covered (retirement, college, estate, trust, succession, roles, literacy, goals, compliance, generational, credit)

### Step 4: Upload Training Data to GCS

```bash
gsutil -m cp -r training_data/* gs://elson-financial-ai/training_data/
```

### Step 5: Run QDoRA Fine-tuning (Memory Optimized for L4 GPU)

**IMPORTANT:** The 14B model requires memory optimization for L4 (24GB VRAM).

Use `train_elson_qdora_v2.py` with these optimizations:
- Batch size: 1 with gradient accumulation: 16
- Max GPU memory: 20GB (allows headroom)
- CPU offloading: 30GB
- 8-bit paged AdamW optimizer
- Gradient checkpointing enabled

```bash
# Activate DVoRA environment
source ~/dvora_env/bin/activate

# Run memory-optimized QDoRA training
python train_elson_qdora_v2.py \
  --model ~/base_model \
  --output ~/wealth-qdora-elson14b \
  --training-data ~/training_data.json \
  --epochs 3

# Monitor training
tail -f ~/training_elson14b_v2.log
```

**Memory Optimization Settings (in script):**
```python
# GPU memory cap with CPU offload
max_memory = {0: "20GiB", "cpu": "30GiB"}

# Training arguments
per_device_train_batch_size=1
gradient_accumulation_steps=16
gradient_checkpointing=True
optim="paged_adamw_8bit"
```

### Step 6: Upload Fine-tuned Model to GCS

```bash
gsutil -m cp -r ~/wealth-qdora-elson14b gs://elson-33a95-elson-models/elson-finance-trading-wealth-14b-q4/
```

### Step 7: Verify Model

```bash
# Test inference with fine-tuned model
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained('./wealth-qdora-elson14b')
tokenizer = AutoTokenizer.from_pretrained('./wealth-qdora-elson14b')
print('Model loaded successfully!')
"
```

### Troubleshooting

**OOM (Out of Memory) Error:**
- Reduce max_memory to `{0: "18GiB", "cpu": "40GiB"}`
- Increase gradient_accumulation_steps to 32
- Reduce max_length to 512 tokens

**Slow Training:**
- Check GPU utilization: `nvidia-smi -l 1`
- Ensure model is on GPU: `watch -n 1 nvidia-smi`

**Model Loading Issues:**
- Verify base_model path contains all shards: `ls -la ~/base_model/`
- Check config.json exists: `cat ~/base_model/config.json`

---

## 11. VM Management Commands

### GCP VM & GPU Inventory (Updated 2026-01-18)

| VM Name | Zone | Machine Type | GPU | VRAM | Disk | Status |
|---------|------|--------------|-----|------|------|--------|
| `elson-h100-spot` | us-central1-a | a3-highgpu-1g | 1x NVIDIA H100 | 80GB HBM3 | 200GB | TERMINATED |
| `elson-dvora-training-l4` | us-east1-b | g2-standard-12 | 1x NVIDIA L4 | 24GB | 200GB | TERMINATED |
| `elson-dvora-training-l4-2` | us-west1-a | g2-standard-8 | 1x NVIDIA L4 | 24GB | 200GB | TERMINATED |
| `my-vm` | us-central1-a | e2-medium | None (CPU) | - | 20GB | RUNNING |

### Start/Stop VMs (You only pay when running)

```bash
# H100 Spot VM (DoRA training) - us-central1-a
gcloud compute instances start elson-h100-spot --zone=us-central1-a
gcloud compute instances stop elson-h100-spot --zone=us-central1-a

# L4 VM #1 - us-east1-b
gcloud compute instances start elson-dvora-training-l4 --zone=us-east1-b
gcloud compute instances stop elson-dvora-training-l4 --zone=us-east1-b

# L4 VM #2 - us-west1-a
gcloud compute instances start elson-dvora-training-l4-2 --zone=us-west1-a
gcloud compute instances stop elson-dvora-training-l4-2 --zone=us-west1-a

# Check all VM status
gcloud compute instances list --filter="name~elson"
```

### SSH into VMs

```bash
# H100 VM (us-central1-a)
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# L4 VM #1 (us-east1-b)
gcloud compute ssh elson-dvora-training-l4 --zone=us-east1-b

# L4 VM #2 (us-west1-a)
gcloud compute ssh elson-dvora-training-l4-2 --zone=us-west1-a

# Claude Code workspace (us-central1-a)
gcloud compute ssh my-vm --zone=us-central1-a
```

### Cost Notes

- **H100 Spot:** ~$2.50/hr (vs ~$8/hr on-demand) - can be preempted
- **L4 On-demand:** ~$0.70/hr per GPU
- **e2-medium (CPU):** ~$0.03/hr
- **Storage (GCS):** ~$0.02/GB/month

---

## 12. Deployment TODO (After Training)

1. **Run inference tests** - Compare LoRA vs DoRA model quality
2. **Deploy to Cloud Run** - Container with FastAPI backend
3. **Final QA testing** - All tiers, all endpoints
4. **Set up Vertex AI endpoint** - For model serving

---

## 13. Next Steps for Tomorrow

### Immediate Tasks

1. **Run inference comparison** - Test DoRA model vs LoRA model quality
   ```bash
   gcloud compute instances start elson-h100-spot --zone=us-central1-a
   # Run test script to compare responses
   ```

2. **Retrain DoRA with improved data** - Use 643 pairs instead of 408
   ```bash
   cd ~/Elson-TB2 && git pull origin main
   # Training data is in backend/training_data/training_data_final.json
   ```

3. **Run evaluation benchmark** - Test against 100 evaluation cases
   - Benchmark file: `backend/training_data/evaluation_benchmark.json`
   - Score each response on accuracy, completeness, compliance, helpfulness

### Model Comparison Checklist

| Metric | LoRA (L4) | DoRA (H100) | Notes |
|--------|-----------|-------------|-------|
| Training Loss | 0.0526 | TBD | Lower is better |
| Inference Speed | TBD | TBD | Tokens/sec |
| Response Quality | TBD | TBD | Manual evaluation |
| Benchmark Score | TBD | TBD | /100 test cases |

### Training Data Improvements Applied

- [x] Generated 643 balanced Q&A pairs (was 408)
- [x] Added multi-turn conversations (6 examples)
- [x] Added negative examples (7 examples)
- [x] Added edge cases (5 examples)
- [x] Added compliance disclaimers
- [x] Created 100-question evaluation benchmark
- [ ] Retrain DoRA with improved data
- [ ] Compare model quality
