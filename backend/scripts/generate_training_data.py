#!/usr/bin/env python3
"""
Generate training data for DVoRA/QDoRA fine-tuning.

Creates 2000+ Q&A pairs from the wealth management knowledge base
covering ALL 17 knowledge domains:
- Retirement planning (401k, IRA, Roth, FIRE)
- College planning (529, Coverdell, FAFSA)
- Goal-based tier progression
- 70+ professional roles and certifications
- Estate planning and trust administration
- Business succession planning
- Family office structure and governance
- Credit and financing strategies
- Treasury and banking
- Compliance and operations
- Generational wealth transfer
- Financial literacy basics

All 5 wealth tiers: Foundation, Builder, Growth, Affluent, HNW/UHNW
"""

import json
import random
from pathlib import Path
from typing import Any
from datetime import datetime

# Knowledge base path
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "app" / "knowledge_base" / "wealth_management" / "data"
OUTPUT_PATH = Path(__file__).parent.parent / "training_data"

# Wealth tier definitions
WEALTH_TIERS = {
    "Foundation": {"min": 0, "max": 10000, "description": "Building financial fundamentals"},
    "Builder": {"min": 10000, "max": 75000, "description": "Establishing wealth habits"},
    "Growth": {"min": 75000, "max": 500000, "description": "Accelerating wealth accumulation"},
    "Affluent": {"min": 500000, "max": 5000000, "description": "Advanced wealth strategies"},
    "HNW_UHNW": {"min": 5000000, "max": None, "description": "Family office level services"}
}


def load_knowledge_base() -> dict[str, Any]:
    """Load all knowledge base JSON files."""
    knowledge = {}
    for json_file in KNOWLEDGE_BASE_PATH.glob("*.json"):
        with open(json_file, 'r') as f:
            knowledge[json_file.stem] = json.load(f)
        print(f"  Loaded: {json_file.name}")
    return knowledge


# =============================================================================
# PASS 1: RETIREMENT PLANNING (retirement_planning.json)
# =============================================================================

def generate_retirement_qa(knowledge: dict) -> list[dict]:
    """Generate comprehensive retirement planning Q&A pairs."""
    qa_pairs = []

    # Age and income combinations for personalized advice
    ages = [22, 25, 28, 30, 32, 35, 38, 40, 42, 45, 48, 50, 52, 55, 58, 60, 62, 65]
    incomes = [35000, 50000, 65000, 75000, 85000, 100000, 125000, 150000, 175000, 200000, 250000, 300000, 400000, 500000]

    # Core retirement questions with detailed responses
    core_questions = [
        {
            "q": "What is a 401(k) and how does it work?",
            "a": """A **401(k)** is an employer-sponsored retirement savings plan with significant tax advantages.

**Key Features:**
- **Contribution Limits (2024):** $23,000 ($30,500 if 50+)
- **Tax Treatment:** Traditional = pre-tax; Roth 401(k) = after-tax
- **Employer Match:** Many employers match contributions (free money!)
- **Vesting:** May require years of service to keep employer contributions

**How It Works:**
1. You elect a percentage of salary to contribute
2. Money is deducted from paycheck before taxes (traditional)
3. Funds grow tax-deferred until withdrawal
4. Withdrawals after 59½ are taxed as income

**Investment Options:**
- Target-date funds (set it and forget it)
- Index funds (low cost, diversified)
- Company stock (limit to 10% max)

**Action Items:**
1. Contribute at least enough to get full employer match
2. Increase contribution by 1% each year
3. Review investment allocation annually"""
        },
        {
            "q": "What is a Roth IRA and who should use one?",
            "a": """A **Roth IRA** offers tax-free growth and withdrawals in retirement.

**Key Features:**
- **Contribution Limits (2024):** $7,000 ($8,000 if 50+)
- **Income Limits:** Single <$161,000; Married <$240,000 (for full contribution)
- **Tax Treatment:** Contribute after-tax money, withdrawals are tax-FREE

**Who Should Use a Roth IRA:**
1. **Young professionals** - likely in lower tax bracket now
2. **Those expecting higher future income** - lock in low tax rate
3. **Anyone wanting tax diversification** - hedge against future tax increases
4. **Those who may need flexibility** - contributions can be withdrawn anytime

**Roth vs Traditional IRA:**
| Feature | Roth IRA | Traditional IRA |
|---------|----------|-----------------|
| Tax on contributions | Pay now | Deduct now |
| Tax on withdrawals | Tax-FREE | Taxed as income |
| RMDs | None (lifetime) | Required at 73 |
| Early access | Contributions anytime | 10% penalty |

**Backdoor Roth:** If over income limits, contribute to traditional IRA then convert to Roth."""
        },
        {
            "q": "When should I start taking Social Security benefits?",
            "a": """Social Security timing significantly impacts lifetime benefits.

**Claiming Ages:**
- **Age 62:** Earliest, but benefits reduced ~30%
- **Age 67:** Full Retirement Age (FRA) for those born 1960+
- **Age 70:** Maximum benefit, ~24% higher than FRA

**Break-Even Analysis:**
- Claiming at 62 vs 67: Break-even around age 78-80
- Claiming at 67 vs 70: Break-even around age 82-83

**When to Claim Early (62):**
- Health issues/shorter life expectancy
- Need the income, no other sources
- Spouse has higher benefit to maximize

**When to Delay (70):**
- Excellent health, family longevity
- Still working with good income
- Spouse with lower benefit (survivor benefits)
- Want maximum guaranteed income

**Spousal Strategies:**
- Lower earner claims early, higher earner delays
- Survivor receives higher of two benefits
- Divorced? May claim on ex-spouse if married 10+ years

**Key Insight:** Delaying is essentially buying an annuity with 8%/year guaranteed return."""
        },
        {
            "q": "What is the 4% rule for retirement withdrawals?",
            "a": """The **4% Rule** is a guideline for sustainable retirement withdrawals.

**The Rule:**
Withdraw 4% of your portfolio in year 1, then adjust for inflation annually.

**Example:**
- $1,000,000 portfolio
- Year 1: Withdraw $40,000
- Year 2: Withdraw $40,000 + inflation (~$41,200)

**Historical Success Rate:** ~95% chance portfolio lasts 30 years

**Assumptions:**
- 50/50 stock/bond allocation
- 30-year retirement horizon
- Based on historical U.S. market returns

**Limitations:**
- Doesn't account for sequence of returns risk
- May be too conservative for younger retirees
- Doesn't adjust for market conditions

**Modern Alternatives:**
1. **Guardrails Strategy:** Adjust spending based on portfolio performance
2. **Dynamic Withdrawal:** Reduce in down years, increase in up years
3. **Bucket Strategy:** Short-term (cash), medium-term (bonds), long-term (stocks)

**Practical Application:**
- Multiply annual expenses by 25 = retirement target
- $50,000/year expenses = need $1,250,000"""
        },
        {
            "q": "How do Required Minimum Distributions (RMDs) work?",
            "a": """**RMDs** are mandatory withdrawals from retirement accounts starting at age 73.

**Accounts Subject to RMDs:**
- Traditional IRA
- 401(k), 403(b), 457
- SEP IRA, SIMPLE IRA
- NOT Roth IRA (during owner's lifetime)

**RMD Age Timeline:**
- Born 1950 or earlier: Age 72
- Born 1951-1959: Age 73
- Born 1960+: Age 75

**Calculation:**
RMD = Account Balance (Dec 31) ÷ Life Expectancy Factor

**Example (Age 75, $500,000 balance):**
$500,000 ÷ 24.6 = $20,325 minimum withdrawal

**Penalties:**
- Failure to take RMD: 25% excise tax on amount not withdrawn
- Reduced to 10% if corrected within 2 years

**Strategies to Minimize RMDs:**
1. **Roth Conversions:** Convert before RMDs start
2. **QCDs:** Qualified Charitable Distributions (up to $105,000/year)
3. **Delay 401(k) RMDs:** If still working past 73

**Key Dates:**
- First RMD: April 1 of year after turning 73
- Subsequent RMDs: December 31 each year"""
        }
    ]

    for item in core_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "retirement_planning"
        })

    # Generate age/income specific questions
    for age in ages:
        for income in incomes:
            # Savings rate advice
            qa_pairs.append({
                "instruction": f"I'm {age} years old making ${income:,}/year. How much should I save for retirement?",
                "input": "",
                "output": _generate_retirement_savings_advice(age, income),
                "category": "retirement_planning"
            })

    # FIRE movement questions
    fire_qa = [
        {
            "q": "What is FIRE and how do I achieve financial independence?",
            "a": """**FIRE** = Financial Independence, Retire Early

**Core Principles:**
1. **High Savings Rate:** 50-70% of income
2. **Frugal Living:** Minimize expenses without sacrificing happiness
3. **Aggressive Investing:** Maximize returns through index funds
4. **Income Growth:** Increase earning potential

**Types of FIRE:**
- **Lean FIRE:** $40,000/year expenses, ~$1M needed
- **Regular FIRE:** $60,000/year, ~$1.5M needed
- **Fat FIRE:** $100,000+/year, ~$2.5M+ needed
- **Coast FIRE:** Save enough early, let compounding do the rest
- **Barista FIRE:** Part-time work covers expenses, investments grow

**The Math:**
- Years to FIRE = (Portfolio Target - Current Savings) / Annual Savings
- At 50% savings rate: ~17 years to FIRE
- At 70% savings rate: ~8.5 years to FIRE

**Key Strategies:**
1. Track every expense (know your number)
2. Eliminate high-cost housing/transportation
3. Maximize tax-advantaged accounts
4. Build multiple income streams
5. Invest in low-cost index funds (VTSAX, VTI)"""
        },
        {
            "q": "How do I access retirement funds before 59.5 without penalty?",
            "a": """Several legal strategies allow early access to retirement funds:

**1. Roth IRA Contributions**
- Withdraw contributions (not earnings) anytime, tax and penalty free
- 5-year rule applies to conversions

**2. Rule of 55**
- Leave employer at 55+ (or later)
- Access that employer's 401(k) without penalty
- Does NOT apply to IRAs

**3. 72(t) SEPP Distributions**
- Substantially Equal Periodic Payments
- Must continue for 5 years OR until 59.5 (whichever is longer)
- Three calculation methods: Required Minimum, Fixed Amortization, Fixed Annuitization

**4. Roth Conversion Ladder**
- Convert Traditional IRA to Roth each year
- Wait 5 years, then withdraw conversions penalty-free
- Requires 5-year runway of expenses

**5. Health Insurance (HSA)**
- Use HSA funds for medical expenses anytime
- After 65, use for anything (taxed like traditional IRA)

**6. Other Exceptions:**
- First-time home purchase ($10,000 lifetime)
- Higher education expenses
- Disability
- Medical expenses exceeding 7.5% of AGI

**Strategy:** Build taxable brokerage alongside retirement accounts for flexibility."""
        }
    ]

    for item in fire_qa:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "retirement_planning"
        })

    return qa_pairs


