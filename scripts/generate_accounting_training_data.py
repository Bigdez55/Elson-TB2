"""
Generate Accounting/Budgeting Training Data for Elson Financial AI

Target: 5,000 - 10,000 accounting and personal finance Q&A pairs
Focus: Budgeting, cash flow, bookkeeping basics, small business

Key Principle: Help with organization and education, but NEVER:
- Provide specific tax calculations
- Give tax filing instructions
- Help with tax evasion
"""

import json
import random
from datetime import datetime
from typing import List, Dict
from pathlib import Path


# =============================================================================
# DISCLAIMERS
# =============================================================================

STANDARD_DISCLAIMER = (
    "\n\n*This information is for educational purposes only. "
    "Consult a CPA or financial advisor for personalized advice.*"
)

TAX_DISCLAIMER = (
    "\n\n*Tax rules change annually. Verify current rules with IRS publications "
    "or a qualified tax professional (CPA or EA).*"
)


# =============================================================================
# BUDGETING Q&A
# =============================================================================

BUDGETING_QA = [
    {
        "instruction": "What is the 50/30/20 budget rule and how do I use it?",
        "output": """The 50/30/20 rule is a simple budgeting framework that divides your after-tax income into three categories:

**50% - Needs (Essential Expenses)**
- Housing (rent/mortgage)
- Utilities
- Groceries
- Transportation
- Insurance
- Minimum debt payments
- Healthcare

**30% - Wants (Discretionary)**
- Dining out
- Entertainment
- Subscriptions
- Shopping
- Hobbies
- Vacations

**20% - Savings & Debt Payoff**
- Emergency fund
- Retirement contributions
- Extra debt payments
- Investments
- Short-term savings goals

**Example on $5,000/month take-home:**
- Needs: $2,500
- Wants: $1,500
- Savings: $1,000

**How to Start:**
1. Calculate your after-tax monthly income
2. List all expenses and categorize them
3. Compare to 50/30/20 targets
4. Adjust spending to align with goals

**When It Doesn't Fit:**
- High cost-of-living areas may need 60/20/20
- High debt may need 50/20/30 (more to debt)
- Adjust based on your priorities""" + STANDARD_DISCLAIMER,
        "category": "budgeting"
    },
    {
        "instruction": "How do I create a budget when my income varies each month?",
        "output": """Variable income budgeting requires a different approach than fixed-salary budgeting:

**Method 1: Baseline Budget**
1. Calculate your minimum monthly income (worst month)
2. Budget essentials based on this minimum
3. Create a plan for "extra" income when it comes

**Method 2: Zero-Based Rolling Average**
1. Average your last 6-12 months of income
2. Budget based on this average
3. Save surplus months for lean months

**Method 3: Priority-Based Allocation**
Create a prioritized list:
1. **Tier 1** (Must Pay): Rent, utilities, food, insurance
2. **Tier 2** (Important): Debt minimums, transportation
3. **Tier 3** (Goals): Emergency fund, retirement
4. **Tier 4** (Wants): Entertainment, dining out

Pay in order as income arrives.

**Buffer Account Strategy:**
- Keep 1-2 months expenses in checking as a buffer
- "Pay yourself" a consistent monthly amount
- Let buffer absorb income fluctuations

**Practical Tips:**
- Track income patterns (seasonal? client-dependent?)
- Build larger emergency fund (6+ months)
- Avoid fixed payments you can't cover in low months
- Consider separate business/personal accounts""" + STANDARD_DISCLAIMER,
        "category": "budgeting"
    },
    {
        "instruction": "What's the difference between needs and wants in a budget?",
        "output": """The distinction between needs and wants can be tricky. Here's a framework:

**Needs (Essentials)**
Expenses required to maintain basic living and employment:

| Category | Need | Want |
|----------|------|------|
| Housing | Basic rent/mortgage | Larger home than necessary |
| Food | Groceries for cooking | Restaurant meals |
| Transportation | Basic reliable car | Luxury vehicle |
| Clothing | Work-appropriate attire | Designer labels |
| Phone | Basic phone plan | Unlimited everything |
| Healthcare | Insurance, medications | Elective procedures |

**Gray Areas - Questions to Ask:**
1. Would I lose my job without this? (Work clothes = need)
2. Would my health suffer without this? (Gym might be need)
3. Could I survive without it for a month? (If yes, probably want)
4. Is there a cheaper alternative? (The upgrade is the "want")

**Common Misclassifications:**
- Internet: Often a need (work from home, job searching)
- Car payment: Need = reliable transport; Want = the premium upgrade
- Childcare: Usually a need for working parents
- Subscriptions: Usually wants (even if it feels essential)

**The Test:**
If you lost your income tomorrow, which expenses would you cut immediately? Those are likely wants. What would you keep paying no matter what? Those are needs.

**Remember:** The goal isn't to eliminate wants—it's to be intentional about the balance.""" + STANDARD_DISCLAIMER,
        "category": "budgeting"
    },
    {
        "instruction": "How much should I have in my emergency fund?",
        "output": """Emergency fund size depends on your situation, but here are general guidelines:

**Standard Recommendation: 3-6 Months of Expenses**

| Situation | Recommended Amount |
|-----------|-------------------|
| Stable job, dual income | 3 months |
| Single income, stable job | 4-6 months |
| Variable income / freelance | 6-9 months |
| Single parent | 6-9 months |
| High-risk industry | 6-12 months |

**Calculate Your Number:**
1. List essential monthly expenses only:
   - Housing, utilities, food, insurance, transportation, minimum debt payments
2. Multiply by your target months
3. That's your emergency fund goal

**Example:**
- Essential expenses: $3,500/month
- Target: 6 months
- Emergency fund goal: $21,000

**Where to Keep It:**
- High-yield savings account (HYSA)
- Money market account
- NOT investments (too volatile)
- Separate from regular checking (reduce temptation)

**Building Strategy:**
1. Start with $1,000 mini emergency fund
2. Pay off high-interest debt
3. Build to 1 month expenses
4. Continue to full target

**What Counts as Emergency:**
✓ Job loss
✓ Medical emergency
✓ Essential car repair
✓ Emergency home repair

**Not Emergencies:**
✗ Vacation
✗ Holiday shopping
✗ Sale "too good to pass up"
✗ Planned expenses you forgot to budget""" + STANDARD_DISCLAIMER,
        "category": "budgeting"
    },
]


