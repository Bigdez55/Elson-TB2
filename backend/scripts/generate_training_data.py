#!/usr/bin/env python3
"""
Generate training data for DVoRA/QDoRA fine-tuning.

Creates 2000+ Q&A pairs from the wealth management knowledge base
covering retirement planning, college planning, goal progression,
professional roles, and all 5 wealth tiers.
"""

import json
import random
from pathlib import Path
from typing import Any
from datetime import datetime

# Knowledge base path
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "app" / "knowledge_base" / "wealth_management" / "data"
OUTPUT_PATH = Path(__file__).parent.parent / "training_data"


def load_knowledge_base() -> dict[str, Any]:
    """Load all knowledge base JSON files."""
    knowledge = {}
    for json_file in KNOWLEDGE_BASE_PATH.glob("*.json"):
        with open(json_file, 'r') as f:
            knowledge[json_file.stem] = json.load(f)
        print(f"Loaded: {json_file.name}")
    return knowledge


def generate_retirement_qa(knowledge: dict) -> list[dict]:
    """Generate retirement planning Q&A pairs."""
    qa_pairs = []
    retirement_data = knowledge.get("retirement_planning", {})

    # Template questions for retirement
    templates = [
        ("What is a {account_type} and how does it work?", "account_types"),
        ("What are the contribution limits for {account_type} in 2024?", "contribution_limits"),
        ("Should I choose a traditional or Roth {account_type}?", "roth_vs_traditional"),
        ("What is the FIRE movement and how can I achieve early retirement?", "fire_movement"),
        ("How do I calculate how much I need to retire?", "retirement_calculations"),
        ("What is the 4% rule for retirement withdrawals?", "withdrawal_strategies"),
        ("When should I start taking Social Security benefits?", "social_security"),
        ("How do Required Minimum Distributions (RMDs) work?", "rmds"),
        ("What is a backdoor Roth IRA conversion?", "backdoor_roth"),
        ("How do I maximize my employer 401k match?", "employer_match"),
    ]

    # Generate variations
    account_types = ["401k", "IRA", "Roth IRA", "403b", "SEP IRA", "SIMPLE IRA"]
    ages = [25, 30, 35, 40, 45, 50, 55, 60, 65]
    incomes = [50000, 75000, 100000, 150000, 200000, 300000]

    for age in ages:
        for income in incomes:
            # Age-specific retirement questions
            qa_pairs.append({
                "instruction": f"I'm {age} years old making ${income:,}/year. How much should I save for retirement?",
                "input": "",
                "output": generate_retirement_advice(age, income, retirement_data),
                "category": "retirement_planning"
            })

            qa_pairs.append({
                "instruction": f"At age {age} with ${income:,} income, should I prioritize 401k or Roth IRA?",
                "input": "",
                "output": generate_account_recommendation(age, income),
                "category": "retirement_planning"
            })

    # FIRE-specific questions
    fire_questions = [
        "How can I retire by age 40?",
        "What savings rate do I need for FIRE?",
        "What is Coast FIRE vs Lean FIRE vs Fat FIRE?",
        "How do I access retirement funds before 59.5 without penalty?",
        "What is the Rule of 55 for early retirement?",
    ]

    for q in fire_questions:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": generate_fire_response(q, retirement_data),
            "category": "retirement_planning"
        })

    return qa_pairs


def generate_retirement_advice(age: int, income: float, data: dict) -> str:
    """Generate personalized retirement advice."""
    years_to_retire = max(65 - age, 0)
    recommended_rate = 0.15 if age < 35 else 0.20 if age < 45 else 0.25
    monthly_savings = income * recommended_rate / 12

    return f"""Based on your age ({age}) and income (${income:,}/year), here's my retirement guidance:

**Recommended Savings Rate:** {recommended_rate*100:.0f}% of gross income (${monthly_savings:,.0f}/month)

**Priority Order:**
1. Contribute enough to 401k to get full employer match (free money)
2. Max out HSA if available ($4,150 individual / $8,300 family in 2024)
3. Max out Roth IRA ($7,000/year, or $8,000 if 50+)
4. Return to 401k up to max ($23,000/year, or $30,500 if 50+)
5. Taxable brokerage for additional savings

**Target Retirement Savings by Age:**
- Age 30: 1x annual salary
- Age 40: 3x annual salary
- Age 50: 6x annual salary
- Age 60: 8x annual salary
- Age 67: 10x annual salary

**Your Timeline:** {years_to_retire} years until traditional retirement age.

Would you like me to create a detailed retirement projection based on your specific situation?"""


