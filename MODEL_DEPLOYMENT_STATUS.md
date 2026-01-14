# Elson Financial AI - Model Deployment Status

**Last Updated:** 2026-01-14 18:40 UTC

## Current Status

### Model Merge - COMPLETE
- **Model:** Elson-Finance-Trading-14B
- **Location:** `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final/`
- **Size:** 27.52 GB (6 shards in SafeTensors format)
- **Base Models Merged:**
  - DeepSeek-R1-Distill-Qwen-14B (reasoning)
  - Qwen2.5-14B-Instruct (general capabilities)
- **Merge Methods:** SLERP + DARE-TIES pruning

### vLLM Deployment - PAUSED
- **Issue:** T4 GPU (16GB) insufficient for 14B model (~28GB required)
- **Solution Options:**
  1. Request L4 GPU quota (24GB) - recommended
  2. Use 2x T4 GPUs with tensor parallelism (32GB total)
  3. Quantize model to 4-bit (~8GB)

### Frontend & Backend - RUNNING
- **Frontend:** Cloud Run (us-central1)
- **Backend:** Cloud Run (us-central1)
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

| Resource | Name | Status | Location |
|----------|------|--------|----------|
| GCS Bucket | elson-33a95-elson-models | Active | us-west1 |
| Firewall Rule | allow-vllm | Active | global (tcp:8000) |
| Secret | HF_TOKEN | Active | Secret Manager |
| Secret | DB_PASSWORD | Active | Secret Manager |
| VM | elson-vllm-server | **Deleted** | - |

## Cost Estimates

| Resource | Cost |
|----------|------|
| vLLM Server (L4) | ~$1.00/hour |
| vLLM Server (2x T4) | ~$1.50/hour |
| GCS Storage | ~$0.60/month |
| Cloud Run | Pay per request |

## Next Steps

1. [ ] Request L4 GPU quota (recommended)
2. [ ] Wait for model updates from GitHub agent
3. [ ] Re-run model merge if base models changed
4. [ ] Deploy with appropriate GPU
5. [ ] Integrate vLLM API with backend

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
