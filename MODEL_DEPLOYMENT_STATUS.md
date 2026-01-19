# Elson Financial AI - Model Deployment Status

**Last Updated:** 2026-01-19

## Current Status

### Model Merge - COMPLETE
- **Model:** Elson-Finance-Trading-14B
- **Location:** `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final/`
- **Size:** 27.52 GB (6 shards in SafeTensors format)
- **Base Models Merged:**
  - DeepSeek-R1-Distill-Qwen-14B (reasoning)
  - Qwen2.5-14B-Instruct (general capabilities)
- **Merge Methods:** SLERP + DARE-TIES pruning

### Fine-Tuning - COMPLETE ✓

> **IMPORTANT:** Only DoRA/QDoRA are production-ready. LoRA models are deprecated.

| Model | GCS Location | Loss | Status |
|-------|--------------|------|--------|
| **DoRA v2 (H100)** | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` | 0.4063 | **PRODUCTION** |
| DoRA v1 (H100) | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100/` | 0.14 | Archived |
| QDoRA v1 (quantized) | `gs://elson-33a95-elson-models/elson-finance-trading-wealth-14b-q4/` | - | Archived |
| ~~LoRA VM1~~ | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm1/` | 0.0526 | DEPRECATED |
| ~~LoRA VM2~~ | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm2/` | 0.0532 | DEPRECATED |

**DoRA v2 Training Details (2026-01-19):**
- Method: QDoRA (4-bit quantized base + DoRA adapter)
- Rank: 64, Alpha: 128
- Epochs: 5, Batch Size: 64 (effective)
- Training Data: 950 Q&A pairs (Alpaca format)
- GPU: H100 80GB

### Inference Testing - VERIFIED ✓

**Tested on:** L4 GPU (24GB VRAM)
- GPU Memory Used: 13.02 GB (4-bit quantized)
- Model loads successfully with PEFT adapter
- All test prompts generated coherent finance/trading responses
- Response quality: Accurate, practical, includes disclaimers

### vLLM Deployment - READY TO DEPLOY
- **Status:** L4 GPUs available, ready to deploy
- **Recommended:** Use existing L4 VMs or deploy new with `./scripts/deploy-vllm-dora.sh`
- **Options:**
  1. `elson-dvora-training-l4` (us-east1-b) - L4 24GB
  2. `elson-dvora-training-l4-2` (us-west1-a) - L4 24GB
  3. New VM with DoRA adapter support

### Frontend & Backend - RUNNING
- **Frontend:** Cloud Run (us-west1)
- **Backend:** Cloud Run (us-west1)
- **Database:** Cloud SQL PostgreSQL

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              Google Cloud                │
                    │                                          │
    ┌───────────────┼──────────────────────────────────────────┼───────────────┐
    │               │                                          │               │
    │  ┌────────────▼────────────┐    ┌────────────────────────▼────────────┐  │
    │  │     Cloud Run           │    │         Cloud Run                   │  │
    │  │   elson-frontend        │    │       elson-backend                 │  │
    │  │   (React TypeScript)    │◄───│       (FastAPI Python)              │  │
    │  └─────────────────────────┘    └──────────────┬───────────────────────┘  │
    │                                                 │                         │
    │                                                 ▼                         │
    │                                    ┌───────────────────────┐              │
    │                                    │     Cloud SQL         │              │
    │                                    │    PostgreSQL         │              │
    │                                    └───────────────────────┘              │
    │                                                                           │
    │  ┌─────────────────────────────────────────────────────────────────────┐  │
    │  │                    AI/ML Infrastructure                              │  │
    │  │                                                                      │  │
    │  │   ┌─────────────────┐         ┌─────────────────────────────────┐   │  │
    │  │   │  GCS Bucket     │         │  Compute Engine VM (future)     │   │  │
    │  │   │  elson-models   │────────►│  vLLM Server + L4 GPU           │   │  │
    │  │   │  (27.5GB model) │         │  Elson-Finance-Trading-14B      │   │  │
    │  │   └─────────────────┘         └─────────────────────────────────┘   │  │
    │  │                                                                      │  │
    │  └─────────────────────────────────────────────────────────────────────┘  │
    │                                                                           │
    └───────────────────────────────────────────────────────────────────────────┘
