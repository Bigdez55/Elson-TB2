# Training Data Structure

**Purpose:** Complete documentation of training data organization for the GCP Agent

---

## Overview

| Metric | Value |
|--------|-------|
| **Total Q&A Pairs** | 40,993+ |
| **Domain Buckets** | 80+ |
| **Difficulty Tiers** | 4 (easy, medium, hard, extremely_complex) |
| **Training Approach** | 3-Phase Curriculum |

---

## Directory Structure

```
backend/training_data/
├── domain_buckets/                    # Main training data (per domain)
│   ├── retirement_planning/
│   │   ├── easy.jsonl
│   │   ├── medium.jsonl
│   │   ├── hard.jsonl
│   │   └── extremely_complex.jsonl
│   ├── federal_income_tax/
│   │   ├── easy.jsonl
│   │   ├── medium.jsonl
│   │   ├── hard.jsonl
│   │   └── extremely_complex.jsonl
│   ├── estate_planning/
│   │   └── ...
│   └── [80+ domain directories]
│
├── curriculum_runs/                   # Generated curriculum manifests
│   ├── manifest_phaseA_YYYYMMDD_HHMMSS.jsonl
│   ├── manifest_phaseB_YYYYMMDD_HHMMSS.jsonl
│   ├── manifest_phaseC_YYYYMMDD_HHMMSS.jsonl
│   ├── merged_phaseA_YYYYMMDD_HHMMSS.jsonl
│   ├── merged_phaseB_YYYYMMDD_HHMMSS.jsonl
│   ├── merged_phaseC_YYYYMMDD_HHMMSS.jsonl
│   └── manifest_stats_phase*_YYYYMMDD_HHMMSS.json
│
├── consolidated_training_data.json    # Legacy flat training data
├── strategic_qa_pairs.json            # Extracted from strategic docs
└── evaluation_benchmark.json          # 100 test cases
```

---

## Domain Buckets

### What is a Domain Bucket?

A domain bucket is a directory containing training data for a single financial domain, organized by difficulty tier.

```
domain_buckets/
└── federal_income_tax/          # Domain name
    ├── easy.jsonl               # Tier 1: Basic concepts
    ├── medium.jsonl             # Tier 2: Multi-concept
    ├── hard.jsonl               # Tier 3: Complex scenarios
    └── extremely_complex.jsonl  # Tier 4: Edge cases, multi-domain
```

### Domain Categories (80+)

| Category | Example Domains |
|----------|-----------------|
| **Tax** | federal_income_tax, state_income_tax, estate_tax, gift_tax |
| **Retirement** | retirement_planning, 401k, ira, roth_ira, pension |
| **Estate** | estate_planning, trusts, wills, probate |
| **Insurance** | life_insurance, health_insurance, property_insurance |
| **Banking** | banking, lending, credit, mortgages |
| **Investment** | portfolio_management, asset_allocation, securities |
| **Compliance** | aml_kyc, securities_regulation, fiduciary |
| **Markets** | stock_market, derivatives, fixed_income |
| **Professional** | professional_roles, certifications, credentials |
| **Family Office** | family_governance, succession_planning, wealth_transfer |

### Full Domain List

```
aml_kyc
asset_allocation
banking
behavioral_finance
business_succession
capital_markets
charitable_giving
college_planning
compliance
corporate_finance
credit
derivatives
disability_planning
elder_care
emergency_fund
estate_planning
estate_tax
exchange_traded_funds
family_governance
federal_income_tax
fiduciary
financial_planning
fixed_income
gift_tax
goal_planning
health_insurance
hedge_funds
high_net_worth
income_planning
insurance
international_tax
investment_management
ira
lending
life_insurance
long_term_care
mortgages
municipal_bonds
mutual_funds
pension
portfolio_management
private_banking
probate
professional_roles
property_insurance
real_estate
retirement_planning
risk_management
roth_ira
securities
securities_regulation
social_security
state_income_tax
stock_market
succession_planning
tax_optimization
tax_planning
trade_execution
trust_administration
trusts
wealth_management
wealth_transfer
wills
... and more
```

---

## Difficulty Tiers

### Tier Definitions

| Tier | File | Description | Training Weight |
|------|------|-------------|-----------------|
| **Easy** | easy.jsonl | Single concept, factual | 35% (Phase A) |
| **Medium** | medium.jsonl | Multi-concept, reasoning | 40% (Phase B) |
| **Hard** | hard.jsonl | Complex scenarios, professional | 35% (Phase C) |
| **Extremely Complex** | extremely_complex.jsonl | Edge cases, multi-domain | 30% (Phase C) |

### Tier Examples

**Easy (Tier 1):**
```json
{
  "instruction": "What is a 401(k)?",
  "input": "",
  "output": "A 401(k) is an employer-sponsored retirement savings plan that allows employees to contribute a portion of their salary on a pre-tax basis. Contributions and investment gains grow tax-deferred until withdrawal in retirement.",
  "domain": "retirement_planning",
  "tier": "easy"
}
```

