# Elson Financial AI - GCP Agent Setup Guide

**Last Updated:** 2026-01-17
**Status:** 98% Complete - LoRA Training Complete, Models in GCS

This document tracks everything needed to restore the GCP environment after ephemeral session ends.

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

## 9. Files Modified in This Session

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

| Model | GCS Path | Status |
|-------|----------|--------|
| Stage 3 Final | `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/` | ✅ Ready |
| Wealth LoRA VM1 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm1/` | ✅ Complete |
| Wealth LoRA VM2 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm2/` | ✅ Complete |

### Training Results (2026-01-17)

| VM | IP | GPU | Final Loss | Runtime | Status |
|----|-----|-----|-----------|---------|--------|
| VM1 | 104.196.0.132 | L4 (24GB) | 0.0526 | 23.5 min | ✅ Complete |
| VM2 | 35.233.173.228 | L4 (24GB) | 0.0532 | 25.1 min | ✅ Complete |

**Training Config:**
- Method: 4-bit LoRA (r=16, α=32) - switched from DoRA due to L4 memory constraints
- Data: 377 Q&A pairs × 3 epochs
- Trainable: 25M / 14.8B params (0.17%)
- Output: ~96MB adapter per VM

**To use the trained model:**
```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("path/to/elson-finance-trading-14b-final")
model = PeftModel.from_pretrained(base, "path/to/wealth-lora-elson14b-vm1/")
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

## 11. Deployment TODO (After Training)

1. **Deploy to Cloud Run** - Container with FastAPI backend
2. **Final QA testing** - All tiers, all endpoints
3. **Set up Vertex AI endpoint** - For model serving