```

## Deployment Scripts

### Deploy Model with L4 GPU (when quota approved)

```bash
# 1. Create VM with L4 GPU
gcloud compute instances create elson-vllm-server \
  --zone=us-central1-a \
  --machine-type=g2-standard-8 \
  --accelerator=type=nvidia-l4,count=1 \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --maintenance-policy=TERMINATE \
  --scopes=cloud-platform \
  --tags=http-server \
  --metadata=startup-script='#!/bin/bash
exec > /var/log/vllm-deploy.log 2>&1
pip install vllm
mkdir -p /workspace/elson-model
gsutil -m cp -r gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final/* /workspace/elson-model/
python3 -m vllm.entrypoints.openai.api_server \
  --model /workspace/elson-model \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype half \
  --max-model-len 4096 \
  --trust-remote-code'

# 2. Get external IP
gcloud compute instances describe elson-vllm-server --zone=us-central1-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

# 3. Test the API
curl http://<EXTERNAL_IP>:8000/v1/models
```

### Deploy with 2x T4 (if L4 not available)

```bash
gcloud compute instances create elson-vllm-server \
  --zone=europe-west4-a \
  --machine-type=n1-standard-16 \
  --accelerator=type=nvidia-tesla-t4,count=2 \
  --image-family=pytorch-2-7-cu128-ubuntu-2204-nvidia-570 \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=100GB \
  --maintenance-policy=TERMINATE \
  --scopes=cloud-platform \
  --tags=http-server \
  --metadata=startup-script='#!/bin/bash
pip install vllm
gsutil -m cp -r gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final/* /workspace/elson-model/
python3 -m vllm.entrypoints.openai.api_server \
  --model /workspace/elson-model \
  --tensor-parallel-size 2 \
  --host 0.0.0.0 --port 8000'
```

## GCP Resources

### VMs (GPU Training/Inference)

| VM Name | Zone | GPU | VRAM | Status | Cost/hr |
|---------|------|-----|------|--------|---------|
| `elson-h100-spot` | us-central1-a | 1x H100 | 80GB | TERMINATED | ~$2.50 |
| `elson-dvora-training-l4` | us-east1-b | 1x L4 | 24GB | TERMINATED | ~$0.70 |
| `elson-dvora-training-l4-2` | us-west1-a | 1x L4 | 24GB | TERMINATED | ~$0.70 |
| `my-vm` | us-central1-a | None | - | RUNNING | ~$0.03 |

### Other Resources

| Resource | Name | Status | Location |
|----------|------|--------|----------|
| GCS Bucket | elson-33a95-elson-models | Active | us-west1 |
| Firewall Rule | allow-vllm | Active | global (tcp:8000) |
| Secret | HF_TOKEN | Active | Secret Manager |
| Secret | DB_PASSWORD | Active | Secret Manager |

## Cost Estimates

| Resource | Cost |
|----------|------|
| H100 Spot (training) | ~$2.50/hour |
| L4 On-demand (inference) | ~$0.70/hour |
| e2-medium (Claude Code) | ~$0.03/hour |
| GCS Storage | ~$0.60/month |
| Cloud Run | Pay per request |

## Next Steps

1. [x] DoRA training complete on H100 (**PRODUCTION**)
2. [x] QDoRA quantized model ready (**PRODUCTION**)
3. [x] Training data expanded to 950 Q&A pairs
4. [x] DoRA v2 retrained with expanded data (2026-01-19)
5. [x] Inference tested on L4 GPU - VERIFIED WORKING
6. [ ] Deploy vLLM on L4 with DoRA adapter
7. [ ] Run 100-question evaluation benchmark
8. [ ] Integrate vLLM API with Cloud Run backend

> **Note:** LoRA models (VM1/VM2) are deprecated and archived. Use DoRA for full quality or QDoRA for cost-efficient inference.

## Quick Commands

```bash
# Check GCS model
gsutil ls -l gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final/

# Request GPU quota
# Go to: https://console.cloud.google.com/iam-admin/quotas?project=elson-33a95
# Filter: "L4" or "GPU"

# Delete old resources
gcloud compute instances delete elson-vllm-server --zone=europe-west4-a --quiet
```