**Medium (Tier 2):**
```json
{
  "instruction": "Compare Roth IRA vs Traditional IRA for a 35-year-old earning $80,000.",
  "input": "",
  "output": "For a 35-year-old earning $80K:\n\n1. Traditional IRA: Tax deduction now (~$1,500 saved at 22% bracket), taxed at withdrawal\n2. Roth IRA: No deduction now, but tax-free withdrawals in retirement\n\nKey factors:\n- 30 years of tax-free growth in Roth is valuable\n- Current income below Roth phase-out ($153K single)\n- If expecting higher taxes in retirement, Roth preferred\n\nRecommendation: Roth IRA likely better given time horizon.",
  "domain": "retirement_planning",
  "tier": "medium"
}
```

**Hard (Tier 3):**
```json
{
  "instruction": "Design a tax-efficient withdrawal strategy for a 65-year-old retiree with $500K Traditional IRA, $300K Roth IRA, and $200K taxable brokerage.",
  "input": "",
  "output": "Optimal withdrawal strategy:\n\n1. **Years 65-72 (Before RMDs):**\n   - Withdraw from taxable brokerage first (LTCG rates lower)\n   - Consider Roth conversions to fill lower tax brackets\n   - Keep Traditional IRA growing tax-deferred\n\n2. **Years 73+ (RMD Phase):**\n   - Take Required Minimum Distributions from Traditional IRA\n   - Use Roth for large expenses (tax-free)\n   - Coordinate with Social Security timing\n\n3. **Tax Bracket Management:**\n   - Stay in 12% or 22% bracket if possible\n   - Convert to Roth during low-income years\n   - Consider IRMAA thresholds for Medicare\n\nThis sequence minimizes lifetime tax burden.",
  "domain": "retirement_planning",
  "tier": "hard"
}
```

**Extremely Complex (Tier 4):**
```json
{
  "instruction": "Structure a GRAT for a business owner with $50M estate, considering GST tax, state estate taxes in California, and business succession planning. The owner has three children, one of whom works in the business.",
  "input": "",
  "output": "Comprehensive GRAT Strategy:\n\n1. **GRAT Structure:**\n   - 2-year rolling GRATs (minimize mortality risk)\n   - Transfer business interest at discount (30-35% for lack of control/marketability)\n   - Annuity rate: Slightly above 7520 rate (currently ~5.4%)\n\n2. **GST Planning:**\n   - GRAT is NOT an effective GST planning tool (ETIP rules)\n   - Use separate GST exemption allocation for dynasty trust\n   - Consider SLATs for spouse for additional GST planning\n\n3. **California Considerations:**\n   - No state estate tax, but consider income tax on sale\n   - IRC 1202 QSBS exclusion if applicable (up to $10M)\n   - Consider incomplete gift non-grantor trust (ING) for income tax\n\n4. **Business Succession:**\n   - GRAT remainder to spray trust for all three children\n   - Business-active child: Voting interests, management role\n   - Non-active children: Non-voting interests, equal economics\n   - Buy-sell agreement with life insurance funding\n\n5. **Implementation:**\n   - Qualified appraisal required (IRS scrutiny high)\n   - File gift tax return disclosing GRAT\n   - Annual compliance: Annuity payments, trust accounting\n\n**Risk Factors:** 7520 rate volatility, IRS audit, business valuation challenges.",
  "domain": "estate_planning",
  "tier": "extremely_complex"
}
```

---

## JSONL Format

All training data uses JSONL (JSON Lines) format:

```jsonl
{"instruction": "...", "input": "", "output": "...", "domain": "...", "tier": "..."}
{"instruction": "...", "input": "", "output": "...", "domain": "...", "tier": "..."}
{"instruction": "...", "input": "", "output": "...", "domain": "...", "tier": "..."}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `instruction` | string | The question/prompt |
| `input` | string | Optional context (usually empty) |
| `output` | string | The model's response |
| `domain` | string | Domain category |
| `tier` | string | Difficulty tier |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `subdomain` | string | More specific categorization |
| `source` | string | Data source identifier |
| `authority_tier` | string | primary/secondary/tertiary |
| `jurisdiction` | string | US, State, Global |

---

## Curriculum Manifests

### What are Manifests?

Manifests are the sampling specifications generated by `curriculum_sampler.py`. They specify which records to use for each training phase.

### Manifest Files

| File | Purpose |
|------|---------|
| `manifest_phaseA_*.jsonl` | Phase A sampling spec (domain blocks) |
| `manifest_phaseB_*.jsonl` | Phase B sampling spec (mixed) |
| `manifest_phaseC_*.jsonl` | Phase C sampling spec (stress) |
| `merged_phaseA_*.jsonl` | Actual training data for Phase A |
| `merged_phaseB_*.jsonl` | Actual training data for Phase B |
| `merged_phaseC_*.jsonl` | Actual training data for Phase C |
| `manifest_stats_*.json` | Sampling statistics |

### Manifest Format

```json
{
  "domain": "federal_income_tax",
  "tier": "medium",
  "source_file": "backend/training_data/domain_buckets/federal_income_tax/medium.jsonl",
  "record_index": 42,
  "phase": "A"
}
```

### Stats File Format

```json
{
  "phase": "A",
  "timestamp": "2026-01-19T12:34:56",
  "total_records": 5000,
  "tier_distribution": {
    "easy": 1750,
    "medium": 1750,
    "hard": 1250,
    "extremely_complex": 250
  },
  "domain_distribution": {
    "federal_income_tax": 312,
    "retirement_planning": 298,
    "estate_planning": 285,
    ...
  }
}
```

---

## Generating Training Data

### Generate Curriculum Manifests

```bash
# Generate all phases at once (recommended)
python scripts/curriculum_sampler.py --phase all --target-records 15000

