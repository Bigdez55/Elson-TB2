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

### Session 6: Curriculum Training v4 - Full Scale (2026-01-21) ✅ COMPLETE

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-21 |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | DoRA (3-Phase Curriculum) |
| **GPU** | H100 80GB HBM3 |
| **VM** | elson-h100-spot |

**Training Data:**
| Phase | Examples | Difficulty Mix |
|-------|----------|----------------|
| A | 21,356 | 35% easy, 35% medium, 25% hard, 5% extreme |
| B | 12,854 | 20% easy, 40% medium, 30% hard, 10% extreme |
| C | 11,927 | 10% easy, 25% medium, 35% hard, 30% extreme |
| **Total** | **46,137** | Curriculum progression |

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

**Training Results:**
| Phase | Final Loss | Steps | Time |
|-------|-----------|-------|------|
| A (Domain Blocks) | 0.6980 | 50 | ~95 min |
| B (Mixed Curriculum) | 0.2706 | 34 | ~65 min |
| C (Stress Epoch) | 0.1622 | 34 | ~65 min |
| **Total** | **0.1622** | **118** | **~225 min (~3.75 hrs)** |

**Inference Test Results (on H100):**
| Domain | Latency | Response Quality |
|--------|---------|-----------------|
| retirement_planning | 81.55s | Excellent - comprehensive 401k explanation with key features |
| federal_income_tax | 25.17s | Good - clear standard vs itemized deduction comparison |
| estate_planning | 14.66s | Good - concise revocable living trust explanation |
| investment | 27.01s | Excellent - DCA explanation with behavioral insight |
| compliance | 22.02s | Good - clear fiduciary duty definition |

**Difficulties Encountered:**
- TRL 0.27.0 API breaking change: `max_length`, `dataset_text_field`, `packing` moved from `SFTTrainer` to `SFTConfig`
- Required replacing `TrainingArguments` with `SFTConfig` from trl
- Local changes on VM required `git stash` before pull
- Flash attention warnings (non-blocking but recommend flash_attention_2)

**Areas for Improvement:**
- Enable flash_attention_2 for better packing support and faster training
- Inference latency still high (14-82s) - consider quantization or vLLM optimization
- Loss progression excellent: 0.698 → 0.271 → 0.162 (6.4x larger dataset than v3)
- Consider increasing Phase A data (domain blocks) for even stronger foundation

**Output Model:** `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/`
**Model Size:** 2.07 GB
**Training Cost:** ~$9.40 (3.75 hrs × $2.50/hr H100 Spot)

---

### Session 5: Curriculum Training v3 (2026-01-20) ✅ COMPLETE

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-01-20 |
| **Model** | Elson-Finance-Trading-14B |
| **Method** | DoRA (3-Phase Curriculum) |
| **GPU** | H100 80GB HBM3 |
| **VM** | elson-h100-spot |

**Training Data:**
| Phase | Examples | Difficulty Mix |
|-------|----------|----------------|
| A | 389 | 35% easy, 35% medium, 25% hard, 5% extreme |
| B | 4,809 | 20% easy, 40% medium, 30% hard, 10% extreme |
| C | 2,000 | 10% easy, 25% medium, 35% hard, 30% extreme |
| **Total** | **7,198** | Curriculum progression |

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

**Training Results:**
| Phase | Final Loss | Steps | Time |
|-------|-----------|-------|------|
| A (Domain Blocks) | 1.8475 | 2 | ~3 min |
| B (Mixed Curriculum) | 1.0533 | 14 | ~25 min |
| C (Stress Epoch) | 0.7560 | 8 | ~14 min |
| **Total** | **0.7560** | **24** | **~42 min** |

**Inference Test Results (on H100):**
| Domain | Latency | Response Quality |
|--------|---------|-----------------|
| retirement_planning | 91.99s | Good - comprehensive 401k explanation |
| federal_income_tax | 31.62s | Good - clear deduction comparison |
| estate_planning | 43.54s | Good - trust explanation with key details |
| investment | 14.21s | Concise - dollar-cost averaging definition |
| compliance | 11.01s | Brief but accurate fiduciary definition |

**Difficulties Encountered:**
- `autoawq` package conflict with transformers 4.57.6 (PytorchGELUTanh removed) - uninstalled autoawq
- `trl` 0.27.0 API changes: `tokenizer`→`processing_class`, `max_seq_length`→`max_length`
- OOM errors with batch_size=16 - reduced to 4 with grad_accum=16
- Disk 100% full - had to delete `/home/bigdez55/models/` (51GB merge models)
- `torch`/`torchvision` version mismatch - reinstalled compatible versions

**Areas for Improvement:**
- Consider using flash_attention_2 for better packing support
- Inference latency high on H100 (91s for first query) - needs optimization
- Loss progression: 1.85 → 1.05 → 0.76 shows curriculum working but could target lower
- Phase A only had 389 examples - consider larger domain block sampling

**Output Model:** `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/`
**Commit Hash:** `79d4103`

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
| wealth-dora-v4-curriculum | DoRA Curriculum | 46,137 | 0.1622 | 225 min | H100 |
| wealth-dora-v3-curriculum | DoRA Curriculum | 7,198 | 0.7560 | 42 min | H100 |
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
| DoRA v3 Curriculum | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100-v3-curriculum/` | 2.07 GB | Production |
| LoRA v1 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm1/` | ~96 MB | Archive |
| LoRA v2 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm2/` | ~96 MB | Archive |

---

## Training Cost Tracking

| Session | GPU | Duration | Cost |
|---------|-----|----------|------|
| Session 6 (Curriculum v4) | H100 Spot | ~225 min | ~$9.40 |
| Session 5 (Curriculum v3) | H100 Spot | ~42 min | ~$1.75 |
| Session 4 (DoRA v2) | H100 Spot | ~6 min | ~$0.25 |
| Session 3 (LoRA v2) | L4 | ~25 min | ~$0.30 |
| Session 2 (LoRA v1) | L4 | ~24 min | ~$0.28 |
| **Total** | | | ~$11.98 |

---

*Last Updated: 2026-01-21*
