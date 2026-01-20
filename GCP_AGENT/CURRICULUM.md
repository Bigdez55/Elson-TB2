# Curriculum Training Method

**Purpose:** Detailed explanation of the 3-phase curriculum learning approach

---

## Why Curriculum Learning?

Traditional "flat" training feeds all data randomly to the model. Curriculum learning is better because:

| Aspect | Flat Training | Curriculum Training |
|--------|--------------|---------------------|
| **Learning progression** | Random difficulty | Easy → Hard |
| **Domain coverage** | Unbalanced | Guaranteed per-domain competence |
| **Convergence** | Often unstable | Smoother, more stable |
| **Edge case handling** | Undertrained | Explicitly stress-tested |
| **Cross-domain reasoning** | Accidental | Explicitly trained |

---

## The 3-Phase Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   PHASE A ──────────────▶ PHASE B ──────────────▶ PHASE C                   │
│                                                                              │
│   Domain Blocks          Mixed Curriculum         Stress Epoch              │
│   (Build foundation)     (Generalize)             (Harden)                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase A: Domain Blocks

### Purpose
Build domain-specific competence by training one domain at a time.

### Method
- Train sequentially through each domain
- Ensure minimum competence in each before moving on
- Heavy emphasis on easy and medium difficulty

### Difficulty Distribution

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   Easy: 35%    │   Medium: 35%   │   Hard: 25%   │ Extreme: 5% │
│   ████████████ │   ████████████  │   ████████    │ ██          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### What Model Learns
- Basic concepts in each financial domain
- Domain-specific terminology
- Fundamental Q&A patterns
- Correct response formats

### Example Domains
- retirement_planning (401k, IRA basics)
- federal_income_tax (tax brackets, deductions)
- estate_planning (wills, trusts basics)
- banking (account types, interest)
- insurance (policy types, coverage)

---

## Phase B: Mixed Curriculum

### Purpose
Force cross-domain generalization by mixing all domains together.

### Method
- Shuffle examples from all domains
- Cap any single domain at 15% of batch
- Increase difficulty level
- Force model to context-switch

### Difficulty Distribution

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   Easy: 20%  │   Medium: 40%    │   Hard: 30%    │ Extreme: 10%│
│   ████████   │   ████████████████│   ████████████ │ ████        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### What Model Learns
- Cross-domain connections
- Transfer learning between domains
- Handling mixed-topic questions
- Not overfitting to any single domain

### Domain Cap Rule
No domain can exceed 15% of training examples in Phase B.

Why? Prevents the model from:
- Over-indexing on common domains
- Forgetting rare but important domains
- Losing generalization ability

---

## Phase C: Stress Epoch

### Purpose
Harden the model against edge cases and complex scenarios.

### Method
- Heavy emphasis on hard and extremely complex examples
- Focus on high-risk domains (compliance, securities, etc.)
- Multi-domain scenarios
- Compliance-heavy content

### Difficulty Distribution

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   Easy: 10% │   Medium: 25%   │   Hard: 35%      │ Extreme: 30%│
│   ████      │   ██████████    │   ██████████████ │ ████████████│
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Focus Domains (High-Risk)
- compliance
- securities_regulation
- aml_kyc
- federal_income_tax
- insurance
- derivatives
- estate_planning
- trade_execution

### What Model Learns
- Robust edge case handling
- Compliance awareness
- Multi-step complex reasoning
- Professional-grade responses
- When to refuse or escalate

---

## Difficulty Tiers Explained

### Easy
- Single concept questions
- Direct, factual answers
- No multi-step reasoning required

**Example:**
```
Q: What is a 401(k)?
A: A 401(k) is an employer-sponsored retirement savings plan that allows
   employees to contribute a portion of their salary on a pre-tax basis.
```

### Medium
- Multiple concepts combined
- Some reasoning required
- Comparison or analysis needed

**Example:**
```
Q: Compare Roth IRA vs Traditional IRA for a 35-year-old earning $80,000.
A: For a 35-year-old at $80K income, consider...
   - Current tax bracket vs expected retirement bracket
   - Time horizon (30 years to grow tax-free in Roth)
   - Income limits (Roth phases out at $153K single)
   ...
```

### Hard
- Complex scenarios
- Multi-step reasoning
- Professional-level advice
- Multiple domains involved