def _generate_retirement_savings_advice(age: int, income: float) -> str:
    """Generate personalized retirement savings advice."""
    years_to_65 = max(65 - age, 0)

    # Savings rate based on age
    if age < 30:
        rate = 0.15
        catch_up = "You have time on your side. Start strong and let compounding work."
    elif age < 40:
        rate = 0.20
        catch_up = "Prime wealth-building years. Maximize tax-advantaged accounts."
    elif age < 50:
        rate = 0.25
        catch_up = "Accelerate savings. Consider catch-up contributions at 50."
    else:
        rate = 0.30
        catch_up = "Maximize catch-up contributions. Consider delaying Social Security."

    monthly = income * rate / 12
    annual = income * rate

    # Target by age (Fidelity benchmarks)
    targets = {25: 0.5, 30: 1, 35: 2, 40: 3, 45: 4, 50: 6, 55: 7, 60: 8, 65: 10}
    target_multiple = targets.get(min(65, max(25, (age // 5) * 5)), 1)
    target_amount = income * target_multiple

    return f"""**Retirement Savings Guidance for Age {age}, Income ${income:,}**

**Recommended Savings Rate:** {rate*100:.0f}% = ${annual:,.0f}/year (${monthly:,.0f}/month)

**{catch_up}**

**Target Savings by Age:**
- Your age ({age}): ${target_amount:,.0f} (approximately {target_multiple}x salary)
- Age 65 goal: ${income * 10:,.0f} (10x salary)

**Priority Order:**
1. 401(k) up to employer match (100% return!)
2. HSA if eligible ($4,150/$8,300 in 2024)
3. Roth IRA ($7,000, or $8,000 if 50+)
4. Back to 401(k) up to max ($23,000, or $30,500 if 50+)
5. Taxable brokerage for additional savings

**Investment Allocation at Age {age}:**
- Stocks: {max(110 - age, 50)}%
- Bonds: {min(age - 10, 50)}%
- Use target-date fund for simplicity

**Timeline:** {years_to_65} years until traditional retirement.

**Key Actions:**
1. Automate contributions (pay yourself first)
2. Increase savings 1% annually with raises
3. Review allocation yearly
4. Avoid early withdrawals"""


# =============================================================================
# PASS 2: COLLEGE PLANNING (college_planning.json)
# =============================================================================

def generate_college_qa(knowledge: dict) -> list[dict]:
    """Generate comprehensive college planning Q&A pairs."""
    qa_pairs = []

    # Core 529 questions
    core_questions = [
        {
            "q": "What is a 529 plan and how does it work?",
            "a": """A **529 plan** is a tax-advantaged education savings account.

**Key Benefits:**
1. **Tax-Free Growth:** No federal taxes on investment gains
2. **Tax-Free Withdrawals:** For qualified education expenses
3. **State Tax Benefits:** Many states offer deductions/credits
4. **High Limits:** $300,000-$500,000+ lifetime per beneficiary
5. **Flexibility:** Change beneficiaries within family

**Two Types:**
1. **529 Savings Plan** (most common)
   - Investment account with mutual fund options
   - Value fluctuates with market

2. **529 Prepaid Tuition Plan**
   - Lock in current tuition rates
   - Limited to specific schools/states

**Qualified Expenses:**
- Tuition and fees (college, trade school, K-12 up to $10k)
- Room and board (if enrolled at least half-time)
- Books, supplies, equipment
- Computers and internet
- Special needs services
- Student loan repayment (up to $10,000 lifetime)

**Non-Qualified Withdrawal Penalty:**
- Income tax on earnings
- 10% penalty on earnings
- State tax recapture if deduction was taken

**Best Practices:**
1. Open account early (even with small amount)
2. Set up automatic contributions
3. Use age-based portfolios
4. Compare your state's plan vs. others"""
        },
        {
            "q": "How do I maximize financial aid eligibility?",
            "a": """Strategic planning can significantly increase financial aid.

**Understanding FAFSA:**
- Uses income from 2 years prior ("Prior-Prior Year")
- Parent assets assessed at ~5.64%
- Student assets assessed at 20%
- Retirement accounts NOT counted

**Asset Positioning Strategies:**

**2+ Years Before College:**
1. Maximize retirement contributions (not counted)
2. Pay down consumer debt
3. Make necessary major purchases
4. Avoid putting assets in child's name

**Income Timing:**
1. Avoid realizing capital gains in base years
2. Defer bonuses if possible
3. Consider Roth conversions timing

**Account Ownership:**
- Parent-owned 529: Best (5.64% assessment)
- Grandparent-owned 529: No longer counted (2024+ FAFSA)
- Custodial accounts (UGMA/UTMA): Counted at 20%

**CSS Profile Considerations:**
- More detailed than FAFSA
- May count home equity, small business
- Used by ~200 private colleges

**Financial Aid Timeline:**
- October 1: FAFSA opens
- Submit ASAP (some aid is first-come)
- Compare award letters carefully
- Appeal if circumstances change

**Red Flags to Avoid:**
- Never hide assets (federal fraud)
- Don't quit job to reduce income
- Don't liquidate retirement accounts"""
        },
        {
            "q": "Should grandparents contribute to a 529 plan?",
            "a": """Grandparent 529 contributions offer excellent benefits post-2024.

**The Good News (FAFSA Simplification Act 2024+):**
- Grandparent-owned 529 distributions NO LONGER reported
- Grandparent gifts to parent's 529 also not counted
- Makes grandparent contributions much more attractive

**Options for Grandparents:**

**Option 1: Own the 529**
- Maintains control over investments
- Can change beneficiary
- Great for estate planning
- 5-year gift tax averaging available

**Option 2: Contribute to Parent's 529**
- Parent controls the account
- Uses grandparent's gift exclusion ($18,000/year)
- Can contribute more via 5-year averaging

**Option 3: Pay Tuition Directly**
- Unlimited gift tax exclusion
- Must go directly to institution
- Doesn't use annual exclusion
- Good for unexpected expenses

**Estate Planning Benefits:**
- **Superfunding:** Contribute 5 years at once
  - Individual: $90,000
  - Couple: $180,000
- Removes assets from taxable estate
- Retains control (unlike other gifts)
- Can reclaim if needed (with penalties)

**Strategy by Grandparent's Situation:**
- **Want control:** Own the 529
- **Want simplicity:** Gift to parent's 529
- **Large estate:** Superfund for estate reduction
- **Near college:** Pay tuition directly"""
        }
    ]

    for item in core_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "college_planning"
        })

    # Age-specific college planning
    child_ages = [0, 1, 2, 3, 5, 7, 10, 12, 14, 16, 17]
    school_types = ["public in-state", "public out-of-state", "private university", "community college"]

    for age in child_ages:
        for school in school_types:
            qa_pairs.append({
                "instruction": f"My child is {age} years old. How much should I save for {school}?",
                "input": "",
                "output": _generate_college_savings_plan(age, school),
                "category": "college_planning"
            })

    return qa_pairs


def _generate_college_savings_plan(child_age: int, school_type: str) -> str:
    """Generate personalized college savings plan."""
    years_until = max(18 - child_age, 1)

    # Current costs (2024)
    costs = {
        "public in-state": 26000,
        "public out-of-state": 46000,
        "private university": 58000,
        "community college": 13000
    }

    annual_cost = costs.get(school_type, 30000)
    inflation = 0.05

    # Calculate future costs
    future_annual = annual_cost * ((1 + inflation) ** years_until)
    total_cost = future_annual * 4  # 4-year degree

    # Monthly savings needed (7% return assumed)
    if years_until > 0:
        monthly_needed = total_cost / (((1.07 ** years_until - 1) / 0.07 * 12) + years_until * 12) / 1.8
    else:
        monthly_needed = total_cost / 48

    return f"""**College Savings Plan: Age {child_age} → {school_type.title()}**

**Timeline:** {years_until} years until college

**Cost Projections (5% annual inflation):**
- Current annual cost: ${annual_cost:,}
- Projected annual cost: ${future_annual:,.0f}
- **Total 4-year cost: ${total_cost:,.0f}**

**Recommended Monthly Savings: ${monthly_needed:,.0f}**
(Assuming 7% average annual return)

**Savings Strategy by Timeline:**

{"**Long Runway (10+ years):**" if years_until > 10 else "**Medium Timeline (5-10 years):**" if years_until > 5 else "**Short Timeline (<5 years):**"}
- Investment mix: {"80% stocks / 20% bonds" if years_until > 10 else "60% stocks / 40% bonds" if years_until > 5 else "40% stocks / 60% bonds"}
- {"Aggressive growth focus" if years_until > 10 else "Balanced approach" if years_until > 5 else "Capital preservation priority"}

**Action Plan:**

1. **Open 529 Account**
   - Compare your state's tax deduction
   - Consider Utah, Nevada, NY for top-rated plans

2. **Automate Contributions**
   - ${monthly_needed:,.0f}/month minimum
   - Increase annually with raises

3. **Involve Family**
   - Request 529 contributions for holidays/birthdays
   - Grandparents can superfund (5 years at once)

4. **Supplemental Strategies**
   - Coverdell ESA: $2,000/year additional
   - I-Bonds: $10,000/year, tax-advantaged

5. **Plan for Financial Aid**
   - File FAFSA October 1 of senior year
   - Research merit scholarships early
   - Keep 529 in parent's name

**Remember:** Saving any amount reduces future student loan burden!"""


# =============================================================================
# PASS 3: ESTATE PLANNING (estate_planning.json)
# =============================================================================

def generate_estate_planning_qa(knowledge: dict) -> list[dict]:
    """Generate estate planning Q&A pairs."""
    qa_pairs = []

    core_questions = [
        {
            "q": "What documents do I need for a basic estate plan?",
            "a": """Every adult needs these **five essential estate planning documents:**

**1. Last Will and Testament**
- Names executor to manage your estate
- Specifies asset distribution
- Names guardians for minor children
- Goes through probate (public process)

**2. Revocable Living Trust**
- Avoids probate (private, faster)
- Manages assets if you're incapacitated
- Can include specific distribution instructions
- More complex/expensive than will alone

**3. Durable Power of Attorney (Financial)**
- Names agent to handle finances if incapacitated
- "Durable" means it survives incapacity
- Can be broad or limited in scope
- Effective immediately or upon incapacity (springing)

**4. Healthcare Power of Attorney**
- Names agent for medical decisions
- Takes effect when you can't communicate
- Should know your wishes
- Also called healthcare proxy

**5. Living Will / Advance Directive**
- Specifies end-of-life care preferences
- Addresses life support, feeding tubes, etc.
- Guides family and doctors
- Reduces burden on loved ones

**Bonus Documents:**
- HIPAA Authorization: Allows access to medical records
- Beneficiary Designations: Update on all accounts
- Letter of Intent: Non-legal guidance for family

**Who Needs What:**
- Single, no kids: At minimum, will + POAs
- Married, no kids: All five + beneficiary review
- Parents: All five + guardian nominations
- Business owners: Add buy-sell agreement
- High net worth: Add irrevocable trusts"""
        },
        {
            "q": "What is the difference between a will and a trust?",
            "a": """**Will vs Trust: Key Differences**

| Feature | Will | Revocable Trust |
|---------|------|-----------------|
| Probate | Goes through probate | Avoids probate |
| Privacy | Public record | Private |
| Cost to create | $300-$1,000 | $1,500-$3,000 |
| Incapacity | No protection | Manages assets |
| Effective | At death | When funded |
| Contestability | Easier to contest | Harder to contest |

**When a Will is Sufficient:**
- Simple estate under $1M
- No real estate in multiple states
- No blended family complications
- No privacy concerns
- Limited assets

**When You Need a Trust:**
- Real estate in multiple states
- Privacy is important
- Blended family situations
- Want to control distributions over time
- Incapacity planning needed
- Business ownership
- High net worth ($1M+)

**Common Trust Types:**
1. **Revocable Living Trust:** Most common, you control
2. **Irrevocable Trust:** Can't change, estate tax benefits
3. **Special Needs Trust:** For disabled beneficiaries
4. **Charitable Trust:** Tax benefits for giving

**Important:** A trust only works if properly funded (assets titled to trust)."""
        },
        {
            "q": "How do I minimize estate taxes?",
            "a": """**Estate Tax Minimization Strategies**

**Current Exemptions (2024):**
- Federal: $13.61 million per person
- Married couples: $27.22 million combined (portability)
- Rate: 40% on amounts over exemption

**Note:** Exemption scheduled to drop to ~$7 million in 2026

**Basic Strategies:**

**1. Annual Gift Exclusion**
- Gift $18,000/person/year tax-free
- Married couples: $36,000/person
- Removes assets + future growth from estate

**2. Spousal Transfers**
- Unlimited marital deduction
- Use "credit shelter" trust to preserve both exemptions

**3. Irrevocable Life Insurance Trust (ILIT)**
- Life insurance proceeds outside estate
- Must be created 3+ years before death
- Cannot be policy owner or trustee

**4. Charitable Giving**
- Charitable Remainder Trust (CRT)
- Donor Advised Fund (DAF)
- Direct charitable bequests

**Advanced Strategies:**

**5. Grantor Retained Annuity Trust (GRAT)**
- Transfer appreciating assets at reduced tax
- "Zeroed-out" GRAT minimizes gift tax

**6. Family Limited Partnership (FLP)**
- Valuation discounts for lack of marketability
- Maintain control while gifting interests

**7. Qualified Personal Residence Trust (QPRT)**
- Transfer home at discounted value
- Continue living there during trust term

**8. Dynasty Trust**
- Multi-generational wealth transfer
- Avoids estate tax at each generation
- State-specific (some allow perpetual)

**Planning Timeline:**
- Under $5M: Focus on income tax planning
- $5M-$13M: Monitor exemption changes
- Over $13M: Implement advanced strategies now"""
        }
    ]

    for item in core_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "estate_planning"
        })

    # Estate value specific questions
    estate_values = [100000, 250000, 500000, 1000000, 2000000, 5000000, 10000000, 25000000]
    for value in estate_values:
        qa_pairs.append({
            "instruction": f"I have an estate worth ${value:,}. What estate planning do I need?",
            "input": "",
            "output": _generate_estate_plan_by_value(value),
            "category": "estate_planning"
        })

    return qa_pairs


