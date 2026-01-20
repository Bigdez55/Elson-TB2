# GCP Agent - Central Documentation

**Last Updated:** 2026-01-19
**Purpose:** Single source of truth for the GCP Agent

---

## Quick Start

```bash
# 1. Pull latest code (ALWAYS do this first)
cd ~/Elson-TB2 && git pull origin main

# 2. Check what to do
cat GCP_AGENT/README.md
```

---

## Folder Contents

### Core Training Guides
| File | Purpose | When to Use |
|------|---------|-------------|
| [README.md](README.md) | This file - main entry point | Start here |
| [TRAINING.md](TRAINING.md) | Quick training instructions | Running training jobs |
| [TRAINING_GUIDE.md](TRAINING_GUIDE.md) | Comprehensive training guide | Detailed training reference |
| [TRAINING_PLAN.md](TRAINING_PLAN.md) | Training plan overview | Planning training runs |
| [TRAINING_PLANv2.md](TRAINING_PLANv2.md) | Updated training plan | Latest training strategy |
| [CURRICULUM.md](CURRICULUM.md) | 3-Phase curriculum method | Understanding training approach |

### Reference & Commands
| File | Purpose | When to Use |
|------|---------|-------------|
| [COMMANDS.md](COMMANDS.md) | All commands reference | Quick command lookup |
| [DATA_STRUCTURE.md](DATA_STRUCTURE.md) | Training data organization | Understanding data layout |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and fixes | When something breaks |
| [SETUP.md](SETUP.md) | GCP Agent setup guide | Initial environment setup |

### Planning & Workflow
| File | Purpose | When to Use |
|------|---------|-------------|
| [ACTION_PLAN.md](ACTION_PLAN.md) | Current action items | What to do next |
| [WORKFLOW.md](WORKFLOW.md) | Agent workflow guide | Understanding agent handoffs |
| [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md) | Issue remediation | Fixing known issues |
| [TRAINING_LOG.md](TRAINING_LOG.md) | Training benchmark history | Tracking all training sessions |

---

## GCP Agent Sole Purpose

> **The GCP Agent exists ONLY to train/enhance the model and manage GCP resources.**

### What GCP Agent DOES

| Task | Examples |
|------|----------|
| **Train the Model** | DoRA/QDoRA fine-tuning, curriculum training, run training jobs |
| **Manage GPU VMs** | Start/stop H100/L4 VMs, SSH into VMs, monitor GPU usage |
| **Manage GCS** | Upload/download models, check bucket contents |
| **Request Quotas** | GPU quota requests, resource allocation |
| **Run Inference** | Test model responses, run benchmarks |
| **Monitor Costs** | Track VM costs, optimize resource usage |

### What GCP Agent does NOT do

- Write or edit code (GitHub Agent only)
- Create new scripts (GitHub Agent only)
- Update documentation (GitHub Agent only)
- Push to GitHub (GitHub Agent only)
- Frontend/backend development (GitHub Agent only)

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| **Base Model** | Ready | `elson-finance-trading-14b-final` (27.52 GB) |
| **Training Method** | **Curriculum (3-Phase)** | Phase A → B → C |
| **Training Data** | 40,993+ pairs | Domain buckets + consolidated |
| **Latest Adapter** | `wealth-dora-elson14b-h100-v2` | DoRA v2 |
| **H100 VM** | TERMINATED | Start when needed |

---

## VM Inventory

| VM Name | Zone | GPU | VRAM | Status | Cost/hr |
|---------|------|-----|------|--------|---------|
| `elson-h100-spot` | us-central1-a | H100 | 80GB | TERMINATED | ~$2.50 |
| `elson-dvora-training-l4` | us-east1-b | L4 | 24GB | TERMINATED | ~$0.70 |
| `elson-dvora-training-l4-2` | us-west1-a | L4 | 24GB | TERMINATED | ~$0.70 |
| `my-vm` | us-central1-a | None | - | RUNNING | ~$0.03 |

---

## Quick Command Reference

### Start Training Session

```bash
# 1. Pull latest
cd ~/Elson-TB2 && git pull origin main

# 2. Generate curriculum manifests
python scripts/curriculum_sampler.py --phase all --target-records 15000

# 3. Start H100
gcloud compute instances start elson-h100-spot --zone=us-central1-a

# 4. SSH into H100
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# 5. Run training (on H100)
cd ~/Elson-TB2 && git pull origin main
./scripts/train-curriculum-h100.sh

# 6. Stop H100 when done (SAVES MONEY!)
exit
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
```

### Check VM Status

```bash
gcloud compute instances list --filter="name~elson"
```

### Check GCS Models

```bash
gsutil ls gs://elson-33a95-elson-models/
```

---

## Model Locations (GCS)

| Model | Path | Status |
|-------|------|--------|
| Base Model | `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/` | Ready |
| DoRA v2 | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` | **PRODUCTION** |
| Curriculum DoRA | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/` | After training |

---

## Training Method: 3-Phase Curriculum

```
Phase A: Domain Blocks     → 35% easy, 35% medium, 25% hard, 5% extreme
Phase B: Mixed Curriculum  → 20% easy, 40% medium, 30% hard, 10% extreme
Phase C: Stress Epoch      → 10% easy, 25% medium, 35% hard, 30% extreme
```

See [CURRICULUM.md](CURRICULUM.md) for full details.

---

## Session Checklist

### Starting a Session

- [ ] `cd ~/Elson-TB2 && git pull origin main`
- [ ] Check this README for current status
- [ ] Check [COMMANDS.md](COMMANDS.md) for needed commands

### Ending a Session

- [ ] Stop all GPU VMs (H100, L4)
- [ ] Verify models uploaded to GCS
- [ ] Note any issues in troubleshooting

---

## Emergency Commands

```bash
# Stop all Elson VMs immediately
gcloud compute instances stop elson-h100-spot --zone=us-central1-a
gcloud compute instances stop elson-dvora-training-l4 --zone=us-east1-b
gcloud compute instances stop elson-dvora-training-l4-2 --zone=us-west1-a

# Check running VMs
gcloud compute instances list --filter="status=RUNNING"

# Check costs
gcloud billing accounts list
```

---

*Always pull latest before starting: `cd ~/Elson-TB2 && git pull origin main`*
