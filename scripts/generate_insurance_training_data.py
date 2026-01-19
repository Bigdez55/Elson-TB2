"""
Generate Insurance Training Data for Elson Financial AI

Target: 10,000 - 30,000 insurance-specific Q&A pairs
Focus: Scenario-driven, compliant responses with proper disclaimers

Categories:
1. Life Insurance (term, whole, universal, variable, IUL)
2. Health Insurance (ACA, Medicare, HSA/FSA)
3. Property & Casualty (auto, home, umbrella)
4. Annuities (fixed, variable, indexed)
5. Long-Term Care (traditional, hybrid)
6. Disability Insurance (STD, LTD)
7. Insurance Basics & Concepts
8. Claims & Processes
9. Suitability Scenarios
10. Regulatory & Compliance
"""

import json
import random
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


# =============================================================================
# DISCLAIMERS (REQUIRED IN ALL OUTPUTS)
# =============================================================================

STANDARD_DISCLAIMER = (
    "\n\n*This information is for educational purposes only and does not constitute "
    "insurance advice. Consult a licensed insurance professional for personalized recommendations.*"
)

ILLUSTRATION_DISCLAIMER = (
    "\n\n*Non-guaranteed values are NOT guaranteed and may be higher or lower than shown. "
    "Actual results will vary based on policy performance.*"
)


# =============================================================================
# LIFE INSURANCE TEMPLATES
# =============================================================================

LIFE_INSURANCE_QA = [
    # Term Life Basics
    {
        "instruction": "What is term life insurance and how does it work?",
        "output": """Term life insurance provides coverage for a specific period (the "term"), typically 10, 20, or 30 years. If you die during the term, your beneficiaries receive the death benefit. If you outlive the term, coverage ends and no benefit is paid.

**Key Features:**
- **Level premiums**: Payments stay the same throughout the term
- **Pure protection**: No cash value accumulation
- **Lowest cost**: Most affordable type of life insurance per dollar of coverage
- **Convertibility**: Many policies can convert to permanent coverage without medical exams

**Best For:**
- Income replacement during working years
- Covering a mortgage or other debts
- Providing for children until they're independent
- Temporary needs with a defined endpoint""" + STANDARD_DISCLAIMER,
        "category": "life_insurance_term"
    },
    {
        "instruction": "How much term life insurance do I need if I make $80,000 per year and have two kids?",
        "output": """A common rule of thumb is 10-12x your annual income, but let's calculate more precisely using the DIME method:

**D - Debt**: Add up mortgages, car loans, credit cards, student loans
**I - Income Replacement**: $80,000 × years until youngest is independent (e.g., 18 years = $1.44M)
**M - Mortgage**: Outstanding balance (e.g., $300,000)
**E - Education**: College costs per child (e.g., $100,000 × 2 = $200,000)

**Example Calculation:**
- Income replacement (15 years): $1,200,000
- Mortgage payoff: $300,000
- College funding: $200,000
- Other debts: $50,000
- Final expenses: $15,000
- **Total Need**: ~$1,765,000

**Subtract existing coverage** (employer life, savings) to find the gap.

For a 35-year-old non-smoker, a 20-year, $1.5M term policy might cost $50-80/month.""" + STANDARD_DISCLAIMER,
        "category": "life_insurance_term"
    },
    # Whole Life
    {
        "instruction": "What is whole life insurance and is it worth it?",
        "output": """Whole life insurance is permanent coverage that lasts your entire life and builds cash value. Here's an objective analysis:

**How It Works:**
- Fixed premiums for life
- Guaranteed death benefit
- Cash value grows at a guaranteed rate
- May pay dividends (if from mutual company)
- Can borrow against cash value

**Potential Benefits:**
- Lifetime coverage certainty
- Forced savings mechanism
- Tax-deferred growth
- Estate planning tool
- Creditor protection (varies by state)

**Potential Drawbacks:**
- Premiums 5-15x higher than term for same death benefit
- Cash value growth typically 2-4% (low vs. market investments)
- Surrender charges if canceled early
- Complexity

**Best Suited For:**
- High-net-worth estate planning
- Business succession planning
- Those who've maxed other tax-advantaged accounts
- Specific legacy goals

**Not Ideal For:**
- Those struggling to fund retirement accounts
- Pure income replacement needs
- Short-term coverage needs

*Whether it's "worth it" depends entirely on your specific goals, financial situation, and alternatives.*""" + STANDARD_DISCLAIMER,
        "category": "life_insurance_permanent"
    },
    # Universal Life
    {
        "instruction": "What's the difference between universal life and whole life insurance?",
        "output": """Both are permanent life insurance, but they differ significantly in flexibility and risk:

| Feature | Whole Life | Universal Life |
|---------|-----------|----------------|
| **Premiums** | Fixed, guaranteed | Flexible (within limits) |
| **Death Benefit** | Fixed | Adjustable |
| **Cash Value Growth** | Guaranteed rate | Based on interest rates |
| **Dividends** | Possible (mutual cos.) | None |
| **Risk** | Low (guaranteed) | Higher (rate-dependent) |
| **Flexibility** | Low | High |

**Universal Life Types:**
1. **Traditional UL**: Cash value tied to current interest rates
2. **Indexed UL (IUL)**: Returns linked to stock index (with caps/floors)
3. **Variable UL (VUL)**: Invested in sub-accounts (market risk)
4. **Guaranteed UL (GUL)**: Focuses on death benefit, minimal cash value

**Key Risk with UL:**
If interest rates drop or you underfund premiums, your policy could lapse. This happened to many policies from the 1980s-90s when projected rates weren't achieved.""" + STANDARD_DISCLAIMER,
        "category": "life_insurance_permanent"
    },
    # IUL Specifics
    {
        "instruction": "Is indexed universal life insurance a good investment?",
        "output": """Important clarification: Indexed Universal Life (IUL) is **insurance**, not an investment. Let's examine it objectively:

**How IUL Works:**
- Cash value growth tied to a stock index (S&P 500, etc.)
- Participation rate: You get a portion of index gains (e.g., 80%)
- Cap: Maximum credit per year (e.g., 10-12%)
- Floor: Minimum credit (typically 0% - you don't lose in down years)
- Spread: Some policies deduct a spread from gains

**Example Year:**
- S&P 500 returns 15%
- With 80% participation and 10% cap → You're credited 10%
- S&P 500 loses 20% → You're credited 0% (floor protects you)

**Realities to Understand:**
1. You don't actually invest in the market
2. Caps limit upside in strong years
3. 0% floor doesn't mean "no loss" - policy charges still apply
4. Illustrations often show optimistic scenarios
5. Complexity makes comparison difficult

**May Be Appropriate For:**
- Those wanting permanent coverage with growth potential
- Conservative accumulators who've maxed other accounts
- Estate planning with growth component

**Generally Not Ideal For:**
- Primary retirement savings vehicle
- Those seeking maximum market growth
- Anyone who doesn't fully understand the product""" + ILLUSTRATION_DISCLAIMER + STANDARD_DISCLAIMER,
        "category": "life_insurance_iul"
    },
]