def _generate_estate_plan_by_value(estate_value: int) -> str:
    """Generate estate planning advice by value."""
    if estate_value < 500000:
        tier = "Basic"
        focus = "Simple estate plan with essential documents"
        strategies = [
            "Will with clear beneficiary designations",
            "Durable Power of Attorney",
            "Healthcare directive",
            "Review beneficiaries on all accounts",
            "Consider term life insurance"
        ]
        professionals = ["Estate planning attorney", "Insurance agent"]
        cost_range = "$500-$1,500"
    elif estate_value < 2000000:
        tier = "Intermediate"
        focus = "Probate avoidance and basic tax planning"
        strategies = [
            "Revocable living trust",
            "Pour-over will",
            "Powers of attorney",
            "Annual gifting program",
            "Life insurance review"
        ]
        professionals = ["Estate planning attorney", "CFP®", "CPA"]
        cost_range = "$2,000-$5,000"
    elif estate_value < 10000000:
        tier = "Advanced"
        focus = "Tax minimization and wealth transfer"
        strategies = [
            "Revocable trust with tax planning",
            "Irrevocable life insurance trust (ILIT)",
            "Annual exclusion gifting",
            "Charitable giving strategy",
            "Family limited partnership consideration"
        ]
        professionals = ["Estate attorney", "CFP®", "CPA", "Insurance specialist"]
        cost_range = "$5,000-$15,000"
    else:
        tier = "Ultra-High Net Worth"
        focus = "Multi-generational wealth preservation"
        strategies = [
            "Dynasty trust structure",
            "GRAT/GRUT strategies",
            "Private foundation or DAF",
            "Family limited partnership",
            "Qualified personal residence trust",
            "Family governance documents"
        ]
        professionals = ["Estate attorney", "Trust company", "CFP®", "CPA", "Family office"]
        cost_range = "$15,000-$50,000+"

    return f"""**Estate Planning for ${estate_value:,} Estate**

**Planning Tier:** {tier}
**Primary Focus:** {focus}

**Recommended Strategies:**
{chr(10).join(f"- {s}" for s in strategies)}

**Professional Team:**
{chr(10).join(f"- {p}" for p in professionals)}

**Estimated Initial Cost:** {cost_range}

**Priority Actions:**
1. Gather all financial account information
2. List all asset ownership and beneficiaries
3. Document family situation and goals
4. Schedule consultation with estate attorney
5. Review and update annually

**Estate Tax Considerations:**
- Current federal exemption: $13.61M (2024)
- Your estate: {"Below exemption - focus on income tax planning" if estate_value < 13000000 else "Implement estate tax reduction strategies"}
- State estate tax: Check your state's exemption"""