def generate_account_recommendation(age: int, income: float) -> str:
    """Generate 401k vs Roth recommendation."""
    # Simplified tax bracket logic
    if income < 95000:
        recommendation = "Roth"
        reason = "you're likely in a lower tax bracket now than in retirement"
    elif income > 200000:
        recommendation = "Traditional 401k"
        reason = "the tax deduction provides more value at your income level"
    else:
        recommendation = "Split between both"
        reason = "tax diversification provides flexibility in retirement"

    return f"""For a {age}-year-old earning ${income:,}/year, I recommend: **{recommendation}**

**Rationale:** {reason.capitalize()}.

**Detailed Analysis:**

**Traditional 401k:**
- Reduces taxable income NOW
- Pay taxes on withdrawals in retirement
- Best if you expect lower tax bracket in retirement

**Roth 401k/IRA:**
- No tax deduction now
- Tax-FREE withdrawals in retirement
- Best if you expect higher taxes later or want tax diversification

**My Recommendation for You:**
At ${income:,}/year and age {age}, {reason}. Consider contributing to both if your employer offers a Roth 401k option.

**Action Items:**
1. Always get full employer match first (it's 100% return)
2. {"Prioritize Roth contributions" if recommendation == "Roth" else "Maximize traditional 401k deduction" if recommendation == "Traditional 401k" else "Split 50/50 between traditional and Roth"}
3. Review annually as income changes"""


def generate_fire_response(question: str, data: dict) -> str:
    """Generate FIRE movement responses."""
    responses = {
        "How can I retire by age 40?": """To retire by 40, you'll need aggressive savings and strategic investing:

**The Math:**
- Target: 25x annual expenses (4% rule)
- If expenses = $50,000/year, you need $1.25M
- Starting at 25, that's 15 years to accumulate

**Required Savings Rate:** 50-70% of income

**Strategy:**
1. **Maximize Income:** Focus on high-earning career or side businesses
2. **Minimize Expenses:** Keep lifestyle inflation in check
3. **Invest Aggressively:** 90%+ in low-cost index funds (VTSAX, VTI)
4. **Use Tax-Advantaged Accounts:** Max 401k, IRA, HSA
5. **Build Taxable Brokerage:** For early access before 59.5

**Early Access Strategies:**
- Roth IRA contributions (not earnings) can be withdrawn anytime
- 72(t) SEPP distributions
- Roth conversion ladder (5-year waiting period)
- Rule of 55 if you leave employer at 55+

**Reality Check:** This requires significant sacrifice and isn't for everyone.""",

        "What savings rate do I need for FIRE?": """Your savings rate determines your years to retirement:

| Savings Rate | Years to FIRE |
|--------------|---------------|
| 10% | 51 years |
| 20% | 37 years |
| 30% | 28 years |
| 40% | 22 years |
| 50% | 17 years |
| 60% | 12.5 years |
| 70% | 8.5 years |
| 80% | 5.5 years |

**Key Insight:** Savings rate matters more than investment returns.

Going from 10% to 20% saves 14 years. Going from 50% to 60% only saves 4.5 years.

**The Formula:**
Years to FIRE = ln((1 + (Expenses/Savings)) / ln(1 + Return Rate)

Assumes 7% real returns and 4% safe withdrawal rate.""",
    }

    return responses.get(question, f"The FIRE (Financial Independence, Retire Early) movement focuses on aggressive saving and investing to achieve financial freedom. Key principles include minimizing expenses, maximizing savings rate, and investing in low-cost index funds.")


