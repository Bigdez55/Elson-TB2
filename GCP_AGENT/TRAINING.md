# Training Guide

**Purpose:** Complete step-by-step training instructions for the GCP Agent

---

## Training Overview

| Aspect | Value |
|--------|-------|
| **Model** | Elson-Finance-Trading-14B (27.52 GB) |
| **Method** | DoRA (Weight-Decomposed Low-Rank Adaptation) |
| **Approach** | 3-Phase Curriculum Learning |
| **GPU** | NVIDIA H100 80GB HBM3 |
| **Training Data** | 40,993+ Q&A pairs |
| **Estimated Time** | 45-60 minutes |
| **Estimated Cost** | ~$2-3 (H100 Spot) |

---

## Pre-Training Checklist

Run these checks BEFORE starting training:

```bash
# 1. Pull latest code (CRITICAL)
cd ~/Elson-TB2 && git pull origin main

# 2. Verify domain buckets exist
ls backend/training_data/domain_buckets/ | wc -l
# Expected: 80+ directories

# 3. Count training data files
find backend/training_data/domain_buckets -name "*.jsonl" | wc -l
# Expected: 80+ files

# 4. Check curriculum sampler exists
ls scripts/curriculum_sampler.py
# Should exist

# 5. Check training script exists
ls scripts/train-curriculum-h100.sh
# Should exist

# 6. Verify GCP authentication
gcloud auth list
gcloud config get-value project
# Should show: elson-33a95
```

---

## Step 1: Generate Curriculum Manifests

Before training, generate the Phase A/B/C training manifests:

```bash
cd ~/Elson-TB2

# Generate all three phases
python scripts/curriculum_sampler.py --phase all --target-records 15000
```

**Expected Output:**
```
============================================================
Elson Financial AI - Curriculum Sampler
============================================================
Timestamp: 2026-01-19T...
Buckets: backend/training_data/domain_buckets
Output: backend/training_data/curriculum_runs
Phase: all
Seed: 42

[PHASE A] Generating manifest...
============================================================
PHASE A SAMPLING COMPLETE
============================================================
Total Examples: X,XXX

[PHASE B] Generating manifest...
...

[PHASE C] Generating manifest...
...

Done!
```

**Verify manifests were created:**
```bash
ls -la backend/training_data/curriculum_runs/

# Expected files:
# manifest_phaseA_YYYYMMDD_HHMMSS.jsonl
# manifest_phaseB_YYYYMMDD_HHMMSS.jsonl
# manifest_phaseC_YYYYMMDD_HHMMSS.jsonl
# merged_phaseA_YYYYMMDD_HHMMSS.jsonl
# merged_phaseB_YYYYMMDD_HHMMSS.jsonl
# merged_phaseC_YYYYMMDD_HHMMSS.jsonl
```

---

## Step 2: Start H100 VM

```bash
# Start the H100 Spot VM
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# Wait for VM to start (1-2 minutes)
echo "Waiting for VM..."
sleep 60

# Verify VM is running
gcloud compute instances list --filter="name=elson-h100-spot"
# STATUS should be: RUNNING
```

---

## Step 3: SSH into H100

```bash
# SSH into the VM
gcloud compute ssh elson-h100-spot --zone=us-central1-a
```

**Once connected, verify GPU:**
```bash
nvidia-smi

# Expected output:
# NVIDIA H100 80GB HBM3
# Memory: 80GB
```

---

## Step 4: Setup on H100

```bash
# Navigate to repository
cd ~/Elson-TB2

# If repo doesn't exist, clone it
if [ ! -d "Elson-TB2" ]; then
    git clone https://github.com/Bigdez55/Elson-TB2.git
    cd Elson-TB2
fi

# Pull latest changes
git pull origin main

# Verify training script
ls -la scripts/train-curriculum-h100.sh
```

---

## Step 5: Run Curriculum Training

### Option A: Dry Run First (Recommended)

```bash
./scripts/train-curriculum-h100.sh --dry-run
```

This will:
- Check GPU availability
- Verify training data exists
- Show what would be trained
- NOT actually train

### Option B: Full Training

```bash
./scripts/train-curriculum-h100.sh
```