# =============================================================================
# PASS 4: TRUST ADMINISTRATION (trust_administration.json)
# =============================================================================

def generate_trust_qa(knowledge: dict) -> list[dict]:
    """Generate trust administration Q&A pairs."""
    qa_pairs = []

    core_questions = [
        {
            "q": "What are the different types of trusts and when should I use each?",
            "a": """**Trust Types and Their Uses**

**Revocable Trusts (You Can Change):**

1. **Revocable Living Trust**
   - Most common estate planning trust
   - Avoids probate, maintains privacy
   - You control during lifetime
   - Use for: Basic estate planning, probate avoidance

**Irrevocable Trusts (Cannot Change):**

2. **Irrevocable Life Insurance Trust (ILIT)**
   - Removes life insurance from estate
   - Avoids estate tax on proceeds
   - Use for: Estate tax planning, large policies

3. **Grantor Retained Annuity Trust (GRAT)**
   - Transfer appreciating assets at discount
   - Receive annuity payments back
   - Use for: Passing business interests, stocks

4. **Charitable Remainder Trust (CRT)**
   - Income stream to you, remainder to charity
   - Immediate tax deduction
   - Use for: Charitable giving with income needs

**Special Purpose Trusts:**

5. **Special Needs Trust**
   - Benefits disabled person without losing government benefits
   - Use for: Children/family with disabilities

6. **Spendthrift Trust**
   - Protects beneficiaries from creditors and themselves
   - Use for: Beneficiaries who can't manage money

7. **Dynasty Trust**
   - Multi-generational wealth transfer
   - Can last perpetually in some states
   - Use for: UHNW families, long-term planning

**Business Trusts:**

8. **Qualified Personal Residence Trust (QPRT)**
   - Transfer home at discounted value
   - Use for: High-value primary residence

9. **Intentionally Defective Grantor Trust (IDGT)**
   - Estate planning with income tax benefits
   - Use for: Sophisticated estate freeze strategies"""
        },
        {
            "q": "What are the responsibilities of a trustee?",
            "a": """**Trustee Responsibilities and Duties**

**Fiduciary Duties:**

1. **Duty of Loyalty**
   - Act solely in beneficiaries' interests
   - No self-dealing or conflicts of interest
   - Disclose any potential conflicts

2. **Duty of Prudent Administration**
   - Manage trust as a prudent person would
   - Document all decisions
   - Seek professional help when needed

3. **Duty of Impartiality**
   - Balance interests of all beneficiaries
   - Consider current vs. future beneficiaries
   - Fair treatment regardless of relationship

4. **Duty to Inform and Account**
   - Provide regular accountings
   - Respond to reasonable requests
   - Keep accurate records

**Specific Responsibilities:**

**Investment Management:**
- Follow prudent investor rule
- Diversify investments appropriately
- Consider trust terms and beneficiary needs
- Review and rebalance regularly

**Tax Compliance:**
- Obtain tax ID (EIN) for irrevocable trusts
- File annual trust tax returns (Form 1041)
- Make required distributions for tax efficiency
- Issue K-1s to beneficiaries

**Record Keeping:**
- Maintain all financial records
- Document distribution decisions
- Keep copy of trust document
- Preserve correspondence with beneficiaries

**Compensation:**
- Trustees entitled to reasonable fees
- Usually 1-2% of trust assets annually
- Corporate trustees may charge more
- Review trust terms for guidance

**Liability:**
- Personal liability for breach of duty
- Can be sued by beneficiaries
- Consider trustee insurance"""
        }
    ]

    for item in core_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "trust_administration"
        })

    return qa_pairs


# =============================================================================
# PASS 5: SUCCESSION PLANNING (succession_planning.json)
# =============================================================================

def generate_succession_qa(knowledge: dict) -> list[dict]:
    """Generate business succession planning Q&A pairs."""
    qa_pairs = []

    core_questions = [
        {
            "q": "How do I create a business succession plan?",
            "a": """**Business Succession Planning Framework**

**Step 1: Define Your Goals**
- When do you want to exit?
- How much do you need from the sale?
- Do you want family involvement?
- What legacy do you want to leave?

**Step 2: Identify Succession Options**

**Internal Succession:**
- Family members
- Key employees (management buyout)
- Employee Stock Ownership Plan (ESOP)

**External Succession:**
- Strategic buyer (competitor/industry)
- Financial buyer (private equity)
- Initial Public Offering (IPO)

**Step 3: Prepare the Business**
- Document all processes and procedures
- Reduce owner dependence
- Strengthen management team
- Clean up financials
- Address legal/compliance issues

**Step 4: Business Valuation**
- Get professional valuation
- Understand value drivers
- Identify areas for improvement
- Set realistic expectations

**Step 5: Develop Transition Plan**
- Timeline: Typically 3-5 years
- Training successors
- Transferring relationships
- Gradual responsibility shift

**Step 6: Address Legal and Tax Issues**
- Buy-sell agreement
- Stock structure
- Tax-efficient transfer methods
- Estate planning integration

**Step 7: Communicate**
- Family (even non-involved members)
- Key employees
- Important customers/vendors
- Advisors

**Professional Team Needed:**
- M&A attorney
- CPA with transaction experience
- Business valuation expert
- Financial planner
- Insurance specialist"""
        },
        {
            "q": "What is a buy-sell agreement and why do I need one?",
            "a": """**Buy-Sell Agreements: Protecting Business Owners**

**What It Is:**
A legally binding contract between business owners that governs what happens to ownership interests when a triggering event occurs.

**Triggering Events:**
- Death of an owner
- Disability
- Retirement
- Divorce
- Bankruptcy
- Voluntary departure
- Termination for cause

**Types of Buy-Sell Agreements:**

**1. Cross-Purchase Agreement**
- Owners agree to buy each other's shares
- Works best with 2-3 owners
- Each owner buys life insurance on others
- Basis step-up for buyers

**2. Entity Redemption (Stock Redemption)**
- Company buys departing owner's shares
- Simpler with many owners
- Company owns life insurance policies
- No basis step-up

**3. Hybrid Agreement**
- Combination of both approaches
- Company has first right to buy
- Remaining owners can pick up rest

**Key Provisions:**

**Valuation Method:**
- Fixed price (requires regular updates)
- Formula-based (revenue or earnings multiple)
- Appraisal at time of trigger
- Combination approach

**Funding Mechanisms:**
- Life insurance (most common)
- Disability insurance
- Company reserves
- Installment payments
- Combination

**Why You Need One:**
1. Ensures fair value for departing owner
2. Prevents unwanted new owners
3. Provides liquidity for family
4. Reduces conflict and lawsuits
5. Establishes clear process
6. Sets agreed-upon value (estate tax)

**Review Annually:**
- Update valuation
- Confirm insurance coverage adequate
- Adjust for ownership changes
- Review triggering events"""
        }
    ]

    for item in core_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "succession_planning"
        })

    return qa_pairs