# =============================================================================
# CASH FLOW Q&A
# =============================================================================

CASH_FLOW_QA = [
    {
        "instruction": "How do I create a cash flow forecast for my personal finances?",
        "output": """A personal cash flow forecast helps you see your financial future and avoid surprises:

**Step 1: List All Income Sources**
- Salary/wages (net after taxes)
- Side income
- Investment income
- Any other regular income

**Step 2: List Fixed Expenses**
(Same amount each month)
- Rent/mortgage
- Car payment
- Insurance premiums
- Subscriptions
- Loan payments

**Step 3: Estimate Variable Expenses**
(Fluctuate monthly)
- Groceries
- Utilities
- Gas
- Entertainment
- Dining out

**Step 4: Note Irregular Expenses**
(Not monthly)
- Annual insurance premiums
- Property taxes
- Car registration
- Holiday spending
- Vacations

**Step 5: Build the Forecast**

| Month | Beginning Balance | + Income | - Expenses | = Ending Balance |
|-------|------------------|----------|------------|------------------|
| Jan   | $5,000          | $4,500   | $4,200     | $5,300          |
| Feb   | $5,300          | $4,500   | $4,000     | $5,800          |
| Mar   | $5,800          | $4,500   | $5,500*    | $4,800          |

*March includes annual insurance payment

**Key Metrics to Track:**
- Lowest projected balance (your danger point)
- Average monthly surplus/deficit
- Months where you'll need extra cash

**Update Regularly:**
- Weekly: Track actual spending
- Monthly: Compare forecast to actual
- Quarterly: Adjust projections""" + STANDARD_DISCLAIMER,
        "category": "cash_flow"
    },
    {
        "instruction": "I'm living paycheck to paycheck. How do I break the cycle?",
        "output": """Breaking the paycheck-to-paycheck cycle takes time but is absolutely possible:

**Phase 1: Stabilize (Month 1-2)**
1. Track every dollar for 30 days
2. Identify your actual spending patterns
3. Find your "leaks" - small expenses that add up
4. Cut 1-2 non-essential expenses immediately

**Phase 2: Create Breathing Room (Month 2-4)**
1. Build a $500-1,000 mini emergency fund
   - Sell unused items
   - Pick up extra hours/gig work
   - Redirect any "found money"
2. This stops the spiral of debt when surprises hit

**Phase 3: Get Ahead (Month 4-8)**
1. Budget to live on last month's income:
   - Save one month's expenses
   - Then start each month already "paid"
2. Continue building emergency fund

**Quick Wins:**
- Negotiate bills (internet, insurance, phone)
- Meal prep to reduce food costs
- Cancel unused subscriptions
- Use cash for discretionary spending
- Avoid lifestyle inflation

**Mindset Shifts:**
- Small progress compounds
- One month buffer changes everything
- "I can't afford it" → "It's not a priority right now"
- Stop comparing to others' spending

**Warning Signs to Address:**
- Using credit cards for essentials
- Overdraft fees as a regular occurrence
- Borrowing to pay bills
- Skipping bills to cover others

**If Income Is the Problem:**
Sometimes cutting isn't enough. Consider:
- Asking for a raise
- Seeking higher-paying position
- Adding income streams
- Reducing housing costs (biggest lever)""" + STANDARD_DISCLAIMER,
        "category": "cash_flow"
    },
]


