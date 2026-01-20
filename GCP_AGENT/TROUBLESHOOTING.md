# Troubleshooting Guide

**Purpose:** Common issues and solutions for the GCP Agent

---

## Table of Contents

1. [VM Issues](#vm-issues)
2. [Training Issues](#training-issues)
3. [GPU Issues](#gpu-issues)
4. [GCS (Storage) Issues](#gcs-storage-issues)
5. [Authentication Issues](#authentication-issues)
6. [Quota Issues](#quota-issues)
7. [Network Issues](#network-issues)
8. [Deployment Issues](#deployment-issues)

---

## VM Issues

### VM Won't Start

**Symptom:** `gcloud compute instances start` hangs or fails

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Spot VM preempted | Wait 5-10 min, try again |
| Quota exceeded | Check quotas, request increase |
| Zone capacity | Try different zone |
| Billing issue | Check billing account |

**Commands:**
```bash
# Check VM status
gcloud compute instances describe elson-h100-spot --zone=us-central1-a

# Try different zone
gcloud compute instances start elson-h100-spot --zone=us-central1-b

# Check quotas
gcloud compute regions describe us-central1 --format="table(quotas.metric,quotas.limit,quotas.usage)"
```

---

### Can't SSH into VM

**Symptom:** SSH connection refused or timeout

**Solutions:**

```bash
# 1. Verify VM is running
gcloud compute instances list --filter="name=elson-h100-spot"

# 2. Wait for VM to fully boot (1-2 min after start)
sleep 120

# 3. Try with more verbose output
gcloud compute ssh elson-h100-spot --zone=us-central1-a --verbosity=debug

# 4. Check firewall rules
gcloud compute firewall-rules list

# 5. Reset SSH keys (if corrupted)
gcloud compute instances add-metadata elson-h100-spot \
  --zone=us-central1-a \
  --metadata-from-file ssh-keys=~/.ssh/google_compute_engine.pub
```

---

### VM Costs Too High

**Symptom:** Unexpected billing charges

**Prevention:**

```bash
# ALWAYS stop VMs when done
gcloud compute instances stop elson-h100-spot --zone=us-central1-a

# Check all running VMs
gcloud compute instances list --filter="status=RUNNING"

# Set up billing alerts (in GCP Console)
# Go to: Billing → Budgets & alerts → Create budget
```

**Cost Reference:**
| VM | Cost/hr (On-Demand) | Cost/hr (Spot) |
|----|---------------------|----------------|
| H100 | ~$8.00 | ~$2.50 |
| L4 | ~$1.50 | ~$0.70 |
| CPU (my-vm) | ~$0.03 | N/A |

---

## Training Issues

### Training Script Not Found

**Symptom:** `./scripts/train-curriculum-h100.sh: No such file`

**Solution:**
```bash
# 1. Make sure you're in the right directory
cd ~/Elson-TB2

# 2. Pull latest code
git pull origin main

# 3. Check script exists
ls -la scripts/train-curriculum-h100.sh

# 4. Make executable
chmod +x scripts/train-curriculum-h100.sh
```

---

### Training Data Not Found

**Symptom:** Training fails with "No such file or directory" for training data

**Solution:**
```bash
# 1. Check domain buckets exist
ls backend/training_data/domain_buckets/ | wc -l
# Expected: 80+

# 2. Check curriculum manifests exist
ls backend/training_data/curriculum_runs/

# 3. Generate manifests if missing
python scripts/curriculum_sampler.py --phase all --target-records 15000

# 4. Verify manifests were created
ls -la backend/training_data/curriculum_runs/merged_phase*.jsonl
```

---

### Training Crashes with OOM

**Symptom:** CUDA out of memory error

**Solutions:**

```bash
# 1. Reduce batch size in training script
# Edit: scripts/train-curriculum-h100.sh
# Change: BATCH_SIZE=16 to BATCH_SIZE=8

# 2. Enable gradient checkpointing
# Already enabled in training script

# 3. Clear GPU memory
nvidia-smi --gpu-reset

# 4. Kill any stuck processes
pkill -f python
pkill -f train
```

**Memory Requirements:**
| Component | VRAM Usage |
|-----------|------------|
| Base model (14B, bf16) | ~28GB |
| DoRA adapters | ~2GB |
| Optimizer states | ~15GB |
| Activations | ~20GB |
| **Total** | ~65GB |

H100 has 80GB, so this fits with some headroom.

---

### Training Loss Not Decreasing

**Symptom:** Loss stays flat or increases

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Learning rate too high | Reduce from 2e-4 to 1e-4 |
| Learning rate too low | Increase from 2e-4 to 5e-4 |
| Data quality issue | Check training data for errors |
| Wrong data format | Verify JSONL format |
| Batch size too small | Increase to 16 |

**Check training data format:**
```bash
# Verify JSONL is valid
head -1 backend/training_data/curriculum_runs/merged_phaseA_*.jsonl | python -m json.tool

# Count records
wc -l backend/training_data/curriculum_runs/merged_phaseA_*.jsonl
```

---

### Training Interrupted (Spot Preemption)

**Symptom:** Training stops unexpectedly on Spot VM

**Solution:**
```bash
# 1. Restart VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# 2. SSH back in
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# 3. Resume from checkpoint (if available)
cd ~/Elson-TB2
./scripts/train-curriculum-h100.sh --resume

# 4. Or restart from specific phase
./scripts/train-curriculum-h100.sh --phase B  # If Phase A completed
```

---

## GPU Issues

### GPU Not Detected

**Symptom:** `nvidia-smi` returns error

**Solutions:**
```bash
# 1. Check NVIDIA driver
nvidia-smi

# 2. Reinstall driver (if needed)
sudo apt update
sudo apt install -y nvidia-driver-535

# 3. Reboot VM
sudo reboot

# 4. Reconnect and verify
nvidia-smi
```

---

### GPU Memory Not Freed

**Symptom:** GPU shows high memory usage but no processes

**Solution:**
```bash
# 1. List GPU processes
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

# 2. Kill zombie processes
sudo fuser -v /dev/nvidia*
sudo kill -9 <PID>

# 3. Reset GPU
sudo nvidia-smi --gpu-reset

# 4. If still stuck, reboot VM
sudo reboot
```

---

### CUDA Version Mismatch

**Symptom:** `CUDA error: no kernel image is available`

**Solution:**
```bash
# Check CUDA version
nvcc --version

# Check PyTorch CUDA version
python -c "import torch; print(torch.version.cuda)"

# They should match. If not:
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## GCS (Storage) Issues

### Permission Denied on GCS

**Symptom:** `AccessDeniedException: 403`

**Solution:**
```bash
# 1. Check authentication
gcloud auth list

# 2. Re-authenticate
gcloud auth login

# 3. Set correct project
gcloud config set project elson-33a95

# 4. Check bucket permissions
gsutil iam get gs://elson-33a95-elson-models/
```

---

### Model Upload Failed

**Symptom:** `gsutil cp` fails or hangs

**Solutions:**
```bash
# 1. Use parallel upload (-m flag)
gsutil -m cp -r /workspace/wealth-dora-elson14b-h100-v3-curriculum gs://elson-33a95-elson-models/

# 2. Increase timeout
gsutil -o "GSUtil:default_api_version=2" cp -r ...

# 3. Upload in chunks
gsutil -m cp /workspace/model/*.safetensors gs://elson-33a95-elson-models/model/
gsutil -m cp /workspace/model/*.json gs://elson-33a95-elson-models/model/

# 4. Check available disk space
df -h
```

---

### Model Download Too Slow

**Symptom:** `gsutil cp` takes very long

**Solution:**
```bash
# Use parallel download with -m flag
gsutil -m cp -r gs://elson-33a95-elson-models/elson-finance-trading-14b-final/ /workspace/base_model/

# Check network speed
curl -o /dev/null -w "Speed: %{speed_download}\n" https://storage.googleapis.com
```

---

## Authentication Issues

### gcloud Not Authenticated

**Symptom:** `ERROR: (gcloud) You do not have permission`

**Solution:**
```bash
# 1. Check current auth
gcloud auth list

# 2. Re-authenticate
gcloud auth login

# 3. Set project
gcloud config set project elson-33a95

# 4. Verify
gcloud config get-value project
```

---

### Service Account Issues

**Symptom:** Automation scripts fail with auth errors

**Solution:**
```bash
# 1. Check service account
gcloud iam service-accounts list

# 2. Activate service account (if using)
gcloud auth activate-service-account --key-file=/path/to/key.json

# 3. Use application default credentials
gcloud auth application-default login
```

---

## Quota Issues

### GPU Quota Exceeded

**Symptom:** VM creation fails with quota error

**Solution:**
1. Go to: https://console.cloud.google.com/iam-admin/quotas?project=elson-33a95
2. Filter: "NVIDIA_H100_GPUS" or "NVIDIA_L4_GPUS"
3. Select region (us-central1-a)
4. Click "Edit Quotas"
5. Request increase (1 GPU)
6. Wait 24-48 hours for approval

**Check current quotas:**
```bash
gcloud compute regions describe us-central1 \
  --format="table(quotas.metric,quotas.limit,quotas.usage)" \
  | grep -i gpu
```

---

### Disk Quota Exceeded

**Symptom:** Can't create disk or resize

**Solution:**
```bash
# Check disk usage
gcloud compute disks list

# Delete old/unused disks
gcloud compute disks delete OLD_DISK_NAME --zone=us-central1-a

# Request quota increase (same process as GPU)
```

---

## Network Issues

### SSH Timeout

**Symptom:** SSH connection times out

**Solutions:**
```bash
# 1. Use IAP tunnel
gcloud compute ssh elson-h100-spot \
  --zone=us-central1-a \
  --tunnel-through-iap

# 2. Check firewall
gcloud compute firewall-rules list --filter="name~ssh"

# 3. Create SSH firewall rule (if missing)
gcloud compute firewall-rules create allow-ssh \
  --allow=tcp:22 \
  --source-ranges=0.0.0.0/0
```

---

### Can't Access vLLM Endpoint

**Symptom:** curl to vLLM returns connection refused

**Solutions:**
```bash
# 1. Check VM external IP
gcloud compute instances describe elson-vllm-l4 \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# 2. Check if vLLM is running
gcloud compute ssh elson-vllm-l4 --zone=us-central1-a -- "ps aux | grep vllm"

# 3. Check firewall allows port 8000
gcloud compute firewall-rules list --filter="name~8000"

# 4. Create firewall rule if needed
gcloud compute firewall-rules create allow-vllm \
  --allow=tcp:8000 \
  --source-ranges=0.0.0.0/0
```

---

## Deployment Issues

### vLLM Won't Start

**Symptom:** vLLM server fails to start

**Solutions:**
```bash
# 1. Check GPU availability
nvidia-smi

# 2. Check vLLM logs
cat ~/vllm.log

# 3. Check model exists
ls -la /workspace/model/

# 4. Try with reduced settings
python -m vllm.entrypoints.openai.api_server \
  --model /workspace/model \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.8
```

---

### Model Too Large for GPU

**Symptom:** OOM when loading model for inference

**Solutions:**

| GPU | VRAM | Solution |
|-----|------|----------|
| T4 | 16GB | Use quantized (4-bit) model |
| L4 | 24GB | Use QDoRA adapter |
| A100 | 40GB | Full model fits |
| H100 | 80GB | Full model fits easily |

**For L4 (24GB):**
```bash
# Use QDoRA (quantized DoRA)
./scripts/deploy-vllm-dora.sh l4 qdora

# Or quantize existing model
python -c "
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
model = AutoModelForCausalLM.from_pretrained(
    '/workspace/model',
    quantization_config=BitsAndBytesConfig(load_in_4bit=True)
)
"
```

---

## Quick Diagnostic Commands

Run these to diagnose most issues:

```bash
# System overview
echo "=== VM Status ==="
gcloud compute instances list --filter="name~elson"

echo "=== GPU Status ==="
nvidia-smi

echo "=== Disk Space ==="
df -h

echo "=== Memory ==="
free -h

echo "=== Python Processes ==="
ps aux | grep python

echo "=== GCP Auth ==="
gcloud auth list
gcloud config get-value project

echo "=== Training Data ==="
ls backend/training_data/domain_buckets/ | wc -l
ls backend/training_data/curriculum_runs/

echo "=== GCS Models ==="
gsutil ls gs://elson-33a95-elson-models/
```

---

## Emergency Recovery

If everything is broken:

```bash
# 1. Stop all VMs (saves money)
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
gcloud compute instances stop elson-dvora-training-l4 --zone=us-east1-b
gcloud compute instances stop elson-dvora-training-l4-2 --zone=us-west1-a

# 2. Re-authenticate
gcloud auth login
gcloud config set project elson-33a95

# 3. Verify GCS access
gsutil ls gs://elson-33a95-elson-models/

# 4. Start fresh
gcloud compute instances start elson-h100-spot --zone=us-central1-a
sleep 120
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# 5. On VM: Fresh clone
cd ~
rm -rf Elson-TB2
git clone https://github.com/Bigdez55/Elson-TB2.git
cd Elson-TB2
./scripts/train-curriculum-h100.sh
```

---

*Last Updated: 2026-01-19*