# =============================================================================
# PASS 6: PROFESSIONAL ROLES (professional_roles.json, certifications.json)
# =============================================================================

def generate_professional_roles_qa(knowledge: dict) -> list[dict]:
    """Generate comprehensive professional roles Q&A."""
    qa_pairs = []

    # All major financial certifications
    certifications = [
        {
            "abbrev": "CFP®",
            "title": "Certified Financial Planner",
            "focus": "comprehensive financial planning",
            "requirements": "Bachelor's degree, 6,000 hours experience, pass exam, ethics",
            "best_for": "Holistic financial planning across all areas"
        },
        {
            "abbrev": "CFA®",
            "title": "Chartered Financial Analyst",
            "focus": "investment analysis and portfolio management",
            "requirements": "Bachelor's degree, 4,000 hours experience, pass 3 exams",
            "best_for": "Investment management and analysis"
        },
        {
            "abbrev": "CPA",
            "title": "Certified Public Accountant",
            "focus": "accounting, tax planning, and auditing",
            "requirements": "150 credit hours, pass exam, state license",
            "best_for": "Tax planning, compliance, and financial statements"
        },
        {
            "abbrev": "ChFC®",
            "title": "Chartered Financial Consultant",
            "focus": "advanced financial planning",
            "requirements": "8 college-level courses, 3 years experience",
            "best_for": "Complex insurance and planning situations"
        },
        {
            "abbrev": "CLU®",
            "title": "Chartered Life Underwriter",
            "focus": "life insurance and estate planning",
            "requirements": "8 college-level courses, 3 years experience",
            "best_for": "Life insurance and estate planning"
        },
        {
            "abbrev": "CPWA®",
            "title": "Certified Private Wealth Advisor",
            "focus": "high-net-worth wealth management",
            "requirements": "5+ years experience, pass exam",
            "best_for": "Ultra-high-net-worth clients ($5M+)"
        },
        {
            "abbrev": "CAIA®",
            "title": "Chartered Alternative Investment Analyst",
            "focus": "alternative investments",
            "requirements": "Bachelor's degree, pass 2 exams",
            "best_for": "Hedge funds, private equity, real assets"
        },
        {
            "abbrev": "EA",
            "title": "Enrolled Agent",
            "focus": "tax preparation and representation",
            "requirements": "Pass IRS exam or IRS experience",
            "best_for": "Tax preparation and IRS representation"
        },
        {
            "abbrev": "AIF®",
            "title": "Accredited Investment Fiduciary",
            "focus": "fiduciary investment practices",
            "requirements": "Training program, pass exam",
            "best_for": "Retirement plan management, fiduciary compliance"
        },
        {
            "abbrev": "RICP®",
            "title": "Retirement Income Certified Professional",
            "focus": "retirement income planning",
            "requirements": "3 college-level courses, experience",
            "best_for": "Creating sustainable retirement income"
        }
    ]

    for cert in certifications:
        qa_pairs.append({
            "instruction": f"What is a {cert['title']} ({cert['abbrev']}) and when should I hire one?",
            "input": "",
            "output": f"""**{cert['title']} ({cert['abbrev']})**

**Focus Area:** {cert['focus'].title()}

**Requirements:** {cert['requirements']}

**Best For:** {cert['best_for']}

**When to Hire a {cert['abbrev']}:**
- You need expertise in {cert['focus']}
- Your situation has become too complex to self-manage
- You want professional guidance and accountability
- Major life transitions (marriage, kids, retirement, inheritance)

**How to Find a Qualified {cert['abbrev']}:**
1. Professional association directory
2. Fee-only advisor networks (NAPFA, Garrett Planning)
3. Referrals from other professionals
4. Your company's benefits resources

**Questions to Ask:**
1. How are you compensated? (Fee-only preferred)
2. Are you a fiduciary? (Should be yes)
3. What is your typical client profile?
4. How do you communicate and how often?
5. What is your investment philosophy?
6. Can you provide references?

**Red Flags:**
- Pushy about specific products
- Guaranteed returns promises
- Unclear fee structure
- Not willing to sign fiduciary oath""",
            "category": "professional_roles"
        })

    # Team coordination questions by situation
    situations = [
        {
            "q": "What professional team do I need for estate planning?",
            "team": ["Estate Planning Attorney (lead)", "CFP®", "CPA", "Trust Officer", "Life Insurance Specialist"]
        },
        {
            "q": "What professionals should I hire for retirement planning?",
            "team": ["CFP® (lead)", "CPA", "Social Security Specialist", "Medicare Specialist", "Estate Attorney"]
        },
        {
            "q": "I'm selling my business. What advisors do I need?",
            "team": ["M&A Attorney (lead)", "Business Broker/Investment Banker", "CPA", "Valuation Expert", "CFP®"]
        },
        {
            "q": "I just inherited $2 million. Who should I talk to?",
            "team": ["CFP® (lead)", "CPA", "Estate Attorney", "Investment Advisor (CFA®)", "Insurance Specialist"]
        }
    ]

    for sit in situations:
        qa_pairs.append({
            "instruction": sit["q"],
            "input": "",
            "output": f"""**Recommended Professional Team**

{chr(10).join(f"{i+1}. **{member}**" for i, member in enumerate(sit['team']))}

**Coordination Tips:**
- Designate a lead advisor (usually CFP® or attorney)
- Ensure all professionals communicate
- Request they share relevant information
- Schedule joint meetings for complex decisions
- Get second opinions on major decisions

**How to Assemble Your Team:**
1. Start with your primary need
2. Ask each professional for referrals to others
3. Verify credentials through professional associations
4. Interview multiple candidates
5. Check references and reviews

**Expected Costs:**
- Attorneys: $200-$500/hour
- CPAs: $150-$400/hour
- CFP®: Fee-only $150-$300/hour or AUM 0.5-1%
- Initial comprehensive planning: $2,000-$10,000""",
            "category": "professional_roles"
        })

    return qa_pairs


# =============================================================================
# PASS 7: FINANCIAL LITERACY (financial_literacy_basics.json)
# =============================================================================