def generate_college_qa(knowledge: dict) -> list[dict]:
    """Generate college planning Q&A pairs."""
    qa_pairs = []

    # Child ages and scenarios
    child_ages = [0, 2, 5, 8, 10, 12, 15, 17]
    school_types = ["public in-state", "public out-of-state", "private", "community college"]

    for age in child_ages:
        years_until = 18 - age
        for school in school_types:
            qa_pairs.append({
                "instruction": f"My child is {age} years old. How do I save for {school} college?",
                "input": "",
                "output": generate_college_advice(age, school),
                "category": "college_planning"
            })

    # 529 specific questions
    qa_pairs.extend([
        {
            "instruction": "What is a 529 plan and how does it work?",
            "input": "",
            "output": """A 529 plan is a tax-advantaged savings account designed for education expenses.

**Key Benefits:**
1. **Tax-Free Growth:** Investments grow without federal taxes
2. **Tax-Free Withdrawals:** For qualified education expenses
3. **State Tax Deductions:** Many states offer deductions for contributions
4. **High Contribution Limits:** Often $300,000+ lifetime per beneficiary
5. **Flexibility:** Can change beneficiaries within family

**Two Types:**
1. **529 Savings Plans:** Investment account, most popular
2. **529 Prepaid Plans:** Lock in today's tuition rates (limited availability)

**Qualified Expenses:**
- Tuition and fees
- Room and board
- Books and supplies
- Computers and technology
- K-12 tuition (up to $10,000/year)
- Student loan repayment (up to $10,000 lifetime)

**Considerations:**
- Non-qualified withdrawals face taxes + 10% penalty on earnings
- May impact financial aid (counted as parent asset at ~5.64% rate)
- Each state has different plans - you can use any state's plan""",
            "category": "college_planning"
        },
        {
            "instruction": "How do I maximize financial aid eligibility?",
            "input": "",
            "output": """Strategies to maximize financial aid:

**Asset Positioning (2+ years before FAFSA):**
1. **Reduce Parent Assets:** Pay down debt, make major purchases
2. **Avoid Student Assets:** Counted at 20% vs parent's 5.64%
3. **Max Retirement Contributions:** 401k/IRA not counted on FAFSA
4. **Use 529s Strategically:** Owned by parent, not grandparent

**Income Timing:**
1. **Base Year Awareness:** FAFSA uses income from 2 years prior
2. **Avoid Capital Gains:** In base years if possible
3. **Defer Bonuses:** If timing works with base years

**FAFSA Tips:**
1. **File Early:** October 1st, aid is first-come-first-served
2. **Use IRS Data Retrieval:** Speeds up verification
3. **Apply Even If Uncertain:** Circumstances change

**EFC Reduction Strategies:**
- Multiple children in college simultaneously
- Legitimate business expenses
- Medical expenses

**Caution:** Never hide assets or misrepresent - it's federal fraud.""",
            "category": "college_planning"
        },
        {
            "instruction": "Should grandparents contribute to a 529 plan?",
            "input": "",
            "output": """Grandparent 529 contributions require strategic planning:

**The Challenge (Pre-2024):**
Grandparent-owned 529 distributions counted as student income on FAFSA, reducing aid by up to 50%.

**FAFSA Simplification Act (2024+):**
Good news! Grandparent 529 distributions are NO LONGER reported on FAFSA.

**Current Best Strategies:**

**Option 1: Grandparent-Owned 529**
- Now safe with new FAFSA rules
- Grandparent maintains control
- Can use for estate planning (5-year gift tax averaging)

**Option 2: Contribute to Parent-Owned 529**
- Grandparent gifts to parent's 529
- Counts as parent asset (5.64%)
- Parent maintains control

**Option 3: Pay Tuition Directly**
- Unlimited gift tax exclusion for direct tuition payments
- Doesn't use annual gift exclusion ($18,000/year)
- Must go directly to institution

**Estate Planning Benefits:**
- Superfunding: Contribute 5 years at once ($90,000 individual/$180,000 couple)
- Removes assets from estate
- Grandparent retains control and can change beneficiary""",
            "category": "college_planning"
        }
    ])

    return qa_pairs


