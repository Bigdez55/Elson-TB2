# Training Benchmark Log

**Purpose:** Track all model training sessions, results, and comparisons

> **IMPORTANT:** This log MUST be updated after EVERY training session.
> See [TRAINING.md](TRAINING.md) for the mandatory post-training protocol.

---

## How to Log a Training Session

After every training session, add an entry using this template:

```markdown
### Session X: [Model Name] (YYYY-MM-DD)

| Attribute | Value |
|-----------|-------|
| **Date** | YYYY-MM-DD |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | DoRA / LoRA / etc |
| **GPU** | H100 / L4 |
| **VM** | elson-h100-spot |

**Training Results:**
| Phase | Final Loss | Steps | Time |
|-------|-----------|-------|------|
| A | X.XXX | XX | XX min |
| B | X.XXX | XX | XX min |
| C | X.XXX | XX | XX min |

**Inference Test Results:**
| Domain | Latency | Quality (1-5) |
|--------|---------|---------------|
| retirement_planning | X.Xs | X |
| federal_income_tax | X.Xs | X |
| estate_planning | X.Xs | X |
| investment | X.Xs | X |
| compliance | X.Xs | X |

**Difficulties Encountered:**
- [List any errors, package issues, OOM, etc.]

**Areas for Improvement:**
- [Hyperparameter suggestions, data quality notes, etc.]

**Output Model:** `model-name`
**Commit Hash:** `abc1234`
```

---

## Training Sessions

### Session 5: Curriculum Training v3 (2026-01-19)

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-19 |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | DoRA (3-Phase Curriculum) |
| **GPU** | H100 80GB |
| **VM** | elson-h100-spot |

**Training Data:**
| Phase | Examples | Difficulty Mix |
|-------|----------|----------------|
| A | ~5,000 | 35% easy, 35% medium, 25% hard, 5% extreme |
| B | 4,809 | 20% easy, 40% medium, 30% hard, 10% extreme |
| C | ~5,000 | 10% easy, 25% medium, 35% hard, 30% extreme |
| **Total** | ~15,000 | Curriculum progression |

**Hyperparameters:**
| Parameter | Value |
|-----------|-------|
| Rank (r) | 128 |
| Alpha | 256 |
| Batch Size | 4 |
| Grad Accum | 16 |
| Effective Batch | 64 |
| Epochs/Phase | 2 |
| Learning Rate | 2e-4 |
| Max Length | 2048 |

**Results:**
| Metric | Phase A | Phase B | Phase C |
|--------|---------|---------|---------|
| Final Loss | TBD | TBD | TBD |
| Training Time | TBD | TBD | TBD |
| Steps | TBD | 14 | TBD |

**Output Model:** `wealth-dora-elson14b-h100-v3-curriculum`

**Notes:**
- Fixed trl 0.27.0 compatibility (processing_class, max_length)
- Reduced batch size from 16→4 to prevent OOM
- First curriculum training run with 3-phase approach

---

### Session 4: DoRA v2 (2026-01-17)

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-17 |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | DoRA (Flat Training) |
| **GPU** | H100 80GB |
| **VM** | elson-h100-spot |

**Training Data:**
| Source | Examples |
|--------|----------|
| consolidated_training_data.json | 408 |

**Hyperparameters:**
| Parameter | Value |
|-----------|-------|
| Rank (r) | 64 |
| Alpha | 128 |
| Batch Size | 8 |
| Epochs | 3 |

**Results:**
| Metric | Value |
|--------|-------|
| Final Loss | 0.14 |
| Training Time | ~6 min |

**Output Model:** `wealth-dora-elson14b-h100-v2`

**Notes:**
- First successful H100 DoRA training
- 4x faster than L4 LoRA training

---

### Session 3: LoRA v2 (2026-01-16)

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-16 |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | 4-bit LoRA |
| **GPU** | L4 24GB |
| **VM** | elson-dvora-training-l4-2 |

**Training Data:**
| Source | Examples |
|--------|----------|
| training_data_final.json | 377 |

**Hyperparameters:**
| Parameter | Value |
|-----------|-------|
| Rank (r) | 16 |
| Alpha | 32 |
| Batch Size | 2-4 |
| Epochs | 3 |

**Results:**
| Metric | Value |
|--------|-------|
| Final Loss | 0.0532 |
| Training Time | ~25.1 min |

**Output Model:** `wealth-lora-elson14b-vm2`

---

### Session 2: LoRA v1 (2026-01-15)

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-15 |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | 4-bit LoRA |
| **GPU** | L4 24GB |
| **VM** | elson-dvora-training-l4 |

**Training Data:**
| Source | Examples |
|--------|----------|
| training_data_final.json | 377 |

**Hyperparameters:**
| Parameter | Value |
|-----------|-------|
| Rank (r) | 16 |
| Alpha | 32 |
| Batch Size | 2-4 |
| Epochs | 3 |

**Results:**
| Metric | Value |
|--------|-------|
| Final Loss | 0.0526 |
| Training Time | ~23.5 min |

**Output Model:** `wealth-lora-elson14b-vm1`

---

### Session 1: Base Model Merge (2026-01-14)

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-14 |
| **Method** | MergeKit SLERP |
| **Output Size** | 27.52 GB |

**Merged Models:**
- Qwen2.5-14B-Instruct (base)
- Financial domain models
- Trading knowledge models

**Output Model:** `elson-finance-trading-14b-final`

**Notes:**
- 6 SafeTensor shards
- Custom tokenizer
- bfloat16 precision

---

## Model Comparison

| Model | Method | Data | Loss | Time | GPU |
|-------|--------|------|------|------|-----|
| wealth-dora-v3-curriculum | DoRA Curriculum | 15,000 | TBD | TBD | H100 |
| wealth-dora-v2 | DoRA Flat | 408 | 0.14 | 6 min | H100 |
| wealth-lora-vm2 | 4-bit LoRA | 377 | 0.0532 | 25 min | L4 |
| wealth-lora-vm1 | 4-bit LoRA | 377 | 0.0526 | 24 min | L4 |

---

## Benchmark Evaluation Results

### Evaluation Benchmark (100 Questions)

| Model | Accuracy | Avg Latency | Notes |
|-------|----------|-------------|-------|
| wealth-dora-v3-curriculum | TBD | TBD | Pending |
| wealth-dora-v2 | ~80% | TBD | Baseline |
| wealth-lora-vm1 | ~75% | TBD | Lower rank |

---

## GCS Model Registry

| Model | Path | Size | Status |
|-------|------|------|--------|
| Base Model | `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/` | 27.52 GB | Production |
| DoRA v2 | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v2/` | ~500 MB | Production |
| DoRA v3 Curriculum | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/` | ~500 MB | Training |
| LoRA v1 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm1/` | ~96 MB | Archive |
| LoRA v2 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm2/` | ~96 MB | Archive |

---

## Training Cost Tracking

| Session | GPU | Duration | Cost |
|---------|-----|----------|------|
| Session 5 (Curriculum v3) | H100 Spot | ~90 min | ~$3.75 |
| Session 4 (DoRA v2) | H100 Spot | ~6 min | ~$0.25 |
| Session 3 (LoRA v2) | L4 | ~25 min | ~$0.30 |
| Session 2 (LoRA v1) | L4 | ~24 min | ~$0.28 |
| **Total** | | | ~$4.58 |

---

*Last Updated: 2026-01-19*