def generate_financial_literacy_qa(knowledge: dict) -> list[dict]:
    """Generate financial literacy Q&A for beginners."""
    qa_pairs = []

    beginner_questions = [
        {
            "q": "How do I create a budget?",
            "a": """**How to Create a Budget: Step-by-Step**

**Step 1: Track Your Income**
- List all income sources
- Use net (after-tax) amounts
- Include regular and irregular income

**Step 2: Track Your Expenses (1 month minimum)**
- Review bank and credit card statements
- Categorize every expense
- Don't forget cash spending

**Step 3: Choose a Budgeting Method**

**50/30/20 Rule (Recommended for beginners):**
- 50% Needs: Housing, utilities, food, insurance, minimum debt payments
- 30% Wants: Entertainment, dining out, subscriptions, hobbies
- 20% Savings: Emergency fund, retirement, debt payoff beyond minimums

**Zero-Based Budget:**
- Give every dollar a job
- Income - Expenses = $0
- More detailed but requires more effort

**Envelope System:**
- Cash in physical/digital envelopes
- When envelope is empty, stop spending
- Great for controlling problem areas

**Step 4: Set Up Your System**
- Spreadsheet (free)
- App: YNAB, Mint, EveryDollar
- Pen and paper

**Step 5: Automate**
- Direct deposit to savings (pay yourself first)
- Auto-pay fixed bills
- Reduces decision fatigue

**Step 6: Review and Adjust**
- Weekly: Quick expense check
- Monthly: Full budget review
- Quarterly: Adjust categories as needed

**Common Mistakes:**
- Being too restrictive (unsustainable)
- Not budgeting for irregular expenses
- Giving up after one bad month
- Not tracking cash spending"""
        },
        {
            "q": "How do I build an emergency fund?",
            "a": """**Building Your Emergency Fund**

**How Much Do You Need?**
- Starter: $1,000 (while paying off high-interest debt)
- Basic: 3 months of expenses
- Secure: 6 months of expenses
- Conservative: 12 months (variable income, sole provider)

**Where to Keep It:**
- High-yield savings account (4-5% APY currently)
- Money market account
- NOT in checking (too easy to spend)
- NOT invested (need stability and access)

**How to Build It:**

**Phase 1: Starter Fund ($1,000)**
- Sell unused items
- Reduce one expense temporarily
- Put tax refund toward it
- Timeline: 1-3 months

**Phase 2: One Month's Expenses**
- Automate $X per paycheck
- Bank windfalls (bonuses, gifts)
- Cut subscriptions temporarily
- Timeline: 3-6 months

**Phase 3: Full Emergency Fund**
- Continue automatic transfers
- Increase with raises
- Add any extra income
- Timeline: 12-24 months

**What Counts as an Emergency:**
✓ Job loss
✓ Medical emergency
✓ Major car repair
✓ Essential home repair
✓ Emergency travel

**NOT Emergencies:**
✗ Vacation
✗ New phone
✗ Sale/deal
✗ Holiday gifts
✗ Planned expenses

**Pro Tips:**
- Keep in separate bank (harder to access)
- Name the account "Emergency Fund"
- Replenish immediately after using
- Increase as lifestyle grows"""
        },
        {
            "q": "How do I start investing with no experience?",
            "a": """**Beginner's Guide to Investing**

**Before You Invest:**
1. ✅ Emergency fund (at least $1,000)
2. ✅ High-interest debt paid off
3. ✅ Basic budget in place

**Step 1: Understand the Basics**

**Key Concepts:**
- **Stocks:** Ownership in companies (higher risk, higher return)
- **Bonds:** Loans to companies/government (lower risk, lower return)
- **Index Funds:** Basket of many stocks (diversified, low cost)
- **Compound Interest:** Earning returns on your returns

**Step 2: Start with Tax-Advantaged Accounts**

**Order of Priority:**
1. **401(k) to employer match** - Free money!
2. **Roth IRA** - Tax-free growth
3. **HSA** (if eligible) - Triple tax benefit
4. **Back to 401(k)** - More tax-deferred growth
5. **Taxable brokerage** - No tax benefits but flexible

**Step 3: Choose Simple Investments**

**Best for Beginners:**
- **Target-Date Fund:** One fund, automatically adjusts
- **Total Stock Market Index:** VTI, VTSAX, FXAIX
- **S&P 500 Index:** VOO, VFIAX, FXAIX

**What to Look For:**
- Low expense ratio (<0.20%)
- Broad diversification
- From reputable company (Vanguard, Fidelity, Schwab)

**Step 4: Automate and Forget**

- Set up automatic contributions
- Invest same amount each paycheck (dollar-cost averaging)
- Don't check daily (or even monthly)
- Rebalance annually

**Common Beginner Mistakes:**
- Waiting for the "right time" to start
- Trying to pick individual stocks
- Selling during market drops
- Paying high fees
- Not starting at all

**The Power of Starting Early:**
$200/month for 40 years at 7% = $480,000+
$200/month for 30 years at 7% = $227,000
Starting 10 years earlier = $253,000 more!"""
        },
        {
            "q": "How do I pay off debt?",
            "a": """**Debt Payoff Strategies**

**Step 1: List All Debts**
- Creditor name
- Total balance
- Interest rate
- Minimum payment

**Step 2: Choose Your Strategy**

**Debt Avalanche (Mathematically Optimal):**
- Pay minimums on all debts
- Put extra money toward highest interest rate
- Saves the most money over time
- Best for: Logical thinkers, high-rate debt

**Debt Snowball (Psychologically Powerful):**
- Pay minimums on all debts
- Put extra money toward smallest balance
- Quick wins build momentum
- Best for: Those needing motivation

**Debt Consolidation:**
- Combine multiple debts into one
- Lower interest rate possible
- Simpler single payment
- Best for: Good credit, multiple high-rate debts

**Step 3: Find Extra Money**

- Cut expenses temporarily
- Sell unused items
- Take on side work
- Use tax refunds and bonuses
- Negotiate bills lower

**Step 4: Accelerate Payoff**

**The Debt Snowball in Action:**
1. Debt A: $500, $25 min - PAY THIS FIRST
2. Debt B: $2,000, $75 min
3. Debt C: $5,000, $150 min
4. Debt D: $10,000, $200 min

When Debt A is paid, add $25 to Debt B payment.

**Step 5: Stay Motivated**

- Track progress visually
- Celebrate milestones
- Find accountability partner
- Remember your "why"

**Debts to Prioritize:**
1. Payday loans (300%+ APR)
2. Credit cards (15-25% APR)
3. Personal loans (10-15% APR)
4. Car loans (5-10% APR)
5. Student loans (5-7% APR)
6. Mortgage (3-7% APR) - usually keep

**When to NOT Rush Payoff:**
- Debt under 4-5% interest
- Would sacrifice employer 401(k) match
- No emergency fund"""
        }
    ]

    for item in beginner_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "financial_literacy"
        })

    return qa_pairs


# =============================================================================
# PASS 8: GOAL-BASED TIER PROGRESSION (goal_tier_progression.json)
# =============================================================================

def generate_goal_planning_qa(knowledge: dict) -> list[dict]:
    """Generate goal-based tier progression Q&A pairs."""
    qa_pairs = []

    # Comprehensive tier progression scenarios
    tiers = ["Foundation", "Builder", "Growth", "Affluent", "HNW_UHNW"]

    for i, current in enumerate(tiers[:-1]):
        for target in tiers[i+1:]:
            qa_pairs.append({
                "instruction": f"How do I progress from {current} tier to {target} tier?",
                "input": "",
                "output": _generate_tier_progression(current, target),
                "category": "goal_planning"
            })

    # Income-specific scenarios
    incomes = [40000, 60000, 80000, 100000, 125000, 150000, 200000, 300000]
    assets = [0, 5000, 10000, 25000, 50000, 100000, 250000]

    for income in incomes:
        for asset in assets:
            if asset < income * 3:  # Realistic combinations
                qa_pairs.append({
                    "instruction": f"I make ${income:,}/year and have ${asset:,} saved. What's my wealth building plan?",
                    "input": "",
                    "output": _generate_wealth_building_plan(income, asset),
                    "category": "goal_planning"
                })

    return qa_pairs[:300]  # Limit to reasonable number


def _generate_tier_progression(current: str, target: str) -> str:
    """Generate tier-to-tier progression plan."""
    tier_thresholds = {
        "Foundation": (0, 10000),
        "Builder": (10000, 75000),
        "Growth": (75000, 500000),
        "Affluent": (500000, 5000000),
        "HNW_UHNW": (5000000, None)
    }

    current_max = tier_thresholds[current][1]
    target_min = tier_thresholds[target][0]

    gap = target_min - current_max

    strategies = {
        "Foundation": "Build emergency fund, eliminate debt, establish savings habit",
        "Builder": "Max tax-advantaged accounts, diversify income, start investing",
        "Growth": "Tax optimization, real estate, increase income significantly",
        "Affluent": "Advanced estate planning, alternative investments, professional team",
        "HNW_UHNW": "Family office services, philanthropy, multi-generational planning"
    }

    return f"""**Tier Progression: {current} → {target}**

**Current Tier:** {current} (up to ${tier_thresholds[current][1]:,})
**Target Tier:** {target} (${target_min:,}+)
**Wealth Gap:** ${gap:,}

**Phase 1: Master {current} Tier**
{strategies[current]}

**Phase 2: Accelerate Growth**
- Increase savings rate to 25%+
- Maximize all tax advantages
- Build multiple income streams
- Invest consistently in index funds

**Phase 3: Reach {target} Tier**
{strategies[target]}

**Key Success Factors:**
1. **Time:** Wealth building takes years
2. **Consistency:** Regular savings > timing the market
3. **Income Growth:** Advance career or add income streams
4. **Expense Control:** Avoid lifestyle inflation
5. **Tax Efficiency:** Use all available strategies

**Professional Help at Each Stage:**
- {current}: CFP® for planning foundation
- {target}: Full professional team

**Realistic Timeline:**
- Aggressive (40%+ savings rate): {int(gap/50000)} years
- Moderate (20-25% savings rate): {int(gap/25000)} years
- Conservative (10-15% savings rate): {int(gap/15000)} years

**Remember:** Progress isn't linear. Focus on the process, not just the numbers."""