# =============================================================================
# BOOKKEEPING BASICS Q&A
# =============================================================================

BOOKKEEPING_QA = [
    {
        "instruction": "What's the difference between a balance sheet and an income statement?",
        "output": """These are the two fundamental financial statements:

**Balance Sheet (Statement of Financial Position)**
- Shows financial position at a **specific point in time**
- Like a snapshot or photograph
- Answers: "What do I own and owe right now?"

Structure:
```
Assets = Liabilities + Equity

ASSETS (What you own)
- Cash: $10,000
- Investments: $50,000
- Home: $300,000
- Car: $15,000
Total Assets: $375,000

LIABILITIES (What you owe)
- Credit cards: $2,000
- Car loan: $10,000
- Mortgage: $250,000
Total Liabilities: $262,000

NET WORTH (Equity)
Assets - Liabilities = $113,000
```

**Income Statement (Profit & Loss)**
- Shows financial activity over a **period of time**
- Like a video or movie
- Answers: "How much did I earn and spend?"

Structure:
```
Income - Expenses = Net Income

INCOME
- Salary: $6,000
- Side gig: $500
Total Income: $6,500

EXPENSES
- Housing: $1,800
- Food: $600
- Transportation: $400
- Other: $1,200
Total Expenses: $4,000

NET INCOME: $2,500
```

**How They Connect:**
- Net income from income statement increases equity on balance sheet
- Spending decreases cash (balance sheet) and appears as expense (income statement)
- Balance sheet equity changes = income statement net income""" + STANDARD_DISCLAIMER,
        "category": "bookkeeping"
    },
    {
        "instruction": "How should I categorize my transactions for tracking?",
        "output": """Good categorization makes tracking meaningful. Here's a recommended structure:

**Income Categories:**
- Salary/Wages
- Self-Employment/Freelance
- Investment Income (dividends, interest)
- Rental Income
- Other Income (gifts, refunds, etc.)

**Essential Expense Categories:**
- **Housing**: Rent/mortgage, property tax, HOA, repairs
- **Utilities**: Electric, gas, water, trash, internet
- **Food**: Groceries (separate from dining out)
- **Transportation**: Car payment, gas, insurance, maintenance, parking
- **Insurance**: Health, life, disability (not car - that's transportation)
- **Healthcare**: Copays, prescriptions, dental, vision
- **Debt Payments**: Minimum payments on loans/cards

**Discretionary Categories:**
- **Dining Out**: Restaurants, coffee shops, takeout
- **Entertainment**: Movies, streaming, concerts, sports
- **Shopping**: Clothing, household items, electronics
- **Personal Care**: Haircuts, gym, cosmetics
- **Subscriptions**: All recurring non-essential services
- **Hobbies**: Specific to your interests

**Savings/Investing:**
- Emergency Fund
- Retirement
- Other Savings Goals
- Investments

**Categorization Tips:**
1. **Be consistent**: Same type of expense, same category every time
2. **Don't over-complicate**: 15-20 categories is usually enough
3. **Split transactions**: $100 at Target might be $60 groceries + $40 household
4. **Review monthly**: Catch miscategorized items
5. **Use automation**: Most apps can learn your patterns

**Business vs Personal:**
If self-employed, keep completely separate:
- Separate accounts
- Separate categories
- Clear documentation""" + STANDARD_DISCLAIMER,
        "category": "bookkeeping"
    },
    {
        "instruction": "What is double-entry bookkeeping and do I need it for personal finances?",
        "output": """Double-entry bookkeeping is the foundation of professional accounting:

**How It Works:**
Every transaction affects at least two accounts:
- One account is debited (left side)
- Another account is credited (right side)
- Debits always equal credits

**Example: Pay $1,000 rent**
```
Debit:  Rent Expense     $1,000  (expense increases)
Credit: Cash/Checking    $1,000  (asset decreases)
```

**Example: Receive $3,000 paycheck**
```
Debit:  Cash/Checking    $3,000  (asset increases)
Credit: Income           $3,000  (income increases)
```

**Do You Need It for Personal Finances?**

**Probably NOT if:**
- You just want to track spending
- You use budgeting apps (Mint, YNAB)
- Your finances are straightforward

**Consider It if:**
- You have rental properties
- You run a small business
- You want precise net worth tracking
- You're preparing for complex tax situations

**Simpler Alternative: Single-Entry**
Just track money in and money out:
```
Date       | Description    | Income | Expense | Balance
01/15      | Paycheck       | $3,000 |         | $5,000
01/16      | Rent           |        | $1,000  | $4,000
01/17      | Groceries      |        | $150    | $3,850
```

Most personal finance needs are met with single-entry tracking in a spreadsheet or app.

**Bottom Line:**
Double-entry is overkill for most personal finances but essential for businesses. Start simple and upgrade if your situation demands it.""" + STANDARD_DISCLAIMER,
        "category": "bookkeeping"
    },
]