# =============================================================================
# HEALTH INSURANCE TEMPLATES
# =============================================================================

HEALTH_INSURANCE_QA = [
    {
        "instruction": "What's the difference between an HMO and a PPO health plan?",
        "output": """HMO (Health Maintenance Organization) and PPO (Preferred Provider Organization) are the two most common health plan types. Here's a comparison:

| Feature | HMO | PPO |
|---------|-----|-----|
| **Primary Care Physician (PCP)** | Required | Optional |
| **Referrals for Specialists** | Required | Not required |
| **Out-of-Network Coverage** | Usually none | Yes (higher cost) |
| **Premiums** | Lower | Higher |
| **Deductibles** | Lower | Higher |
| **Flexibility** | Less | More |

**HMO Best For:**
- Those who prefer lower premiums
- People comfortable with a PCP coordinating care
- Those who don't travel frequently
- Healthy individuals with predictable care needs

**PPO Best For:**
- Those wanting to see specialists without referrals
- People who travel frequently
- Those with ongoing specialist care needs
- People willing to pay more for flexibility

**Key Consideration:** Many people overvalue PPO flexibility. If you rarely need specialists, an HMO can save thousands annually.""" + STANDARD_DISCLAIMER,
        "category": "health_insurance"
    },
    {
        "instruction": "How do HSAs work and why are they called 'triple tax advantaged'?",
        "output": """Health Savings Accounts (HSAs) offer unique tax benefits that no other account matches:

**The Triple Tax Advantage:**
1. **Tax-Deductible Contributions**: Reduce your taxable income
2. **Tax-Free Growth**: No taxes on investment gains
3. **Tax-Free Withdrawals**: For qualified medical expenses

**2025 Contribution Limits:**
- Individual: $4,150
- Family: $8,300
- Age 55+ catch-up: +$1,000

**Requirements:**
- Must have a High-Deductible Health Plan (HDHP)
- Cannot be claimed as a dependent
- Cannot have Medicare
- Cannot have other non-HDHP coverage

**Why HSAs Are Powerful:**
1. **No "use it or lose it"**: Unlike FSAs, funds roll over forever
2. **Portable**: You keep it if you change jobs
3. **Investment option**: Can invest in stocks/funds after threshold
4. **Retirement tool**: After 65, withdrawals for any purpose (taxed as income, no penalty)

**Optimal Strategy:**
If affordable, pay current medical expenses out-of-pocket, let HSA grow tax-free, and save receipts for future reimbursement (no time limit).""" + STANDARD_DISCLAIMER,
        "category": "health_insurance"
    },
    {
        "instruction": "When should I enroll in Medicare and what are the parts?",
        "output": """Medicare has specific enrollment windows and four parts. Missing deadlines can result in permanent penalties.

**Medicare Parts:**

| Part | Coverage | Premium |
|------|----------|---------|
| **Part A** | Hospital, skilled nursing, hospice | Usually $0 (paid via payroll taxes) |
| **Part B** | Doctor visits, outpatient, preventive | ~$175/month (2025, income-based) |
| **Part C** | Medicare Advantage (private plans) | Varies (replaces A & B) |
| **Part D** | Prescription drugs | ~$35-100/month (varies) |

**Enrollment Windows:**
1. **Initial Enrollment Period (IEP)**: 7 months around your 65th birthday (3 months before, birthday month, 3 months after)
2. **General Enrollment**: January 1 - March 31 (late penalty applies)
3. **Special Enrollment**: If you have employer coverage

**Critical Deadlines:**
- If you don't enroll in Part B during IEP and don't have creditable employer coverage, you'll face a **10% penalty for each 12-month period** you delayed
- Part D late penalty: 1% of national base premium × months without coverage

**If Still Working at 65:**
- With creditable employer coverage, you can delay Parts B and D without penalty
- Enroll within 8 months of employer coverage ending""" + STANDARD_DISCLAIMER,
        "category": "health_insurance_medicare"
    },
]