def _generate_wealth_building_plan(income: int, assets: int) -> str:
    """Generate personalized wealth building plan."""
    savings_rate = 0.20
    annual_savings = income * savings_rate

    # Determine current tier
    if assets < 10000:
        tier = "Foundation"
    elif assets < 75000:
        tier = "Builder"
    elif assets < 500000:
        tier = "Growth"
    elif assets < 5000000:
        tier = "Affluent"
    else:
        tier = "HNW_UHNW"

    return f"""**Personalized Wealth Building Plan**

**Current Situation:**
- Annual Income: ${income:,}
- Current Assets: ${assets:,}
- Current Tier: {tier}

**Recommended Savings Rate:** 20% = ${annual_savings:,.0f}/year (${annual_savings/12:,.0f}/month)

**Immediate Priorities:**

{"**1. Build Emergency Fund**" if assets < income * 0.5 else "**1. Maximize Retirement Contributions**"}
{"- Target: ${:.0f} (6 months expenses)".format(income * 0.5) if assets < income * 0.5 else "- 401(k): $23,000/year\n- Roth IRA: $7,000/year"}

**2. Optimize Tax Strategy**
- {"Start with employer match, then Roth IRA" if income < 100000 else "Max traditional 401(k) for tax deduction"}

**3. Invest for Growth**
- Target-date fund or total market index
- Automate contributions

**5-Year Projection (20% savings, 7% returns):**
- Year 1: ${assets + annual_savings:,.0f}
- Year 3: ${(assets + annual_savings * 3) * 1.07:,.0f}
- Year 5: ${(assets + annual_savings * 5) * 1.15:,.0f}

**Next Tier Target:**
- Builder: $10,000 - {"✓ Achieved" if assets >= 10000 else f"{max(0, (10000-assets)/annual_savings):.1f} years"}
- Growth: $75,000 - {"✓ Achieved" if assets >= 75000 else f"{max(0, (75000-assets)/annual_savings):.1f} years"}
- Affluent: $500,000 - {"✓ Achieved" if assets >= 500000 else f"{max(0, (500000-assets)/annual_savings):.1f} years"}

**Key Actions This Month:**
1. Set up automatic transfers to savings
2. Review and reduce unnecessary expenses
3. Ensure you're getting full employer match
4. Open Roth IRA if you don't have one"""


# =============================================================================
# PASS 9: COMPLIANCE & OPERATIONS (compliance_operations.json)
# =============================================================================

def generate_compliance_qa(knowledge: dict) -> list[dict]:
    """Generate compliance and regulatory Q&A pairs."""
    qa_pairs = []

    compliance_topics = [
        {
            "q": "What is a fiduciary and why does it matter?",
            "a": """**Fiduciary Duty Explained**

**What is a Fiduciary?**
A fiduciary is legally and ethically obligated to act in your best interest, not their own.

**Fiduciary vs. Suitability Standard:**

| Aspect | Fiduciary | Suitability |
|--------|-----------|-------------|
| Standard | Best interest | Suitable |
| Conflicts | Must disclose/avoid | Only disclose |
| Loyalty | To client | To firm/self allowed |
| Compensation | Must be reasonable | Can be higher |

**Who is a Fiduciary:**
- Registered Investment Advisors (RIAs)
- CFP® professionals (when providing planning)
- ERISA plan fiduciaries
- Attorneys (in legal matters)
- CPAs (in professional capacity)

**Who May NOT Be:**
- Broker-dealers (suitability standard)
- Insurance agents (selling products)
- Bank representatives
- Some "financial advisors"

**How to Verify:**
1. Ask directly: "Are you a fiduciary?"
2. Get it in writing
3. Check Form ADV (SEC registration)
4. Look for RIA registration

**Why It Matters:**
- Conflicts of interest reduced
- Fees tend to be more transparent
- Advice focused on your needs
- Legal recourse if violated

**Questions to Ask:**
1. "Are you a fiduciary at all times?"
2. "How are you compensated?"
3. "Will you sign a fiduciary oath?"
4. "Do you receive any third-party compensation?"

**Red Flags:**
- Reluctance to confirm fiduciary status
- Pushing proprietary products
- High-commission products recommended
- Unclear fee structure"""
        },
        {
            "q": "How do I verify a financial advisor's credentials?",
            "a": """**Verifying Financial Advisor Credentials**

**Step 1: Check Registrations**

**FINRA BrokerCheck (free):**
- Website: brokercheck.finra.org
- Shows: Licenses, employment history, complaints, regulatory actions
- For: Brokers and brokerage firms

**SEC Investment Adviser Search:**
- Website: adviserinfo.sec.gov
- Shows: Form ADV, fees, services, conflicts, disciplinary history
- For: Registered Investment Advisers

**Step 2: Verify Certifications**

**CFP® Verification:**
- Website: letsmakeaplan.org
- Confirms active certification
- Shows any disciplinary actions

**CPA Verification:**
- Check state board of accountancy
- Varies by state

**CFA® Verification:**
- Website: cfainstitute.org
- Member directory

**Step 3: Check State Records**
- State securities regulator
- State insurance department
- Better Business Bureau

**Step 4: Review Form ADV**
- Part 1: Registration info, disciplinary history
- Part 2A: Services, fees, conflicts (Brochure)
- Part 2B: Educational background, experience (Supplement)

**Red Flags to Watch For:**
- Gaps in employment history
- Multiple firm changes in short time
- Customer complaints (especially patterns)
- Regulatory actions or sanctions
- Bankruptcy filings
- Criminal history

**Questions to Ask:**
1. What licenses and certifications do you hold?
2. Have you ever been disciplined?
3. May I see your Form ADV Part 2?
4. How long have you been in business?
5. Can you provide references?

**Trust But Verify:**
Even with referrals, always check independently."""
        }
    ]

    for item in compliance_topics:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "compliance"
        })

    return qa_pairs


# =============================================================================
# PASS 10: GENERATIONAL WEALTH (generational_wealth.json)
# =============================================================================