# =============================================================================
# SMALL BUSINESS Q&A
# =============================================================================

SMALL_BUSINESS_QA = [
    {
        "instruction": "I'm starting a side business. How should I track income and expenses?",
        "output": """Proper tracking from day one makes taxes easier and protects your business:

**Step 1: Separate Business and Personal**
- Open a dedicated business checking account
- Get a business credit card
- Never mix funds

**Step 2: Choose a Tracking Method**

| Method | Best For | Examples |
|--------|----------|----------|
| Spreadsheet | Very small/simple | Google Sheets, Excel |
| Accounting software | Growing businesses | Wave (free), QuickBooks |
| Shoebox (don't) | Nobody | Leads to problems |

**Step 3: Set Up Categories**
Income:
- Product/Service sales
- Other income

Expenses:
- Advertising/Marketing
- Bank fees
- Contract labor
- Equipment/Supplies
- Insurance
- Professional services (legal, accounting)
- Software/Subscriptions
- Travel/Meals (50% deductible)
- Home office (if applicable)

**Step 4: Document Everything**
- Save all receipts (photo apps work great)
- Note business purpose on each expense
- Keep records for 7 years minimum

**Step 5: Regular Maintenance**
- Weekly: Categorize transactions
- Monthly: Reconcile accounts
- Quarterly: Review P&L, estimate taxes
- Annually: Prepare for tax filing

**Tax Considerations:**
- Estimated taxes may be required quarterly
- Self-employment tax is ~15.3%
- Track mileage if you drive for business
- Home office deduction has specific rules""" + TAX_DISCLAIMER + STANDARD_DISCLAIMER,
        "category": "small_business"
    },
    {
        "instruction": "What are the most important financial metrics for a small business?",
        "output": """Focus on these key metrics to understand your business health:

**Profitability Metrics:**

1. **Gross Profit Margin**
   - Formula: (Revenue - Cost of Goods) / Revenue
   - Shows: Pricing power and production efficiency
   - Target: Varies by industry (30-50% for many services)

2. **Net Profit Margin**
   - Formula: Net Income / Revenue
   - Shows: Overall profitability after all expenses
   - Target: 10-20% is healthy for most small businesses

3. **Break-Even Point**
   - Formula: Fixed Costs / (Price - Variable Cost per Unit)
   - Shows: How much you need to sell to cover costs

**Cash Flow Metrics:**

4. **Operating Cash Flow**
   - Cash from normal business operations
   - Should be positive most months

5. **Cash Runway**
   - Formula: Cash / Monthly Burn Rate
   - Shows: How long you can operate if revenue stops
   - Target: 3-6 months minimum

**Efficiency Metrics:**

6. **Accounts Receivable Days**
   - Formula: (AR / Revenue) × 365
   - Shows: How fast customers pay you
   - Lower is better

7. **Revenue per Employee**
   - Formula: Total Revenue / Number of Employees
   - Shows: Labor efficiency

**Growth Metrics:**

8. **Revenue Growth Rate**
   - Formula: (Current - Previous) / Previous
   - Shows: Business momentum

9. **Customer Acquisition Cost (CAC)**
   - Formula: Marketing Spend / New Customers
   - Shows: Cost to get each customer

**Health Check Questions:**
- Is revenue growing?
- Is profit margin stable or improving?
- Is cash flow positive?
- Are customers paying on time?
- Can you cover 3+ months expenses?""" + STANDARD_DISCLAIMER,
        "category": "small_business"
    },
]