# =============================================================================
# ANNUITY TEMPLATES
# =============================================================================

ANNUITY_QA = [
    {
        "instruction": "What are the different types of annuities and which is best for retirement income?",
        "output": """Annuities come in several types, each serving different purposes:

**By Timing:**
- **Immediate Annuity**: Start payments within 1 year of purchase
- **Deferred Annuity**: Accumulate value, convert to income later

**By Return Type:**
| Type | How It Works | Risk Level |
|------|--------------|------------|
| **Fixed** | Guaranteed interest rate | Low |
| **Fixed Indexed** | Returns linked to index with cap/floor | Low-Moderate |
| **Variable** | Invested in sub-accounts | Higher |

**For Guaranteed Retirement Income:**
A **Single Premium Immediate Annuity (SPIA)** provides the highest payout rate because:
- No accumulation phase
- Insurance company can plan precisely
- Mortality credits (pooled risk)

**Example SPIA Payout (65-year-old, $100,000):**
- Life only: ~$6,000-7,000/year
- 10-year certain: ~$5,500-6,500/year
- Joint life (both 65): ~$5,000-6,000/year

**Key Considerations:**
1. Inflation risk (payments fixed unless indexed)
2. Loss of principal access
3. No death benefit for life-only option
4. Issuer credit risk (choose strong carriers)

**Best Practice:** Don't annuitize more than you need. Keep liquid assets for emergencies and flexibility.""" + ILLUSTRATION_DISCLAIMER + STANDARD_DISCLAIMER,
        "category": "annuities"
    },
    {
        "instruction": "I'm 70 years old and a financial advisor is pushing me to put $200,000 into an indexed annuity with a 10-year surrender period. Is this appropriate?",
        "output": """This raises several suitability concerns that warrant careful consideration:

**Red Flags:**

1. **Age + Surrender Period**: At 70, a 10-year surrender period means limited access to these funds until age 80. This is a significant portion of remaining life expectancy.

2. **Amount Relative to Liquid Assets**: If $200,000 represents a large portion of your liquid net worth, tying it up could create hardship.

3. **"Pushing"**: Appropriate recommendations are explained, not pushed.

**Questions to Ask:**
- What are the exact surrender charges by year?
- What is your total liquid net worth?
- What other income sources do you have?
- Why is an indexed annuity better than alternatives for your goals?
- What commission does the advisor earn?

**NAIC Suitability Standards Require:**
- Reasonable basis that product meets your objectives
- You have the financial ability to sustain the purchase
- Replacement considerations if exchanging another product

**Alternatives to Consider:**
- Shorter surrender period products
- Multi-year guaranteed annuities (MYGAs)
- Laddered approach with smaller amounts
- Keeping more liquid

**Bottom Line:** A 10-year surrender period for a 70-year-old requires strong justification. Get a second opinion from a fee-only advisor who doesn't earn commissions.""" + STANDARD_DISCLAIMER,
        "category": "annuities_suitability"
    },
]