This will:
1. Install dependencies (~2 min)
2. Download base model from GCS (~5 min, first run only)
3. Run Phase A training (~15-20 min)
4. Run Phase B training (~20-25 min)
5. Run Phase C training (~10-15 min)
6. Upload final model to GCS (~5 min)

### Option C: Run Specific Phase

```bash
# Only Phase A (Domain Blocks)
./scripts/train-curriculum-h100.sh --phase A

# Only Phase B (Mixed Curriculum)
./scripts/train-curriculum-h100.sh --phase B

# Only Phase C (Stress Epoch)
./scripts/train-curriculum-h100.sh --phase C
```

---

## Step 6: Monitor Training

In a separate terminal (if available), monitor GPU:

```bash
watch -n 1 nvidia-smi
```

**Expected during training:**
- GPU Memory: 60-70 GB used
- GPU Utilization: 90-100%
- Temperature: 60-80°C

**Training output to watch:**
```
Starting Phase A training...
Step 10: loss = 1.523
Step 20: loss = 1.234
Step 30: loss = 1.056
...
Phase A training complete! Final loss: 0.856

Starting Phase B training...
...
```

**Loss progression targets:**
| Phase | Starting Loss | Ending Loss |
|-------|--------------|-------------|
| A | ~1.5-2.0 | ~0.8-1.0 |
| B | ~0.8-1.0 | ~0.5-0.7 |
| C | ~0.5-0.7 | ~0.3-0.5 |

---

## Step 7: Verify Training Completed

After training finishes:

```bash
# Check model was saved locally
ls -la /workspace/wealth-dora-elson14b-h100-v3-curriculum/

# Expected files:
# adapter_config.json
# adapter_model.safetensors
# training_metadata.json
# tokenizer.json
# tokenizer_config.json

# Check training metadata
cat /workspace/wealth-dora-elson14b-h100-v3-curriculum/training_metadata.json

# Verify GCS upload
gsutil ls gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/
```

---

## Step 8: Stop H100 VM (CRITICAL!)

**This saves money! H100 costs ~$2.50/hour.**

```bash
# Exit SSH session
exit

# Stop the VM
gcloud compute instances stop elson-h100-spot --zone=us-central1-a

# Verify VM is stopped
gcloud compute instances list --filter="name=elson-h100-spot"
# STATUS should be: TERMINATED
```

---

## Post-Training: Quick Inference Test

Before stopping VM, optionally test the model:

```bash
python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

print("Loading model...")
base = AutoModelForCausalLM.from_pretrained(
    "/workspace/base_model",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
model = PeftModel.from_pretrained(
    base,
    "/workspace/wealth-dora-elson14b-h100-v3-curriculum"
)
tokenizer = AutoTokenizer.from_pretrained("/workspace/wealth-dora-elson14b-h100-v3-curriculum")

print("Testing inference...")
prompt = "### Instruction:\nWhat is a 401(k) retirement account?\n\n### Response:\n"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
EOF
```

---

## Training Hyperparameters Reference

| Parameter | Value | Description |
|-----------|-------|-------------|
| `r` (rank) | 128 | DoRA rank |
| `lora_alpha` | 256 | Scaling factor (2x rank) |
| `lora_dropout` | 0.05 | Regularization |
| `use_dora` | True | Enable DoRA |
| `batch_size` | 16 | Per-device batch |
| `gradient_accumulation` | 4 | Effective batch: 64 |
| `epochs_per_phase` | 2 | 6 total across phases |
| `learning_rate` | 2e-4 | Standard for DoRA |
| `max_seq_length` | 2048 | Context window |
| `precision` | bfloat16 | H100 native |

---

## Legacy Training (Flat, Non-Curriculum)

If you need to run the old flat training method:

```bash
./scripts/train-and-quantize-h100.sh
```

This uses `consolidated_training_data.json` instead of curriculum phases.

---

## Next Steps After Training

1. **Deploy for inference:**
   ```bash
   ./scripts/deploy-vllm-dora.sh l4 dora
   ```

2. **Run evaluation benchmark:**
   ```bash
   python scripts/run_model_evaluation.py --api-url http://EXTERNAL_IP:8000
   ```

3. **Compare with previous models:**
   - Check loss values
   - Run benchmark comparisons
   - Test specific domain questions

---

*See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues.*