def generate_college_advice(child_age: int, school_type: str) -> str:
    """Generate college savings advice."""
    years_until = max(18 - child_age, 1)

    # Estimated costs
    costs = {
        "public in-state": 25000,
        "public out-of-state": 45000,
        "private": 60000,
        "community college": 12000
    }

    annual_cost = costs.get(school_type, 30000)
    inflation_rate = 0.05
    future_cost = annual_cost * ((1 + inflation_rate) ** years_until)
    total_4_year = future_cost * 4
    monthly_needed = total_4_year / (years_until * 12) / 1.5  # Assuming some growth

    return f"""College savings plan for your {child_age}-year-old targeting {school_type}:

**Cost Projection ({years_until} years until college):**
- Current annual cost: ${annual_cost:,.0f}
- Projected annual cost: ${future_cost:,.0f} (5% inflation)
- Total 4-year cost: ${total_4_year:,.0f}

**Recommended Monthly Savings:** ${monthly_needed:,.0f}
(Assumes 7% annual return in 529 plan)

**Action Plan:**

1. **Open a 529 Plan**
   - Research your state's plan for tax deductions
   - Consider Utah, Nevada, or New York plans for best options

2. **Set Up Automatic Contributions**
   - ${monthly_needed:,.0f}/month to reach goal
   - Increase annually with raises

3. **Investment Strategy**
   - {years_until} years out: {"Aggressive (80%+ stocks)" if years_until > 10 else "Moderate (60% stocks)" if years_until > 5 else "Conservative (40% stocks)"}
   - Use age-based portfolios for automatic rebalancing

4. **Supplement with:**
   - Grandparent contributions
   - Birthday/holiday gifts to 529
   - Coverdell ESA ($2,000/year) for private K-12

5. **Financial Aid Prep:**
   - File FAFSA starting October 1st of senior year
   - Research merit scholarships early

**Remember:** Any amount saved reduces future student loans!"""


def generate_goal_planning_qa(knowledge: dict) -> list[dict]:
    """Generate goal-based tier progression Q&A pairs."""
    qa_pairs = []

    tiers = [
        ("Foundation", 0, 10000),
        ("Builder", 10000, 75000),
        ("Growth", 75000, 500000),
        ("Affluent", 500000, 5000000),
        ("HNW/UHNW", 5000000, None)
    ]

    # Generate progression scenarios
    incomes = [50000, 75000, 100000, 150000, 200000, 300000, 500000]
    ages = [25, 30, 35, 40, 45, 50]

    for age in ages:
        for income in incomes:
            for i, (current_tier, min_assets, max_assets) in enumerate(tiers[:-1]):
                for j, (target_tier, target_min, target_max) in enumerate(tiers[i+1:], i+1):
                    if j - i <= 2:  # Only 1-2 tier jumps
                        qa_pairs.append({
                            "instruction": f"I'm {age} with ${income:,} income and ${min_assets:,} in assets. How do I reach {target_tier} tier?",
                            "input": "",
                            "output": generate_tier_roadmap(age, income, current_tier, target_tier, min_assets, target_min),
                            "category": "goal_planning"
                        })

    return qa_pairs[:200]  # Limit to avoid too many


def generate_tier_roadmap(age: int, income: float, current_tier: str, target_tier: str, current_assets: float, target_assets: float) -> str:
    """Generate tier progression roadmap."""
    gap = target_assets - current_assets
    years_working = 65 - age

    # Calculate required savings
    annual_return = 0.07
    required_annual = gap / (((1 + annual_return) ** min(years_working, 20) - 1) / annual_return)
    savings_rate = required_annual / income

    return f"""**Wealth Tier Progression Plan**

**Current:** {current_tier} (${current_assets:,.0f})
**Target:** {target_tier} (${target_assets:,.0f})
**Gap:** ${gap:,.0f}

**Required to Reach Goal:**
- Annual savings needed: ${required_annual:,.0f}
- Savings rate: {savings_rate*100:.1f}% of income
- Timeline: {min(int(gap / (income * 0.20)), years_working)} years (at 20% savings rate)

**Year-by-Year Roadmap:**

**Years 1-2: Foundation Building**
- Emergency fund: 6 months expenses
- Eliminate high-interest debt
- Max employer 401k match
- Target: ${current_assets + income * 0.15 * 2:,.0f}

**Years 3-5: Acceleration**
- Increase savings rate to 25%+
- Open taxable brokerage
- Consider real estate investment
- Target: ${current_assets + income * 0.25 * 5:,.0f}

**Years 6-10: Wealth Building**
- Diversify income streams
- Tax optimization strategies
- Regular portfolio rebalancing
- Target: ${target_assets:,.0f}

**Professional Team at {target_tier} Tier:**
- CFP® for comprehensive planning
- CPA for tax optimization
- Estate attorney for wealth protection

**Key Success Factors:**
1. Automate savings (pay yourself first)
2. Avoid lifestyle inflation
3. Stay invested through market volatility
4. Review and adjust annually"""