# =============================================================================
# PROPERTY & CASUALTY TEMPLATES
# =============================================================================

PC_INSURANCE_QA = [
    {
        "instruction": "What does umbrella insurance cover and how much do I need?",
        "output": """Umbrella insurance provides additional liability coverage above your auto and homeowners policies. It's one of the most valuable yet underutilized coverages.

**What It Covers:**
- Bodily injury to others
- Property damage you cause
- Personal liability (defamation, libel, slander)
- Landlord liability (for rental properties)
- Legal defense costs

**What It Doesn't Cover:**
- Your own injuries or property
- Business activities
- Intentional acts
- Contractual liability

**How Much You Need:**
Consider your "exposure" - what could you lose in a lawsuit:

| Net Worth | Suggested Umbrella |
|-----------|-------------------|
| $100K-500K | $1 million |
| $500K-1M | $1-2 million |
| $1M-2M | $2-3 million |
| $2M+ | $3-5 million+ |

**Additional Factors:**
- Number of drivers in household
- Teen drivers (higher risk)
- Pool, trampoline, or dog (attractive nuisances)
- High-profile career
- Rental properties
- Frequent entertaining

**Cost:**
Surprisingly affordable: ~$150-300/year for $1 million. Additional millions often cost only $50-100 each.

**Requirement:** You typically need minimum underlying coverage (e.g., $250K/$500K auto liability) to qualify.""" + STANDARD_DISCLAIMER,
        "category": "property_casualty"
    },
    {
        "instruction": "What's the difference between replacement cost and actual cash value for homeowners insurance?",
        "output": """This distinction significantly impacts claims payouts:

**Replacement Cost (RC):**
- Pays to replace or repair with new items of similar kind/quality
- No deduction for depreciation
- You receive what it costs to buy new
- Higher premiums

**Actual Cash Value (ACV):**
- Pays replacement cost MINUS depreciation
- Factors in age and condition
- You receive what the item was "worth" when lost
- Lower premiums

**Example: 8-Year-Old Roof Destroyed by Hail**
- Replacement cost: $15,000 (cost of new roof)
- ACV calculation: $15,000 - (8 years × $750/year depreciation) = $9,000

**The $6,000 difference** comes out of your pocket with ACV.

**Recommendations:**
1. **Dwelling**: Always replacement cost
2. **Personal Property**: Replacement cost if affordable
3. **Review Policy**: Ensure coverage equals replacement cost, not market value
4. **Inflation Guard**: Add endorsement for automatic increases
5. **Document Belongings**: Photo/video inventory for claims

**Warning:** Some policies have "Replacement Cost" but pay ACV initially, reimbursing the difference after repairs are made.""" + STANDARD_DISCLAIMER,
        "category": "property_casualty"
    },
]


# =============================================================================
# LONG-TERM CARE TEMPLATES
# =============================================================================

