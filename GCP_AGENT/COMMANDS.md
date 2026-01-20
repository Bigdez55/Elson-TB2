# Commands Reference

**Purpose:** All commands the GCP Agent needs in one place

---

## Table of Contents

1. [Session Management](#session-management)
2. [VM Management](#vm-management)
3. [Training Commands](#training-commands)
4. [GCS (Storage) Commands](#gcs-storage-commands)
5. [Monitoring Commands](#monitoring-commands)
6. [Deployment Commands](#deployment-commands)
7. [Emergency Commands](#emergency-commands)

---

## Session Management

### Start Every Session

```bash
# ALWAYS run this first
cd ~/Elson-TB2 && git pull origin main

# Check current status
cat GCP_AGENT/README.md | head -50
```

### End Every Session

```bash
# Stop all GPU VMs
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
gcloud compute instances stop elson-dvora-training-l4 --zone=us-east1-b
gcloud compute instances stop elson-dvora-training-l4-2 --zone=us-west1-a

# Verify all stopped
gcloud compute instances list --filter="name~elson"
```

---

## VM Management

### List All VMs

```bash
gcloud compute instances list
```

### List Elson VMs Only

```bash
gcloud compute instances list --filter="name~elson"
```

### H100 VM (Training)

```bash
# Start H100
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# SSH into H100
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# Stop H100
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

### L4 VM #1 (Inference)

```bash
# Start L4
gcloud compute instances start elson-dvora-training-l4 --zone=us-east1-b

# SSH into L4
gcloud compute ssh elson-dvora-training-l4 --zone=us-east1-b

# Stop L4
gcloud compute instances stop elson-dvora-training-l4 --zone=us-east1-b
```

### L4 VM #2 (Backup)

```bash
# Start L4 #2
gcloud compute instances start elson-dvora-training-l4-2 --zone=us-west1-a

# SSH into L4 #2
gcloud compute ssh elson-dvora-training-l4-2 --zone=us-west1-a

# Stop L4 #2
gcloud compute instances stop elson-dvora-training-l4-2 --zone=us-west1-a
```

### Claude Code VM (CPU)

```bash
# SSH into my-vm
gcloud compute ssh my-vm --zone=us-central1-a
```

---

## Training Commands

### Generate Curriculum Manifests

```bash
# Generate all phases (recommended)
python scripts/curriculum_sampler.py --phase all --target-records 15000

# Generate specific phase
python scripts/curriculum_sampler.py --phase A --target-records 5000
python scripts/curriculum_sampler.py --phase B --target-records 10000
python scripts/curriculum_sampler.py --phase C --target-records 5000

# Generate for specific domain (Phase A only)
python scripts/curriculum_sampler.py --phase A --domain federal_income_tax
```

### Run Curriculum Training (on H100)

```bash
# Dry run first (recommended)
./scripts/train-curriculum-h100.sh --dry-run

# Full training (all phases)
./scripts/train-curriculum-h100.sh

# Specific phase only
./scripts/train-curriculum-h100.sh --phase A
./scripts/train-curriculum-h100.sh --phase B
./scripts/train-curriculum-h100.sh --phase C
```

### Run Legacy Flat Training (on H100)

```bash
./scripts/train-and-quantize-h100.sh
```

### Check Training Data

```bash
# Count domain buckets
ls backend/training_data/domain_buckets/ | wc -l

# Count total bucket files
find backend/training_data/domain_buckets -name "*.jsonl" | wc -l

# List curriculum runs
ls -la backend/training_data/curriculum_runs/

# Count training pairs in a file
wc -l backend/training_data/curriculum_runs/merged_phaseB_*.jsonl
```

---

## GCS (Storage) Commands

### List All Models

```bash
gsutil ls gs://elson-33a95-elson-models/
```

### List Specific Model Contents

```bash
# Base model
gsutil ls gs://elson-33a95-elson-models/elson-finance-trading-14b-final/

# DoRA v2
gsutil ls gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/

# Curriculum DoRA
gsutil ls gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/
```

### Check Model Size

```bash
gsutil du -sh gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/
```

### Download Model

```bash
# Download to local
gsutil -m cp -r gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/ ./

# Download to /workspace (on VM)
gsutil -m cp -r gs://elson-33a95-elson-models/elson-finance-trading-14b-final/ /workspace/base_model/
```

### Upload Model

```bash
# Upload adapter
gsutil -m cp -r /workspace/wealth-dora-elson14b-h100-v3-curriculum gs://elson-33a95-elson-models/
```

### Delete Model (CAREFUL!)

```bash
# Delete a model version
gsutil -m rm -r gs://elson-33a95-elson-models/OLD_MODEL_NAME/
```

---

## Monitoring Commands

### GPU Status (on VM)

```bash
# One-time check
nvidia-smi

# Continuous monitoring
watch -n 1 nvidia-smi
```

### Disk Space

```bash
df -h
```

### Memory

```bash
free -h
```

### Running Processes

```bash
ps aux | grep python
```

### Kill Stuck Process

```bash
pkill -f train
pkill -f python
```

### Check Training Logs

```bash
# If training writes to file
tail -f ~/training.log

# Most recent lines
tail -100 ~/training.log
```

---

## Deployment Commands

### Deploy vLLM with DoRA

```bash
# Deploy on L4 (recommended)
./scripts/deploy-vllm-dora.sh l4 dora

# Deploy on Spot (cheaper)
./scripts/deploy-vllm-dora.sh spot dora

# Deploy QDoRA (quantized)
./scripts/deploy-vllm-dora.sh l4 qdora
```

### Test vLLM Endpoint

```bash
# Get external IP
gcloud compute instances describe elson-vllm-l4 \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Test API
curl http://EXTERNAL_IP:8000/v1/models

# Test completion
curl http://EXTERNAL_IP:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "elson", "prompt": "What is a 401k?", "max_tokens": 100}'
```

### Run Evaluation Benchmark

```bash
python scripts/run_model_evaluation.py --api-url http://EXTERNAL_IP:8000
```

---

## Emergency Commands

### Stop ALL VMs Immediately

```bash
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
gcloud compute instances stop elson-dvora-training-l4 --zone=us-east1-b
gcloud compute instances stop elson-dvora-training-l4-2 --zone=us-west1-a
```

### Check Running VMs

```bash
gcloud compute instances list --filter="status=RUNNING"
```

### Check GCP Authentication

```bash
gcloud auth list
gcloud config get-value project
```

### Re-authenticate

```bash
gcloud auth login
gcloud config set project elson-33a95
```

### Check Quotas

```bash
gcloud compute regions describe us-central1 --format="table(quotas.metric,quotas.limit,quotas.usage)"
```

### Request GPU Quota

1. Go to: https://console.cloud.google.com/iam-admin/quotas?project=elson-33a95
2. Filter: "NVIDIA_L4_GPUS" or "NVIDIA_H100_GPUS"
3. Select region and request increase

---

## Quick Copy-Paste Workflows

### Full Training Workflow

```bash
# From Cloud Shell or local:
cd ~/Elson-TB2 && git pull origin main
python scripts/curriculum_sampler.py --phase all --target-records 15000
gcloud compute instances start elson-h100-spot --zone=us-central1-a
sleep 60
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# On H100:
cd ~/Elson-TB2 && git pull origin main
./scripts/train-curriculum-h100.sh

# After training:
exit
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

### Quick Status Check

```bash
gcloud compute instances list --filter="name~elson"
gsutil ls gs://elson-33a95-elson-models/
```

---

*Last Updated: 2026-01-19*