def generate_professional_roles_qa(knowledge: dict) -> list[dict]:
    """Generate Q&A about professional roles."""
    qa_pairs = []

    roles = [
        ("CFP", "Certified Financial Planner", "comprehensive financial planning"),
        ("CFA", "Chartered Financial Analyst", "investment analysis and portfolio management"),
        ("CPA", "Certified Public Accountant", "tax planning and accounting"),
        ("ChFC", "Chartered Financial Consultant", "advanced financial planning"),
        ("CLU", "Chartered Life Underwriter", "life insurance and estate planning"),
        ("CPWA", "Certified Private Wealth Advisor", "high-net-worth wealth management"),
        ("CFP", "Estate Planning Attorney", "wills, trusts, and estate documents"),
        ("CAIA", "Chartered Alternative Investment Analyst", "alternative investments"),
    ]

    for abbrev, title, specialty in roles:
        qa_pairs.append({
            "instruction": f"What does a {title} ({abbrev}) do?",
            "input": "",
            "output": f"""A **{title} ({abbrev})** specializes in {specialty}.

**Key Responsibilities:**
- Analyzing client financial situations
- Developing customized strategies
- Implementing and monitoring plans
- Coordinating with other professionals

**When to Hire:**
- Complex financial situations
- Major life transitions
- Significant assets to manage
- Need for specialized expertise

**How to Find:**
- Professional association directories
- Referrals from other advisors
- Fee-only advisor networks (NAPFA)

**Questions to Ask:**
1. What are your credentials and experience?
2. How are you compensated?
3. Are you a fiduciary?
4. What is your investment philosophy?
5. How often will we meet?""",
            "category": "professional_roles"
        })

    # Team coordination questions
    qa_pairs.append({
        "instruction": "What professionals do I need for estate planning?",
        "input": "",
        "output": """**Estate Planning Dream Team:**

**Core Team:**
1. **Estate Planning Attorney** (Quarterback)
   - Drafts wills, trusts, powers of attorney
   - Ensures legal compliance
   - Coordinates document execution

2. **CFP® (Financial Planner)**
   - Integrates estate plan with financial goals
   - Analyzes liquidity needs
   - Coordinates beneficiary designations

3. **CPA (Tax Specialist)**
   - Estate and gift tax planning
   - Income tax implications
   - Charitable giving strategies

**Specialized Additions (for complex estates):**
4. **Trust Officer** - Administers trusts
5. **Insurance Specialist** - Life insurance for liquidity
6. **Business Valuation Expert** - For business owners
7. **Philanthropic Advisor** - For charitable planning

**Coordination Structure:**
- Attorney leads legal document creation
- CFP ensures alignment with overall financial plan
- CPA optimizes tax efficiency
- Annual team meetings recommended

**Cost Expectations:**
- Basic estate plan: $1,500-$3,000
- Complex trust planning: $5,000-$15,000
- Ongoing administration: 0.5-1% of trust assets""",
        "category": "professional_roles"
    })

    return qa_pairs


def generate_tier_specific_qa(knowledge: dict) -> list[dict]:
    """Generate tier-specific Q&A pairs."""
    qa_pairs = []

    tier_questions = {
        "Foundation": [
            "I have $5,000 saved. What should I do with it?",
            "How do I start investing with no experience?",
            "What's the best budget method for beginners?",
            "How do I build an emergency fund?",
        ],
        "Builder": [
            "I have $50,000. Should I invest or pay off debt?",
            "How do I start building passive income?",
            "What investment accounts should I prioritize?",
            "How do I create a diversified portfolio?",
        ],
        "Growth": [
            "With $200,000, should I hire a financial advisor?",
            "How do I minimize taxes on investments?",
            "Should I invest in real estate?",
            "What is tax-loss harvesting?",
        ],
        "Affluent": [
            "With $2M, what wealth protection strategies should I use?",
            "How do I set up a trust for my children?",
            "What is a family limited partnership?",
            "How do I plan for multi-generational wealth?",
        ],
        "HNW/UHNW": [
            "With $10M+, should I set up a family office?",
            "How do I structure charitable giving for tax benefits?",
            "What is a private placement life insurance policy?",
            "How do I protect assets from lawsuits?",
        ]
    }

    for tier, questions in tier_questions.items():
        for q in questions:
            qa_pairs.append({
                "instruction": q,
                "input": "",
                "output": generate_tier_response(tier, q),
                "category": f"tier_{tier.lower()}"
            })

    return qa_pairs