# Generate individual phases
python scripts/curriculum_sampler.py --phase A --target-records 5000
python scripts/curriculum_sampler.py --phase B --target-records 10000
python scripts/curriculum_sampler.py --phase C --target-records 5000
```

### Verify Training Data

```bash
# Count domain buckets
ls backend/training_data/domain_buckets/ | wc -l

# Count total files
find backend/training_data/domain_buckets -name "*.jsonl" | wc -l

# Check records per tier (example for one domain)
wc -l backend/training_data/domain_buckets/federal_income_tax/*.jsonl

# Validate JSONL format
head -1 backend/training_data/domain_buckets/federal_income_tax/easy.jsonl | python -m json.tool
```

---

## Phase-Specific Data Requirements

### Phase A: Domain Blocks

- **Purpose:** Build domain-specific competence
- **Tier Mix:** 35% easy, 35% medium, 25% hard, 5% extreme
- **Target:** ~5,000 records
- **Key Rule:** Train sequentially through each domain

### Phase B: Mixed Curriculum

- **Purpose:** Cross-domain generalization
- **Tier Mix:** 20% easy, 40% medium, 30% hard, 10% extreme
- **Target:** ~10,000 records
- **Key Rule:** No single domain > 15% of batch

### Phase C: Stress Epoch

- **Purpose:** Harden against edge cases
- **Tier Mix:** 10% easy, 25% medium, 35% hard, 30% extreme
- **Target:** ~5,000 records
- **Focus Domains:** compliance, securities_regulation, aml_kyc, federal_income_tax

---

## Adding New Training Data

### Step 1: Create Domain Bucket

```bash
mkdir -p backend/training_data/domain_buckets/NEW_DOMAIN
touch backend/training_data/domain_buckets/NEW_DOMAIN/easy.jsonl
touch backend/training_data/domain_buckets/NEW_DOMAIN/medium.jsonl
touch backend/training_data/domain_buckets/NEW_DOMAIN/hard.jsonl
touch backend/training_data/domain_buckets/NEW_DOMAIN/extremely_complex.jsonl
```

### Step 2: Add JSONL Records

```bash
# Append to the appropriate tier file
echo '{"instruction": "What is...?", "input": "", "output": "...", "domain": "NEW_DOMAIN", "tier": "easy"}' >> backend/training_data/domain_buckets/NEW_DOMAIN/easy.jsonl
```

### Step 3: Validate

```bash
# Check format
python -m json.tool < backend/training_data/domain_buckets/NEW_DOMAIN/easy.jsonl

# Count records
wc -l backend/training_data/domain_buckets/NEW_DOMAIN/*.jsonl
```

### Step 4: Regenerate Manifests

```bash
python scripts/curriculum_sampler.py --phase all --target-records 15000
```

---

## Legacy Data Files

These files exist for backwards compatibility but curriculum training uses domain buckets:

| File | Purpose | Records |
|------|---------|---------|
| `consolidated_training_data.json` | Original flat training set | ~23,493 |
| `strategic_qa_pairs.json` | Extracted from strategic docs | ~205 |
| `evaluation_benchmark.json` | Test evaluation set | 100 |

**Note:** The curriculum sampler reads from domain_buckets/, not these legacy files.

---

## Data Quality Guidelines

### Do's

- Use clear, professional language
- Include specific numbers and examples
- Cite relevant regulations (IRC sections, CFR)
- Cover edge cases in "extremely_complex" tier
- Balance domains (no single domain > 20% of total)

### Don'ts

- No generic "it depends" answers
- No personal financial advice without context
- No outdated information (check tax year, contribution limits)
- No overly promotional content
- No duplicate Q&A pairs across tiers

---

## Useful Commands

```bash
# Count all training records
find backend/training_data/domain_buckets -name "*.jsonl" -exec wc -l {} + | tail -1

# Find domains with most data
for d in backend/training_data/domain_buckets/*/; do
  echo "$(find $d -name "*.jsonl" -exec wc -l {} + | tail -1 | awk '{print $1}') $(basename $d)"
done | sort -rn | head -20

# Find domains with least data
for d in backend/training_data/domain_buckets/*/; do
  echo "$(find $d -name "*.jsonl" -exec wc -l {} + | tail -1 | awk '{print $1}') $(basename $d)"
done | sort -n | head -20

# Check tier balance for a domain
wc -l backend/training_data/domain_buckets/retirement_planning/*.jsonl

# Validate all JSONL files
find backend/training_data/domain_buckets -name "*.jsonl" -exec sh -c 'python -m json.tool < {} > /dev/null || echo "Invalid: {}"' \;
```

---

*Last Updated: 2026-01-19*