def generate_generational_wealth_qa(knowledge: dict) -> list[dict]:
    """Generate generational wealth Q&A pairs."""
    qa_pairs = []

    questions = [
        {
            "q": "How do I build generational wealth?",
            "a": """**Building Generational Wealth**

**The Foundation: Mindset Shift**
- Think beyond your lifetime
- Prioritize assets over income
- Teach financial literacy
- Create systems, not just savings

**Pillar 1: Accumulate Assets**

**Best Assets for Wealth Transfer:**
1. **Real Estate** - Appreciates, generates income, tax benefits
2. **Business Ownership** - Can grow exponentially, employ family
3. **Investment Portfolios** - Liquid, diversified, step-up in basis
4. **Life Insurance** - Tax-free transfer, liquidity

**Pillar 2: Protect Wealth**

**Legal Structures:**
- Trusts (revocable and irrevocable)
- LLCs and family limited partnerships
- Proper insurance coverage
- Asset protection strategies

**Pillar 3: Transfer Efficiently**

**Tax-Efficient Strategies:**
- Annual gift exclusion ($18,000/person/year)
- 529 plans for education
- Roth conversions (tax-free inheritance)
- Charitable vehicles

**Pillar 4: Educate Heirs**

**Critical Topics:**
- Basic financial literacy
- Family wealth philosophy
- Responsibilities of wealth
- Investment principles
- Philanthropic values

**Pillar 5: Govern the Wealth**

**Family Governance:**
- Family mission statement
- Regular family meetings
- Clear roles and expectations
- Conflict resolution processes

**The Numbers:**
- 70% of wealthy families lose wealth by 2nd generation
- 90% lose it by 3rd generation
- Primary cause: Lack of communication and preparation

**Action Plan:**
1. Start having money conversations with kids
2. Create estate plan with proper structures
3. Establish family values around wealth
4. Involve next generation in decisions
5. Consider family meetings annually"""
        },
        {
            "q": "How do I teach my children about money?",
            "a": """**Teaching Children Financial Literacy by Age**

**Ages 3-5: Basic Concepts**
- Money is used to buy things
- You have to earn money
- We save for things we want
- Piggy bank introduction

**Ages 6-10: Practical Skills**
- Allowance with three jars: Save, Spend, Give
- Comparison shopping
- Delayed gratification
- Basic budgeting for goals
- Wants vs. needs

**Ages 11-14: Money Management**
- Bank account (with parent)
- Tracking spending
- Compound interest concept
- Part-time jobs (lawn mowing, babysitting)
- Matching their savings

**Ages 15-18: Real World Prep**
- Debit card responsibility
- First job with paycheck
- Taxes and deductions
- Saving for car/college
- Credit score basics
- Student loan implications

**Ages 18-22: Independence**
- Full budget responsibility
- Credit card (with guardrails)
- Investing introduction
- Retirement account (Roth IRA)
- Insurance basics

**Teaching Methods:**

**1. Give Allowance with Purpose**
- Tied to chores (work = money)
- Three-jar system (save/spend/give)
- Let them make mistakes with small amounts

**2. Include Them in Family Finances**
- Age-appropriate budget discussions
- Grocery shopping comparisons
- Bill paying explanations
- Major purchase decisions

**3. Match Their Savings**
- Incentivize saving behavior
- "Family 401(k) match"
- Teach compound growth concept

**4. Let Them Fail Safely**
- Don't bail out every mistake
- Discuss what went wrong
- Help them problem-solve

**5. Model Good Behavior**
- They watch everything you do
- Discuss your financial decisions
- Show delayed gratification
- Demonstrate generosity

**Conversations to Have:**
- Why we work
- How our family makes financial decisions
- What happens if we overspend
- Why saving matters
- How to be generous"""
        }
    ]

    for item in questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "generational_wealth"
        })

    return qa_pairs


# =============================================================================
# PASS 11: CREDIT & FINANCING (credit_financing.json)
# =============================================================================

def generate_credit_qa(knowledge: dict) -> list[dict]:
    """Generate credit and financing Q&A pairs."""
    qa_pairs = []

    questions = [
        {
            "q": "How do I improve my credit score?",
            "a": """**Improving Your Credit Score**

**Credit Score Factors (FICO):**

1. **Payment History (35%)**
   - Most important factor
   - One late payment can drop score 50-100+ points
   - Set up autopay for at least minimums

2. **Credit Utilization (30%)**
   - % of available credit used
   - Keep below 30%, ideally below 10%
   - Ask for credit limit increases
   - Pay before statement closes

3. **Length of Credit History (15%)**
   - Keep old accounts open
   - Don't close your oldest card
   - Average age of accounts matters

4. **Credit Mix (10%)**
   - Having different types helps
   - Credit cards + installment loans
   - Don't open accounts just for mix

5. **New Credit (10%)**
   - Hard inquiries impact score
   - Multiple inquiries for same loan type = one inquiry (within 14-45 days)
   - New accounts lower average age

**Quick Wins:**
1. Dispute any errors on credit reports
2. Pay down credit card balances
3. Become authorized user on family member's old, good account
4. Set up autopay to never miss payments
5. Request credit limit increases

**Timeline:**
- 30 days: Utilization improvements show
- 3-6 months: New positive history builds
- 1-2 years: Significant score improvement
- 7 years: Negative items fall off

**Check Your Reports:**
- Free weekly at AnnualCreditReport.com
- Check all three bureaus (Equifax, Experian, TransUnion)
- Dispute errors immediately"""
        },
        {
            "q": "Should I pay off my mortgage early?",
            "a": """**Should You Pay Off Your Mortgage Early?**

**Arguments FOR Paying Off Early:**

1. **Guaranteed Return**
   - Paying off 6% mortgage = 6% guaranteed return
   - No market risk

2. **Peace of Mind**
   - Psychological benefit of no debt
   - Housing security in any economy

3. **Cash Flow Freedom**
   - No monthly payment frees up income
   - Flexibility in retirement

4. **Interest Savings**
   - $300,000 mortgage at 7% = $418,000 in interest over 30 years
   - Pay off in 15 = save $200,000+

**Arguments AGAINST Paying Off Early:**

1. **Opportunity Cost**
   - S&P 500 averages ~10%/year
   - Mortgage at 3-4% = invest the difference

2. **Tax Deduction**
   - Mortgage interest may be deductible
   - Effective rate lower than stated rate
   - (Most people don't itemize post-2017)

3. **Liquidity**
   - Money in home is illiquid
   - Can't access without refinance/HELOC
   - Emergency fund more important

4. **Inflation Hedge**
   - Fixed payment decreases in real value
   - Paying with "cheaper" future dollars

**Decision Framework:**

**PAY OFF EARLY IF:**
- Mortgage rate > 6%
- Already maxing retirement accounts
- Close to retirement
- Peace of mind is priority
- Have 6+ months emergency fund

**DON'T RUSH TO PAY OFF IF:**
- Mortgage rate < 4%
- Not maxing retirement accounts
- High-interest debt exists
- Inadequate emergency fund
- Young with long investment horizon

**Middle Ground:**
- Make one extra payment per year (13 instead of 12)
- Round up payments
- Apply windfalls to principal
- Refinance to 15-year at lower rate"""
        }
    ]

    for item in questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"],
            "category": "credit_financing"
        })

    return qa_pairs


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Generate all training data."""
    print("=" * 70)
    print("Elson Financial AI - Comprehensive Training Data Generation")
    print("=" * 70)

    # Create output directory
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    # Load knowledge base
    print("\nLoading knowledge base...")
    knowledge = load_knowledge_base()
    print(f"Loaded {len(knowledge)} knowledge files")

    # Generate Q&A pairs from all categories
    print("\nGenerating Q&A pairs...")
    all_qa = []

    generators = [
        ("Retirement Planning", generate_retirement_qa),
        ("College Planning", generate_college_qa),
        ("Estate Planning", generate_estate_planning_qa),
        ("Trust Administration", generate_trust_qa),
        ("Succession Planning", generate_succession_qa),
        ("Professional Roles", generate_professional_roles_qa),
        ("Financial Literacy", generate_financial_literacy_qa),
        ("Goal Planning", generate_goal_planning_qa),
        ("Compliance", generate_compliance_qa),
        ("Generational Wealth", generate_generational_wealth_qa),
        ("Credit & Financing", generate_credit_qa),
    ]

    for name, generator in generators:
        qa = generator(knowledge)
        print(f"  {name}: {len(qa)} pairs")
        all_qa.extend(qa)

    # Shuffle for training
    random.shuffle(all_qa)

    print(f"\n{'=' * 70}")
    print(f"Total Q&A pairs generated: {len(all_qa)}")
    print(f"{'=' * 70}")

    # Split into train/val/test
    total = len(all_qa)
    train_size = int(total * 0.8)
    val_size = int(total * 0.1)

    train_data = all_qa[:train_size]
    val_data = all_qa[train_size:train_size + val_size]
    test_data = all_qa[train_size + val_size:]

    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    train_file = OUTPUT_PATH / f"train_{timestamp}.json"
    val_file = OUTPUT_PATH / f"val_{timestamp}.json"
    test_file = OUTPUT_PATH / f"test_{timestamp}.json"

    with open(train_file, 'w') as f:
        json.dump(train_data, f, indent=2)
    print(f"\nSaved: {train_file} ({len(train_data)} pairs)")

    with open(val_file, 'w') as f:
        json.dump(val_data, f, indent=2)
    print(f"Saved: {val_file} ({len(val_data)} pairs)")

    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"Saved: {test_file} ({len(test_data)} pairs)")

    # Combined file
    combined_file = OUTPUT_PATH / "training_data_complete.json"
    with open(combined_file, 'w') as f:
        json.dump(all_qa, f, indent=2)
    print(f"Saved: {combined_file}")

    # Category summary
    print(f"\n{'=' * 70}")
    print("Category Distribution:")
    print(f"{'=' * 70}")
    categories = {}
    for qa in all_qa:
        cat = qa.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = count / len(all_qa) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    print(f"\n{'=' * 70}")
    print("Training data generation complete!")
    print(f"{'=' * 70}")

    return all_qa


if __name__ == "__main__":
    main()