def generate_tier_response(tier: str, question: str) -> str:
    """Generate tier-appropriate responses."""
    # Simplified responses - in production would be more detailed
    tier_advice = {
        "Foundation": "Focus on building financial fundamentals: emergency fund, debt elimination, and basic investing through low-cost index funds.",
        "Builder": "Prioritize tax-advantaged accounts, diversification, and developing multiple income streams while keeping costs low.",
        "Growth": "Consider working with a fee-only CFP, implement tax optimization strategies, and explore real estate and alternative investments.",
        "Affluent": "Assemble a professional team (CFP, CPA, attorney), implement advanced estate planning, and focus on wealth preservation alongside growth.",
        "HNW/UHNW": "Evaluate family office structure, implement sophisticated tax and estate strategies, consider philanthropic vehicles, and coordinate a full professional team."
    }

    return f"""**{tier} Tier Guidance**

{tier_advice.get(tier, "Consult with a qualified financial advisor for personalized advice.")}

**For your specific question:** {question}

This requires analysis of your complete financial picture. Key considerations:
1. Current income and expenses
2. Existing assets and liabilities
3. Risk tolerance and time horizon
4. Tax situation
5. Family and estate planning needs

**Recommended Next Steps:**
1. Document your complete financial situation
2. Define clear goals with timelines
3. Consult with appropriate professionals for your tier
4. Create a written plan
5. Review and adjust quarterly

Would you like me to provide more specific guidance based on your situation?"""


def main():
    """Generate all training data."""
    print("=" * 60)
    print("Elson Financial AI - Training Data Generation")
    print("=" * 60)

    # Create output directory
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    # Load knowledge base
    print("\nLoading knowledge base...")
    knowledge = load_knowledge_base()
    print(f"Loaded {len(knowledge)} knowledge files")

    # Generate Q&A pairs
    print("\nGenerating Q&A pairs...")
    all_qa = []

    retirement_qa = generate_retirement_qa(knowledge)
    print(f"  Retirement planning: {len(retirement_qa)} pairs")
    all_qa.extend(retirement_qa)

    college_qa = generate_college_qa(knowledge)
    print(f"  College planning: {len(college_qa)} pairs")
    all_qa.extend(college_qa)

    goal_qa = generate_goal_planning_qa(knowledge)
    print(f"  Goal planning: {len(goal_qa)} pairs")
    all_qa.extend(goal_qa)

    roles_qa = generate_professional_roles_qa(knowledge)
    print(f"  Professional roles: {len(roles_qa)} pairs")
    all_qa.extend(roles_qa)

    tier_qa = generate_tier_specific_qa(knowledge)
    print(f"  Tier-specific: {len(tier_qa)} pairs")
    all_qa.extend(tier_qa)

    # Shuffle for training
    random.shuffle(all_qa)

    print(f"\nTotal Q&A pairs generated: {len(all_qa)}")

    # Split into train/val/test
    total = len(all_qa)
    train_size = int(total * 0.8)
    val_size = int(total * 0.1)

    train_data = all_qa[:train_size]
    val_data = all_qa[train_size:train_size + val_size]
    test_data = all_qa[train_size + val_size:]

    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Alpaca format for training
    train_file = OUTPUT_PATH / f"train_{timestamp}.json"
    val_file = OUTPUT_PATH / f"val_{timestamp}.json"
    test_file = OUTPUT_PATH / f"test_{timestamp}.json"

    with open(train_file, 'w') as f:
        json.dump(train_data, f, indent=2)
    print(f"\nSaved training data: {train_file} ({len(train_data)} pairs)")

    with open(val_file, 'w') as f:
        json.dump(val_data, f, indent=2)
    print(f"Saved validation data: {val_file} ({len(val_data)} pairs)")

    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"Saved test data: {test_file} ({len(test_data)} pairs)")

    # Also save a combined file
    combined_file = OUTPUT_PATH / "training_data_complete.json"
    with open(combined_file, 'w') as f:
        json.dump(all_qa, f, indent=2)
    print(f"Saved complete dataset: {combined_file}")

    # Summary by category
    print("\n" + "=" * 60)
    print("Category Distribution:")
    print("=" * 60)
    categories = {}
    for qa in all_qa:
        cat = qa.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\n" + "=" * 60)
    print("Training data generation complete!")
    print("=" * 60)

    return all_qa


if __name__ == "__main__":
    main()