**Example:**
```
Q: Design a tax-efficient withdrawal strategy for a 65-year-old retiree with
   $500K in Traditional IRA, $300K in Roth IRA, and $200K in taxable brokerage.
A: The optimal withdrawal sequence considers...
   1. Tax bracket management
   2. Required Minimum Distributions starting at 73
   3. Roth conversion opportunities
   ...
```

### Extremely Complex
- Edge cases
- Multi-domain integration
- Compliance-heavy
- High-stakes decisions

**Example:**
```
Q: Structure a GRAT for a business owner with $50M estate, considering
   GST tax, state estate taxes in California, and business succession
   planning. The owner has three children, one of whom works in the business.
A: This requires coordination across estate planning, tax law, business
   succession, and family dynamics...
```

---

## Phase Continuity

Training is **continuous across phases**:

```
Phase A checkpoint
       │
       └──▶ Load checkpoint, continue training
       │
Phase B checkpoint
       │
       └──▶ Load checkpoint, continue training
       │
Phase C FINAL MODEL
```

The model:
1. Preserves learning from previous phases
2. Adds new capabilities in each phase
3. Doesn't "forget" earlier training

---

## Curriculum Sampler Configuration

### Default Phase A Config
```python
PhaseAConfig(
    tier_mix={
        "easy": 0.35,
        "medium": 0.35,
        "hard": 0.25,
        "extremely_complex": 0.05,
    },
    domain_quota=1000,  # Examples per domain
)
```

### Default Phase B Config
```python
PhaseBConfig(
    tier_mix={
        "easy": 0.20,
        "medium": 0.40,
        "hard": 0.30,
        "extremely_complex": 0.10,
    },
    domain_cap=0.15,  # Max 15% per domain
    target_records=10000,
)
```

### Default Phase C Config
```python
PhaseCConfig(
    tier_mix={
        "easy": 0.10,
        "medium": 0.25,
        "hard": 0.35,
        "extremely_complex": 0.30,
    },
    extreme_ratio=0.30,
    focus_multi_domain=True,
    focus_compliance=True,
    target_records=5000,
)
```

---

## Running Curriculum Training

### Generate Manifests

```bash
# All phases at once
python scripts/curriculum_sampler.py --phase all --target-records 15000

# Individual phases
python scripts/curriculum_sampler.py --phase A --target-records 5000
python scripts/curriculum_sampler.py --phase B --target-records 10000
python scripts/curriculum_sampler.py --phase C --target-records 5000
```

### Output Files

```
backend/training_data/curriculum_runs/
├── manifest_phaseA_YYYYMMDD_HHMMSS.jsonl   # Phase A manifest
├── manifest_phaseB_YYYYMMDD_HHMMSS.jsonl   # Phase B manifest
├── manifest_phaseC_YYYYMMDD_HHMMSS.jsonl   # Phase C manifest
├── merged_phaseA_YYYYMMDD_HHMMSS.jsonl     # Phase A training data
├── merged_phaseB_YYYYMMDD_HHMMSS.jsonl     # Phase B training data
├── merged_phaseC_YYYYMMDD_HHMMSS.jsonl     # Phase C training data
├── manifest_stats_phaseA_YYYYMMDD_HHMMSS.json   # Phase A stats
├── manifest_stats_phaseB_YYYYMMDD_HHMMSS.json   # Phase B stats
└── manifest_stats_phaseC_YYYYMMDD_HHMMSS.json   # Phase C stats
```

### Run Training

```bash
./scripts/train-curriculum-h100.sh
```

---

## Expected Training Results

### Loss Progression

| Phase | Start Loss | End Loss | Notes |
|-------|-----------|----------|-------|
| A | ~1.5-2.0 | ~0.8-1.0 | Domain competence |
| B | ~0.8-1.0 | ~0.5-0.7 | Generalization |
| C | ~0.5-0.7 | ~0.3-0.5 | Robustness |

### Time Estimates (H100)

| Phase | Samples | Time |
|-------|---------|------|
| A | ~5,000 | ~15-20 min |
| B | ~10,000 | ~20-25 min |
| C | ~5,000 | ~10-15 min |
| **Total** | **~20,000** | **~45-60 min** |

---

*Last Updated: 2026-01-19*