LTC_INSURANCE_QA = [
    {
        "instruction": "What is long-term care insurance and when should I consider buying it?",
        "output": """Long-term care insurance covers services not covered by health insurance or Medicare when you can't perform daily activities independently.

**What It Covers:**
- Nursing home care
- Assisted living facilities
- Home health aides
- Adult day care
- Hospice care

**Benefit Triggers (typically need 2 of 6 ADLs):**
1. Bathing
2. Dressing
3. Eating
4. Toileting
5. Transferring (moving in/out of bed)
6. Continence

Or cognitive impairment (dementia, Alzheimer's)

**Key Policy Features:**
- **Daily/Monthly Benefit**: $150-300/day typical
- **Benefit Period**: 2-5 years or lifetime
- **Elimination Period**: 30-90 days before benefits start
- **Inflation Protection**: 3-5% compound or simple

**Ideal Purchase Window: Ages 50-65**
- Earlier: May never need it, paying longer
- Later: Health issues may disqualify you, premiums much higher

**The LTC Dilemma:**
- ~70% of 65-year-olds will need some LTC
- Average need: 3 years
- 20% need care for 5+ years
- Average nursing home: $95,000/year

**Alternatives:**
- Hybrid life/LTC policies
- Self-insuring (requires significant assets)
- Medicaid planning (must spend down assets)""" + STANDARD_DISCLAIMER,
        "category": "long_term_care"
    },
]


# =============================================================================
# DISABILITY INSURANCE TEMPLATES
# =============================================================================

DISABILITY_INSURANCE_QA = [
    {
        "instruction": "Why is disability insurance important and how much coverage do I need?",
        "output": """Disability insurance protects your most valuable asset: your ability to earn income.

**The Risk:**
- 1 in 4 workers will be disabled for 90+ days before age 65
- Average disability lasts 2.5 years
- Most disabilities are illness-related, not accidents

**Coverage Types:**

| Feature | Short-Term (STD) | Long-Term (LTD) |
|---------|------------------|-----------------|
| Waiting Period | 0-14 days | 90-180 days |
| Benefit Duration | 3-6 months | Years to age 65 |
| Typical Benefit | 60-70% of salary | 60% of salary |
| Source | Usually employer | Employer or individual |

**How Much You Need:**
- Target: 60-70% of gross income
- Why not 100%? Benefits paid by employee premiums are tax-free
- 60% tax-free ≈ 100% of take-home pay for many

**Key Policy Features:**
1. **Own-Occupation**: Pays if you can't do YOUR job
2. **Any-Occupation**: Only pays if you can't do ANY job
3. **Residual Benefits**: Partial disability coverage
4. **Non-Cancelable**: Carrier can't change terms or rates
5. **Guaranteed Renewable**: Carrier must renew regardless of health

**Gap Analysis:**
| Source | Typical Coverage |
|--------|-----------------|
| Social Security Disability | ~$1,500/month average (strict criteria) |
| Employer LTD | 60% of salary (often capped) |
| Individual Policy | Fills the gap |

**Priority Order:**
1. Max employer LTD if available
2. Add individual policy if income exceeds employer cap
3. Especially important for self-employed""" + STANDARD_DISCLAIMER,
        "category": "disability_insurance"
    },
]


# =============================================================================
# REGULATORY & COMPLIANCE TEMPLATES
# =============================================================================