# =============================================================================
# TAX-ADJACENT EDUCATION Q&A (No specific advice)
# =============================================================================

TAX_EDUCATION_QA = [
    {
        "instruction": "What's the difference between a tax deduction and a tax credit?",
        "output": """Both reduce your taxes, but they work very differently:

**Tax Deduction**
- Reduces your **taxable income**
- Value depends on your tax bracket
- Applied before calculating tax owed

Example (22% bracket):
- $1,000 deduction
- Reduces taxable income by $1,000
- Saves $1,000 × 22% = **$220 in taxes**

**Tax Credit**
- Reduces your **tax bill directly**
- Dollar-for-dollar reduction
- Applied after calculating tax owed

Example:
- $1,000 credit
- Reduces tax bill by $1,000
- Saves exactly **$1,000 in taxes**

**Credits Are More Valuable:**
A $1,000 credit always saves $1,000.
A $1,000 deduction saves $100-$370 depending on bracket.

**Common Deductions:**
- Mortgage interest
- State/local taxes (SALT, capped at $10K)
- Charitable contributions
- Medical expenses (above threshold)
- Student loan interest

**Common Credits:**
- Child Tax Credit
- Earned Income Tax Credit (EITC)
- Education credits (AOTC, LLC)
- Child and Dependent Care Credit
- Energy credits

**Refundable vs Non-Refundable Credits:**
- Non-refundable: Can only reduce tax to $0
- Refundable: Can result in a refund even if no tax owed""" + TAX_DISCLAIMER,
        "category": "tax_education"
    },
    {
        "instruction": "What records should I keep for tax purposes and for how long?",
        "output": """Good recordkeeping protects you if the IRS has questions:

**What to Keep:**

Income Records:
- W-2s (wage statements)
- 1099s (freelance, investment, interest)
- K-1s (partnership/S-corp income)
- Records of cash income

Expense Records:
- Receipts for deductible expenses
- Mileage logs
- Home office measurements and expenses
- Medical expense receipts
- Charitable donation receipts

Financial Records:
- Bank statements
- Investment statements
- Mortgage interest statements (Form 1098)
- Student loan interest (Form 1098-E)

**How Long to Keep:**

| Record Type | Keep For |
|-------------|----------|
| Tax returns | 7 years (or permanently) |
| Supporting documents | 7 years after filing |
| Investment purchase records | Until 7 years after sale |
| Home improvement records | Until 7 years after sale |
| Business records | 7 years minimum |
| Employment records | 7 years after employment ends |

**Why 7 Years?**
- IRS generally has 3 years to audit
- Extended to 6 years for substantial understatement
- No limit for fraud or failure to file
- 7 years provides safety margin

**Organization Tips:**
1. Create annual folders (paper or digital)
2. Keep digital copies of paper receipts
3. Use cloud backup
4. Organize by category within each year
5. Shred old records after retention period""" + TAX_DISCLAIMER,
        "category": "tax_education"
    },
    {
        "instruction": "What is adjusted gross income (AGI) and why does it matter?",
        "output": """AGI is one of the most important numbers on your tax return:

**What Is AGI?**
Adjusted Gross Income = Total Income - "Above the Line" Deductions

**How It's Calculated:**

Start with Gross Income:
- Wages
- Self-employment income
- Investment income
- Retirement distributions
- Rental income
- Other income

Subtract "Above the Line" Deductions:
- Traditional IRA contributions
- Student loan interest (up to $2,500)
- HSA contributions
- Self-employment tax (half)
- Self-employed health insurance
- Educator expenses
- Alimony paid (pre-2019 divorces)

= **Adjusted Gross Income (AGI)**

**Why AGI Matters:**

1. **Determines deduction eligibility:**
   - Many deductions have AGI limits
   - Medical expenses: Only deduct what exceeds 7.5% of AGI
   - Charitable deductions: Limited to % of AGI

2. **Affects tax credits:**
   - Many credits phase out at higher AGIs
   - Child tax credit, education credits, etc.

3. **Affects other financial areas:**
   - Medicare premium surcharges (IRMAA)
   - Student loan repayment plans
   - Affordable Care Act subsidies
   - Roth IRA contribution eligibility

**Modified AGI (MAGI):**
Some calculations add back certain deductions to AGI. MAGI is used for:
- Roth IRA eligibility
- Premium tax credit
- Various phase-outs

*The specific items added back depend on which calculation.*""" + TAX_DISCLAIMER,
        "category": "tax_education"
    },
]


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_accounting_dataset(n_examples: int = 5000) -> List[Dict]:
    """Generate full accounting training dataset"""
    all_templates = (
        BUDGETING_QA +
        CASH_FLOW_QA +
        BOOKKEEPING_QA +
        SMALL_BUSINESS_QA +
        TAX_EDUCATION_QA
    )

    examples = []

    # Generate base examples
    for template in all_templates:
        examples.append(template)

        # Add variations
        if random.random() > 0.3:
            beginner = template.copy()
            beginner["instruction"] = f"Can you explain in simple terms: {template['instruction'].lower()}"
            beginner["category"] = template["category"] + "_beginner"
            examples.append(beginner)

    # Expand with scenarios
    scenarios = [
        "I make $50,000 per year. ",
        "I'm a freelancer with variable income. ",
        "I'm married with two kids. ",
        "I just started my first job. ",
        "I'm self-employed. ",
        "I'm a college student. ",
        "I'm retiring next year. ",
    ]

    while len(examples) < n_examples:
        template = random.choice(all_templates)
        example = template.copy()

        if random.random() > 0.5:
            scenario = random.choice(scenarios)
            example["instruction"] = scenario + template["instruction"]
            example["category"] = template["category"] + "_scenario"

        examples.append(example)

    return examples[:n_examples]


def save_dataset(examples: List[Dict], output_path: str):
    """Save dataset to JSON file"""
    with open(output_path, "w") as f:
        json.dump(examples, f, indent=2)

    print(f"Saved {len(examples)} examples to {output_path}")

    categories = {}
    for ex in examples:
        cat = ex.get("category", "unknown").split("_")[0]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate accounting training data")
    parser.add_argument("--n", type=int, default=5000, help="Number of examples")
    parser.add_argument("--output", type=str,
                        default="backend/training_data/accounting_training_data.json",
                        help="Output file path")
    args = parser.parse_args()

    print(f"Generating {args.n} accounting training examples...")
    examples = generate_accounting_dataset(args.n)
    save_dataset(examples, args.output)

    print("\nDataset includes proper disclaimers and CPA referrals.")
    print("No specific tax calculations or filing instructions.")