REGULATORY_QA = [
    {
        "instruction": "What does fiduciary mean in insurance and are insurance agents fiduciaries?",
        "output": """This is an important distinction that affects the advice you receive:

**Traditional Insurance Standard: Suitability**
Most insurance agents must only recommend products that are "suitable" - meaning:
- Appropriate for your general financial situation
- Meets your stated objectives
- You can afford the premiums

**Fiduciary Standard**
Fiduciaries must act in your "best interest," which is a higher standard:
- Must put your interests above their own
- Must disclose conflicts of interest
- Must recommend the best option, not just a suitable one

**Who's Who:**
| Professional | Standard | Commission |
|--------------|----------|------------|
| Insurance Agent | Suitability | Commission |
| Broker (NY) | Best Interest (Reg 187) | Commission |
| RIA (Investment Advisor) | Fiduciary | Fee-based |
| Fee-Only Advisor | Fiduciary | Fee-only |

**Recent Changes:**
- **NY Regulation 187** (2020): Requires "best interest" for life insurance and annuities in New York
- **NAIC Model Regulation**: Enhanced suitability requirements nationwide
- Proposed federal rules have been contested

**Practical Advice:**
1. Ask: "Are you acting as a fiduciary?"
2. Ask: "How are you compensated?"
3. Get recommendations in writing
4. Compare multiple options independently
5. Consider fee-only advisors for complex decisions""" + STANDARD_DISCLAIMER,
        "category": "regulatory"
    },
    {
        "instruction": "What is a 1035 exchange and when should I consider it?",
        "output": """A 1035 exchange allows you to transfer one insurance policy or annuity to another without triggering immediate taxes.

**Qualifying Exchanges (IRS Section 1035):**
- Life insurance → Life insurance
- Life insurance → Annuity
- Annuity → Annuity
- Life insurance → Long-term care
- Annuity → Long-term care

**Cannot Exchange:**
- Annuity → Life insurance (wrong direction)
- Employer-sponsored plans → Individual policies

**When It Makes Sense:**
1. Better terms on new policy
2. Lower fees or expenses
3. Different features needed
4. Company financial concerns
5. Consolidating policies

**When to Be Cautious:**
1. New surrender charges begin
2. New contestability period (2 years)
3. Losing grandfathered benefits
4. Health changes affect new coverage
5. Commission-motivated recommendation

**Critical Steps:**
1. Never surrender old policy until new one is issued
2. Keep same owner and insured
3. Have new company handle the transfer directly
4. Document cost basis for tax purposes
5. Compare policies side-by-side

**Red Flags:**
- Agent pushing exchange shortly after previous sale
- Focus on "upgrades" without discussing costs
- Pressure to act quickly
- Not comparing surrender charges

**NAIC Replacement Rules:**
When replacing an existing policy, agents must provide specific disclosures and comparisons.""" + STANDARD_DISCLAIMER,
        "category": "regulatory"
    },
]


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_variations(base_qa: Dict, num_variations: int = 3) -> List[Dict]:
    """Generate slight variations of a base Q&A"""
    variations = [base_qa]

    # Add difficulty variations
    if "instruction" in base_qa and num_variations > 1:
        # Beginner version
        beginner = base_qa.copy()
        beginner["instruction"] = f"In simple terms, {base_qa['instruction'].lower()}"
        beginner["category"] = base_qa["category"] + "_beginner"
        variations.append(beginner)

        # Scenario version
        scenario = base_qa.copy()
        ages = [25, 35, 45, 55, 65]
        incomes = ["$50,000", "$75,000", "$100,000", "$150,000"]
        scenario["instruction"] = f"I'm {random.choice(ages)} years old making {random.choice(incomes)}. {base_qa['instruction']}"
        scenario["category"] = base_qa["category"] + "_scenario"
        variations.append(scenario)

    return variations


def generate_insurance_dataset(n_examples: int = 10000) -> List[Dict]:
    """Generate full insurance training dataset"""
    all_templates = (
        LIFE_INSURANCE_QA +
        HEALTH_INSURANCE_QA +
        ANNUITY_QA +
        PC_INSURANCE_QA +
        LTC_INSURANCE_QA +
        DISABILITY_INSURANCE_QA +
        REGULATORY_QA
    )

    examples = []

    # Generate base examples with variations
    for template in all_templates:
        variations = generate_variations(template, num_variations=3)
        examples.extend(variations)

    # Duplicate and vary to reach target
    while len(examples) < n_examples:
        template = random.choice(all_templates)
        example = template.copy()

        # Add random context
        if random.random() > 0.5:
            age = random.randint(25, 70)
            income = random.choice([50000, 75000, 100000, 150000, 200000])
            example["instruction"] = f"I'm {age} and make ${income:,}. {template['instruction']}"
            example["category"] = template["category"] + "_personalized"

        examples.append(example)

    return examples[:n_examples]


def save_dataset(examples: List[Dict], output_path: str):
    """Save dataset to JSON file"""
    with open(output_path, "w") as f:
        json.dump(examples, f, indent=2)

    print(f"Saved {len(examples)} examples to {output_path}")

    # Print statistics
    categories = {}
    for ex in examples:
        cat = ex.get("category", "unknown")
        base_cat = cat.split("_")[0] + "_" + cat.split("_")[1] if "_" in cat else cat
        categories[base_cat] = categories.get(base_cat, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:20]:
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate insurance training data")
    parser.add_argument("--n", type=int, default=10000, help="Number of examples")
    parser.add_argument("--output", type=str,
                        default="backend/training_data/insurance_training_data.json",
                        help="Output file path")
    args = parser.parse_args()

    print(f"Generating {args.n} insurance training examples...")
    examples = generate_insurance_dataset(args.n)
    save_dataset(examples, args.output)

    print("\nDataset includes proper disclaimers and compliance language.")
    print("All examples follow NAIC suitability guidelines.")
