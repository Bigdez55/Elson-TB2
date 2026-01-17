#!/usr/bin/env python3
"""
Enhanced Training Data Generator v2 for Elson Financial AI

Improvements over v1:
1. More balanced category distribution
2. Multi-turn conversation examples
3. Negative examples (what NOT to recommend)
4. Compliance disclaimers in responses
5. Edge cases and unusual scenarios
6. Different client personas

Target: 2000+ high-quality Q&A pairs
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Any

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "app" / "knowledge_base" / "wealth_management" / "data"
OUTPUT_PATH = Path(__file__).parent.parent / "training_data"

# Compliance disclaimer templates
COMPLIANCE_DISCLAIMERS = [
    "\n\n*Note: This information is for educational purposes. Consult a qualified financial professional for personalized advice.*",
    "\n\n*Disclaimer: Individual circumstances vary. Please consult with a CFP\u00ae or qualified advisor before making financial decisions.*",
    "\n\n*Important: Tax laws change frequently. Verify current rules with a CPA or tax professional.*",
    "\n\n*This is general guidance. Your specific situation may require different strategies. Consider consulting a fiduciary advisor.*",
]

def add_disclaimer(response: str, category: str = "") -> str:
    """Add appropriate compliance disclaimer to response."""
    # Higher-risk categories get disclaimers more often
    high_risk = ["estate_planning", "tax_planning", "investment_advice", "retirement_planning"]
    if category in high_risk or random.random() < 0.3:
        return response + random.choice(COMPLIANCE_DISCLAIMERS)
    return response


# =============================================================================
# MULTI-TURN CONVERSATIONS
# =============================================================================

def generate_multi_turn_conversations() -> list[dict]:
    """Generate multi-turn conversation examples."""
    conversations = [
        # Retirement planning follow-up
        {
            "instruction": "I'm 35 and just started saving for retirement. Where should I begin?",
            "input": "",
            "output": """Great that you're starting! At 35, you have 30 years of growth ahead. Here's your starting plan:

**Immediate Actions:**
1. Enroll in your employer's 401(k) - contribute at least enough to get the full match
2. If no 401(k), open a Roth IRA ($7,000/year limit)
3. Aim for 15% of income toward retirement

**Investment Approach:**
- At 35, target 75-80% stocks, 20-25% bonds
- Use target-date 2055 fund for simplicity
- Low-cost index funds (expense ratio under 0.2%)

What's your current income and does your employer offer a 401(k) match?""",
            "category": "multi_turn",
            "turn": 1
        },
        {
            "instruction": "I make $85,000 and my employer matches 4%. I have $0 saved currently.",
            "input": "Previous: User asked about starting retirement savings at 35. I recommended 401(k) with employer match.",
            "output": """Perfect, let's build your specific plan:

**Your Numbers:**
- Income: $85,000/year
- Employer match: 4% = $3,400 FREE money annually
- Your 4% contribution: $3,400/year ($283/month)

**Phase 1 (Months 1-3): Get the Match**
- Contribute 4% to 401(k) immediately
- This alone = $6,800/year toward retirement

**Phase 2 (Months 4-12): Add Roth IRA**
- Open Roth IRA at Fidelity, Vanguard, or Schwab
- Contribute $500/month ($6,000/year)
- Invest in target-date 2055 fund

**Phase 3 (Year 2+): Increase to 15%**
- Bump 401(k) to 11% ($9,350/year)
- Total: 15% = $12,750/year + $3,400 match = $16,150

**30-Year Projection (7% returns):**
- If you save $16,150/year: **~$1.6 million by 65**

Should I explain which investments to choose inside these accounts?""",
            "category": "multi_turn",
            "turn": 2
        },
        {
            "instruction": "Yes, what should I invest in? And what about my company stock option?",
            "input": "Previous: User is 35, makes $85k, starting retirement savings. We set up 401(k) + Roth IRA plan totaling $16,150/year.",
            "output": """**Investment Selection:**

**Inside Your 401(k):**
Best option: **Target-Date 2055 Fund** (if available)
- Automatically adjusts as you age
- Diversified across stocks and bonds
- "Set it and forget it"

If no target-date fund, build this:
- 60% US Total Stock Market Index
- 20% International Stock Index
- 20% US Bond Index

**Inside Your Roth IRA:**
- VTI (Vanguard Total Stock Market) - 80%
- VXUS (International Stocks) - 20%

**About Company Stock:**
\u26a0\ufe0f **Important Warning:**
- Limit company stock to **10% MAX** of portfolio
- Your salary AND investments shouldn't both depend on one company
- Think Enron - employees lost jobs AND retirement savings

**If you have stock options:**
1. Exercise when vested and immediately diversify
2. Don't hold more than 10% in any single stock
3. Set automatic sell triggers

**Rebalancing:**
- Check allocation once per year
- Rebalance if off by more than 5%

Any questions about the specific fund options in your 401(k)?""",
            "category": "multi_turn",
            "turn": 3
        },

        # Estate planning follow-up
        {
            "instruction": "My parents are in their 70s and haven't done any estate planning. How do I bring this up?",
            "input": "",
            "output": """This is a sensitive but important conversation. Here's how to approach it:

**Framing the Conversation:**
- Don't make it about their death - make it about protecting the family
- Share your own planning as an opener: "I just updated my will and it made me think..."
- Focus on practical concerns: "What would happen if you needed care?"

**Good Conversation Starters:**
1. "I want to make sure I can help if something happens. Do you have documents I should know about?"
2. "My friend's family had a terrible time with probate. Have you thought about that?"
3. "Where do you keep important documents? I'd like to know just in case."

**What to Ask About:**
- Do they have a will?
- Healthcare power of attorney?
- Financial power of attorney?
- Where are important documents kept?
- Who is the executor?

Would you like specific guidance on what documents they should have at their age and situation?""",
            "category": "multi_turn",
            "turn": 1
        },
        {
            "instruction": "Yes, they have a house worth about $400k, some savings, and dad has a pension. What do they need?",
            "input": "Previous: User asking how to discuss estate planning with parents in their 70s.",
            "output": """**Essential Documents for Parents (70s, ~$400k home + savings + pension):**

**Must-Have (Priority Order):**

1. **Healthcare Power of Attorney** \u2605 URGENT
   - Names someone to make medical decisions
   - Critical if either becomes incapacitated
   - Each parent needs their own

2. **HIPAA Authorization**
   - Allows family to access medical information
   - Without this, doctors can't share info

3. **Living Will / Advance Directive**
   - End-of-life care wishes
   - Reduces family burden during crisis

4. **Durable Financial Power of Attorney**
   - Someone to pay bills, manage finances if incapacitated
   - "Durable" means it survives incapacity

5. **Will**
   - Names executor
   - Specifies who gets what
   - Names guardians for any dependents

**For the $400k House:**
Consider a **Revocable Living Trust**:
- Avoids probate (saves $10-20k+ and 6-18 months)
- Private (wills are public record)
- Manages assets if they're incapacitated
- Cost: $1,500-3,000 one-time

**Dad's Pension:**
- Ensure beneficiary designation is correct
- Check if it has survivor benefits for mom

**Action Plan:**
1. This week: Have the conversation
2. This month: Schedule estate attorney appointment ($500-1,500 for basic package)
3. Within 90 days: All documents signed and stored safely

Should I explain what to look for in an estate attorney?""",
            "category": "multi_turn",
            "turn": 2
        },
    ]

    return conversations


# =============================================================================
# NEGATIVE EXAMPLES (What NOT to do)
# =============================================================================

def generate_negative_examples() -> list[dict]:
    """Generate examples of bad financial advice to avoid."""
    negative_examples = [
        {
            "instruction": "My friend said I should put my entire emergency fund in crypto because it grows faster. Is this good advice?",
            "input": "",
            "output": """**No, this is bad advice. Here's why:**

\u274c **Why NOT to put emergency fund in crypto:**

1. **Volatility Risk**
   - Crypto can drop 50-80% in weeks
   - Your $10,000 emergency fund could become $2,000
   - When you need it, it might be at its lowest

2. **Liquidity Issues**
   - Takes time to convert to cash
   - Exchange outages during market stress
   - Weekend emergencies = no bank transfers

3. **Emergency Fund Purpose**
   - Must be stable and accessible
   - You can't predict when you'll need it
   - Emergencies don't wait for market recovery

**What emergency funds ARE for:**
- High-yield savings account (4-5% currently)
- Money market account
- Accessible within 1-2 days
- FDIC insured

**Crypto is for:**
- Money you can afford to lose
- Long-term speculation (5+ years)
- AFTER emergency fund is full
- Max 5-10% of investment portfolio

**Red Flag:** Anyone advising you to put essential savings in highly volatile assets doesn't understand risk management.""",
            "category": "negative_example"
        },
        {
            "instruction": "A financial advisor wants me to put all my retirement savings into a fixed annuity at age 30. He says it's safe and guaranteed. Should I do it?",
            "input": "",
            "output": """**No, this is likely bad advice for a 30-year-old. Here's why:**

\u274c **Problems with this recommendation:**

1. **Opportunity Cost**
   - At 30, you have 35+ years until retirement
   - Stocks historically return 7-10%/year
   - Fixed annuities return 3-5%
   - Difference over 35 years is MASSIVE

2. **Liquidity Trap**
   - Surrender charges (often 7-10 years)
   - Penalties to access your money
   - Locked up during your prime earning years

3. **Commission Red Flag** \u26a0\ufe0f
   - Annuities pay HIGH commissions to advisors (4-8%)
   - This advisor may be recommending what pays THEM best
   - Ask: "How are you compensated for this recommendation?"

4. **Inflation Risk**
   - Fixed 4% doesn't keep up with inflation long-term
   - $100,000 today = $50,000 purchasing power in 35 years

**When annuities MIGHT make sense:**
- Age 55+ approaching retirement
- Already have diversified portfolio
- Want guaranteed income stream
- Understand all fees and terms

**Better approach at 30:**
- 401(k) with employer match
- Roth IRA
- Low-cost index funds
- Time in market > timing the market

**Questions to ask this advisor:**
1. Are you a fiduciary?
2. How are you compensated?
3. What alternatives did you consider?
4. Can I see this recommendation in writing?""",
            "category": "negative_example"
        },
        {
            "instruction": "I inherited $50,000. My uncle says I should use it to day-trade stocks because his friend made a fortune doing it. Good idea?",
            "input": "",
            "output": """**No, day trading your inheritance is a bad idea. Here's the reality:**

\u274c **Day Trading Statistics:**
- 70-90% of day traders LOSE money
- Average day trader underperforms a simple index fund
- After fees and taxes, returns are even worse
- "Survivorship bias" - you only hear success stories

\u274c **Why your uncle's friend's story is misleading:**
- For every success story, there are 9 failures you don't hear about
- Luck often mistaken for skill short-term
- Most "winners" eventually give gains back
- Transaction costs eat into returns

**What to actually do with $50,000 inheritance:**

**Step 1: Pause (Don't invest immediately)**
- Put in high-yield savings for 3-6 months
- Avoid emotional decisions while grieving
- Take time to plan properly

**Step 2: Prioritize**
1. Pay off high-interest debt (credit cards)
2. Build 6-month emergency fund
3. Max out Roth IRA ($7,000)
4. Invest remainder in index funds

**Step 3: Simple Investment**
- Vanguard Total Stock Market (VTI)
- Target-date fund for hands-off approach
- Expected long-term return: ~7%/year
- In 30 years at 7%: $50,000 \u2192 $380,000

**If you want "action":**
- Set aside $5,000 max (10%) for individual stocks
- Consider it "tuition" you might lose
- Keep 90% in boring index funds

**Remember:** Wealth is built slowly through consistent investing, not gambling.""",
            "category": "negative_example"
        },
        {
            "instruction": "I can't afford to save for retirement right now, so I'll just start when I'm 50. I'll have 15 years which is plenty of time, right?",
            "input": "",
            "output": """**This is a costly mistake. Let me show you the math:**

\u274c **The Cost of Waiting:**

**Scenario A: Start at age 25**
- Save $500/month for 40 years
- Total contributed: $240,000
- Value at 65 (7% return): **$1,200,000+**

**Scenario B: Start at age 50**
- Save $500/month for 15 years
- Total contributed: $90,000
- Value at 65 (7% return): **~$158,000**

**The Difference:** Starting at 25 gives you 7x more money while contributing only 2.7x more!

\u274c **Why "I can't afford it" is often untrue:**

You probably CAN afford something:
- $50/month = $600/year
- Skip 2 coffee shop visits per week = $500/year
- Employer match = FREE money you're leaving on table

**Even small amounts matter:**
- $100/month from age 25 = $264,000 at 65
- $100/month from age 50 = $31,000 at 65

**What to do NOW (even with tight budget):**

1. **Get the employer match** - It's 100% return!
2. **Start with 1%** - You won't notice it
3. **Increase 1% with each raise**
4. **Automate it** - Out of sight, out of mind

**The real problem with waiting until 50:**
- Life rarely gets "less expensive"
- Kids, mortgage, health issues
- You'll be trying to catch up AND save for kids' college
- Much more stressful than starting small now

**Compound interest is the most powerful force in wealth building. Don't waste your 20s and 30s.**""",
            "category": "negative_example"
        },
        {
            "instruction": "My brother-in-law has a 'can't miss' investment opportunity that guarantees 20% annual returns. Should I invest my savings?",
            "input": "",
            "output": """**STOP. This has major red flags for fraud.**

\u26a0\ufe0f **Warning Signs of Investment Fraud:**

1. **"Guaranteed" high returns**
   - Nothing in investing is guaranteed
   - S&P 500 averages ~10%/year with significant volatility
   - 20% "guaranteed" is mathematically suspicious

2. **Family/friend referral**
   - Affinity fraud (Ponzi schemes) target trust networks
   - Bernie Madoff used this exact approach
   - Good people unknowingly recruit victims

3. **Pressure to act quickly**
   - "Limited time opportunity"
   - "Get in before it's too late"
   - Legitimate investments don't require urgency

4. **Complex or vague explanation**
   - Can't clearly explain how returns are generated
   - "Proprietary strategy" without details
   - Secretive about the actual investments

**Legitimate investments:**
- Are registered with SEC/FINRA
- Have clear prospectuses
- Don't "guarantee" high returns
- Allow you to take your time deciding

**What to do:**
1. **Ask for written documentation**
2. **Check FINRA BrokerCheck** (brokercheck.finra.org)
3. **Search SEC EDGAR** for registration
4. **Google "[company name] + scam/fraud/complaint"**
5. **If hesitant to do due diligence, walk away**

**How to respond to your brother-in-law:**
"Thanks for thinking of me, but I have a financial advisor I work with. If you can send me the prospectus and SEC registration, I'll have them review it."

**Remember:** If it sounds too good to be true, it almost always is.""",
            "category": "negative_example"
        },
        {
            "instruction": "I'm going to take money out of my 401(k) to pay off my car loan at 5% interest. It makes sense to eliminate debt, right?",
            "input": "",
            "output": """**No, this is usually a bad idea. Here's why the math doesn't work:**

\u274c **Hidden Costs of 401(k) Withdrawal:**

**1. Immediate Tax Hit**
- Withdrawal taxed as ordinary income
- If you're in 22% bracket: lose $2,200 per $10,000

**2. Early Withdrawal Penalty**
- Additional 10% penalty if under 59\u00bd
- That's $1,000 per $10,000

**3. Total Immediate Loss: 32%+**
- $10,000 withdrawal = $6,800 in your pocket
- Plus state taxes (another 5-10% in most states)

**4. Lost Growth (The Hidden Cost)**
- That $10,000 would grow to $76,000 in 30 years (7% return)
- You're not just losing $10,000, you're losing $76,000

**The Real Math:**

Paying off 5% car loan with 401(k):
- Withdrawal: $10,000
- Taxes + Penalty: ~$3,500
- Interest saved: ~$1,500 total
- **Net Loss: $2,000+ immediately**
- **Plus $65,000+ in lost future growth**

\u2705 **Better Alternatives:**

1. **Refinance the car loan** - Rates may be lower now
2. **Pay extra monthly** - Even $50/month helps
3. **Balance transfer to 0% card** - If good credit
4. **Side income** - Temporarily increase earnings
5. **Reduce expenses** - Free up cash for extra payments

**When 401(k) withdrawal MIGHT make sense:**
- Avoiding foreclosure/eviction (true emergency)
- Medical emergency with no other options
- NEVER for a 5% car loan

**Rule of thumb:** Only raid retirement for true emergencies, not for optimizing low-interest debt.""",
            "category": "negative_example"
        },
    ]

    return negative_examples


# =============================================================================
# EDGE CASES AND UNUSUAL SCENARIOS
# =============================================================================

def generate_edge_cases() -> list[dict]:
    """Generate edge cases and unusual financial scenarios."""
    edge_cases = [
        {
            "instruction": "I'm 62 and just got diagnosed with a terminal illness. How should I adjust my financial plan?",
            "input": "",
            "output": """I'm sorry to hear about your diagnosis. Here's practical financial guidance for this situation:

**Immediate Priorities:**

**1. Review Life Insurance**
- Check all policies (personal, employer, group)
- Understand payout terms
- Consider accelerated death benefit option (up to 50-75% paid early)

**2. Social Security Decision**
- With limited life expectancy, claiming early may make sense
- File as soon as eligible
- Don't leave money on the table by waiting

**3. Healthcare and Long-Term Care**
- Review Medicare coverage
- Understand hospice benefits (covered by Medicare)
- Consider Medicaid planning if assets limited

**4. Estate Planning Urgency**
- Update or create will immediately
- Execute healthcare directives
- Ensure power of attorney in place
- Review all beneficiary designations

**5. Roth Conversions**
- If in lower tax bracket due to reduced income
- Heirs inherit Roth tax-free
- No RMDs means more goes to family

**6. Gifting Strategy**
- Annual exclusion: $18,000/person/year
- Consider larger gifts if estate over $13.6M
- Direct payment of medical/education expenses unlimited

**7. Retirement Account Strategy**
- 401(k)/IRA: Named beneficiaries avoid probate
- Consider withdrawals while in lower bracket
- Non-spouse beneficiaries have 10-year withdrawal rule

**Professional Team to Assemble:**
- Estate attorney (update documents)
- CPA (tax optimization)
- Insurance specialist (review all coverage)
- Palliative care coordinator

**For Your Family:**
- Organize all financial documents
- Create list of accounts and contacts
- Share passwords/access securely
- Consider letter of instruction

*I encourage you to also consider consulting with a counselor or support group. Financial planning is important, but so is emotional well-being.*""",
            "category": "edge_case"
        },
        {
            "instruction": "My spouse and I are getting divorced after 25 years. How do I protect my retirement?",
            "input": "",
            "output": """Divorce after a long marriage requires careful financial planning. Here's what to know:

**Understanding Division of Retirement Assets:**

**1. Retirement Accounts Are Marital Property**
- 401(k), IRA, pensions accumulated during marriage are typically split
- Even if only one spouse's name is on account
- Division is usually 50/50 but negotiable

**2. QDRO (Qualified Domestic Relations Order)**
- Required to divide 401(k), 403(b), pension
- Must be approved by plan administrator
- Allows transfer without early withdrawal penalty
- **Critical:** Get attorney experienced with QDROs

**3. IRA Division**
- Easier than 401(k) - done via divorce decree
- Transferred portion becomes recipient's IRA
- No taxes if transferred properly (not withdrawn)

**Strategy for Negotiations:**

**Know What You're Dividing:**
- Get statements for ALL retirement accounts
- Include: 401(k), IRA, pension, deferred comp, stock options
- Value pensions properly (present value calculation)

**Consider the Trade-offs:**
- Retirement assets are pre-tax (worth less than face value)
- Home equity is after-tax
- $100k in 401(k) \u2260 $100k in home equity
- Account for different tax treatments

**Protect Yourself:**

**1. Don't agree to anything without legal advice**
- Divorce attorneys who understand retirement assets
- Possibly a Certified Divorce Financial Analyst (CDFA\u00ae)

**2. Document everything**
- Account balances at separation date
- Any premarital contributions (may be yours)
- Inherited retirement funds (may be protected)

**3. Update Beneficiaries Immediately**
- AFTER divorce is final
- Don't leave ex-spouse on accounts
- QDROs override beneficiary designations until removed

**Social Security Consideration:**
- Married 10+ years = entitled to benefits based on ex's record
- Must be unmarried to claim
- Doesn't reduce your ex's benefit
- Can be better than your own benefit

**After Divorce:**
- Rebuild retirement savings aggressively
- Update estate plan completely
- Adjust asset allocation for new situation
- Consider catch-up contributions (age 50+)

*Get a financial planner post-divorce to create a new retirement projection with your revised assets.*""",
            "category": "edge_case"
        },
        {
            "instruction": "I'm a gig worker with irregular income. How do I budget and save for retirement?",
            "input": "",
            "output": """Gig economy workers face unique challenges but can absolutely build wealth. Here's your framework:

**Budgeting with Irregular Income:**

**Step 1: Calculate Your Baseline**
- Average last 12 months of income
- Identify your lowest-earning months
- Budget based on 80% of average (conservative)

**Step 2: "Pay Yourself a Salary"**
- When good months happen, don't spend it all
- Transfer excess to savings buffer
- Draw consistent "salary" from buffer
- Aim for 3+ months income in buffer

**Step 3: Priority-Based Spending**
1. Essentials (rent, food, utilities, insurance)
2. Taxes (set aside 25-30% immediately)
3. Retirement savings
4. Discretionary

**Tax Strategy (Critical for Gig Workers):**

**Quarterly Estimated Taxes:**
- Due: Apr 15, Jun 15, Sep 15, Jan 15
- Underpayment penalties if you miss them
- Set aside 25-30% of every payment received
- Use separate savings account labeled "Taxes"

**Deductions to Track:**
- Home office (dedicated space)
- Equipment and supplies
- Vehicle/mileage (keep log!)
- Health insurance premiums
- Professional development
- Phone/internet (business portion)

**Retirement Options for Self-Employed:**

**1. Solo 401(k)** \u2b50 Best for most
- Contribute as employee AND employer
- 2024 limit: Up to $69,000 total
- Can contribute when you have income
- Roth option available

**2. SEP-IRA**
- Simpler than Solo 401(k)
- Up to 25% of net self-employment income
- Max $69,000 (2024)
- Easy to set up

**3. SIMPLE IRA**
- Good if you have employees
- Lower limits ($16,000 + $3,500 catch-up)

**4. Traditional/Roth IRA**
- $7,000 limit ($8,000 if 50+)
- In addition to above options

**Practical System:**

**When you receive payment:**
1. 30% \u2192 Tax savings account
2. 15% \u2192 Retirement account
3. 10% \u2192 Income buffer
4. 45% \u2192 Operating/spending

**Emergency Fund Priority:**
- Gig workers need MORE emergency fund
- Target 6-12 months expenses (vs 3-6 for employees)
- Keep in high-yield savings

**Health Insurance:**
- Healthcare.gov marketplace
- May qualify for subsidies based on income
- HSA if you have qualifying high-deductible plan

*Consider working with an accountant familiar with self-employment - the tax savings often pay for their fees.*""",
            "category": "edge_case"
        },
        {
            "instruction": "I'm 25 and just won $500,000 in the lottery. What should I do?",
            "input": "",
            "output": """Congratulations! This is life-changing money IF you handle it right. 70% of lottery winners go broke within a few years. Don't be one of them.

**Immediate Steps (First 30 Days):**

**1. Tell Almost No One**
- Seriously - this is the #1 mistake
- Money changes relationships
- You'll get requests from everyone
- Keep circle small: spouse, financial advisor, attorney

**2. Don't Quit Your Job Yet**
- Take time to plan
- Keep your routine
- Make no major decisions for 6 months

**3. Secure the Money**
- Deposit in insured accounts (spread across banks if needed)
- FDIC limit is $250k per bank
- Don't invest anything yet

**4. Assemble Your Team**
- Fee-only financial planner (NOT commission-based)
- CPA (taxes will be complex)
- Estate attorney
- Interview multiple candidates

**Understanding the Money:**

**After Taxes:**
- Federal tax: ~37% ($185,000)
- State tax: varies by state
- **Net:** Approximately $280,000-$350,000

**This is still significant but not "never work again" money at 25.**

**Smart Allocation:**

**1. Emergency Fund: $30,000**
- 12 months expenses
- High-yield savings

**2. Pay Off ALL Debt**
- Student loans, car, credit cards
- Probably $20,000-$100,000 for most 25-year-olds

**3. Max Out Retirement (This Year + Next Few):**
- Roth IRA: $7,000/year
- 401(k): $23,000/year
- Invest in index funds

**4. Down Payment on Modest Home: $60,000-$80,000**
- Don't buy a mansion
- Buy what you'd afford on your salary
- Stability, not status

**5. Invest the Rest: $100,000-$150,000**
- Taxable brokerage account
- 80% total stock market index
- 20% international index
- Don't touch for 10+ years

**What NOT to Do:**
\u274c Buy luxury car
\u274c Quit job immediately
\u274c Lend money to family/friends
\u274c Start a business (yet)
\u274c Tell everyone

**Long-Term Perspective:**
$150,000 invested at 25, growing at 7%/year = **$1.5 million at 65**

This money can secure your future if you're boring with it now.""",
            "category": "edge_case"
        },
    ]

    return edge_cases


# =============================================================================
# CLIENT PERSONA-BASED Q&A
# =============================================================================

def generate_persona_qa() -> list[dict]:
    """Generate Q&A for different client personas."""
    personas = [
        # Young Professional
        {
            "instruction": "I'm a 28-year-old software engineer making $150,000. I have $50,000 in savings and no debt. What's my optimal wealth building strategy?",
            "input": "",
            "output": """Excellent position! High income, no debt, and time on your side. Here's your optimal strategy:

**Your Advantages:**
- High income with growth potential
- 37 years until traditional retirement
- Clean slate (no debt)

**Wealth Building Blueprint:**

**Phase 1: Maximize Tax-Advantaged Accounts**

1. **401(k):** $23,000/year
   - Get any employer match first
   - Mega-backdoor Roth if available ($69,000 total limit)

2. **Roth IRA:** $7,000/year (backdoor if over income limit)

3. **HSA:** $4,150/year if you have HDHP
   - Triple tax advantage
   - Use as stealth retirement account

**Phase 2: Taxable Investing**
- After maxing above, invest additional in brokerage
- Index funds (VTI, VXUS)
- Tax-efficient placement

**Phase 3: Build Optionality**
- Save for house down payment (if homeownership goal)
- Keep 6-month emergency fund separate

**Your Numbers:**

**Savings Rate Target: 50%+** ($75,000/year)
- $23,000 \u2192 401(k)
- $7,000 \u2192 Roth IRA
- $4,150 \u2192 HSA
- $40,850 \u2192 Taxable brokerage

**At 7% returns:**
- $75k/year for 37 years = **$11+ million by 65**
- FIRE possible in 10-15 years if you want

**Current $50k:**
- $25k \u2192 Emergency fund (keep in HYSA)
- $25k \u2192 Invest immediately (lump sum > DCA statistically)

**Investment Allocation at 28:**
- 90% stocks (70% US, 20% International)
- 10% bonds
- Or just use target-date 2060 fund

**Tax Optimization:**
- Max 401(k) traditional (reduce taxable income)
- Roth IRA for tax diversification
- Tax-loss harvest in taxable account

*You're in a position to potentially reach financial independence by 40 if you maintain this trajectory.*""",
            "category": "persona"
        },
        # Single Parent
        {
            "instruction": "I'm a single mom with two kids (ages 8 and 12), making $65,000. I have $10,000 saved and $15,000 in credit card debt. Where do I start?",
            "input": "",
            "output": """You're doing more than you think by even asking this question. Let's build a realistic plan:

**Your Reality:**
- Income: $65,000 (~$4,300/month take-home)
- Responsibilities: Two children approaching expensive years
- Challenges: Credit card debt + limited savings

**Priority Order:**

**Phase 1: Stabilize (Months 1-6)**

1. **Minimum Emergency Fund: $2,000**
   - Keep $2,000 untouched in savings
   - Prevents new debt from emergencies
   - Don't touch the rest of your $10k yet

2. **Attack Credit Card Debt**
   - Use remaining $8,000 toward $15,000 debt
   - New balance: $7,000
   - Pay $500/month ($300 min + $200 extra)
   - Debt-free in 14 months

3. **Get the 401(k) Match**
   - If employer matches, contribute enough to get it
   - Even 3% = $1,950 + $975 match = $2,925/year

**Phase 2: Build Security (Months 7-18)**

1. **Grow Emergency Fund**
   - Target: $10,000 (3 months expenses)
   - Redirect debt payment ($500/month) to savings

2. **Increase Retirement**
   - Bump to 10% ($6,500/year)

**Phase 3: Kids' Future (Year 2+)**

1. **529 Plans**
   - Start with $50-100/month per child
   - State tax deduction available
   - Something is better than nothing

2. **Consider Roth IRA**
   - At your income, Roth makes sense
   - Contributions accessible for emergencies
   - Can use for kids' education if needed

**Practical Tips:**

**Increase Income:**
- Annual raise requests (document achievements)
- Side income when kids are with other parent
- Consider certifications for career advancement

**Reduce Expenses:**
- Review all subscriptions
- Meal planning saves $200-400/month
- Use library, parks, free activities with kids

**Tax Optimization:**
- Claim Earned Income Tax Credit
- Child Tax Credit ($2,000 per child)
- Dependent care FSA if applicable
- Head of Household filing status

**Your 10-Year Projection (Conservative):**
- Emergency fund: $15,000
- Retirement: $80,000+
- 529 plans: $20,000+ (with modest growth)
- Debt: $0

**You've got this.** The hardest part is starting, and you're doing that now.

*Look into your state's TANF and childcare assistance programs - you may qualify for additional support.*""",
            "category": "persona"
        },
        # Near Retiree
        {
            "instruction": "I'm 58, want to retire at 62, have $800,000 saved, and spend about $60,000/year. Am I on track?",
            "input": "",
            "output": """Let's run the numbers and see where you stand:

**Your Situation:**
- Current age: 58
- Target retirement: 62 (4 years)
- Current savings: $800,000
- Annual spending: $60,000

**Quick Retirement Math:**

**4% Rule Check:**
- $60,000 \u00f7 0.04 = $1,500,000 needed
- You have $800,000
- **Gap: $700,000**

**Projection to Age 62:**
If you save $30,000/year + 7% growth:
- Current: $800,000
- Year 1: $886,000
- Year 2: $978,000
- Year 3: $1,078,000
- Year 4: $1,187,000

**At 62: ~$1.2 million** (still short of $1.5M target)

**Honest Assessment: You're close but need adjustments.**

**Options to Close the Gap:**

**Option 1: Work 2-3 More Years (Most Effective)**
- Each year adds: $30k savings + $84k growth
- At 65: ~$1.5 million \u2705
- Also delays Social Security (8%/year increase to 70)

**Option 2: Reduce Spending**
- $50,000/year needs only $1.25 million
- At 62 you'd have ~$1.2M (close!)
- Can you cut $10k/year? ($833/month)

**Option 3: Part-Time Work in Early Retirement**
- $20,000/year part-time reduces withdrawal need
- Only need $40k from portfolio
- $40k \u00f7 0.04 = $1 million (achievable)

**Option 4: Combination**
- Work to 63 (adds ~$120k)
- Reduce spending to $55k
- Part-time for first 3 years ($15k/year)
- This works!

**Social Security Impact:**

| Claim Age | Monthly Benefit (est.) | Annual |
|-----------|------------------------|--------|
| 62 | $1,800 | $21,600 |
| 67 (FRA) | $2,600 | $31,200 |
| 70 | $3,224 | $38,688 |

**Strategy:** Delay Social Security to 67-70 if possible. Live on savings first.

**Healthcare:**
- Medicare starts at 65
- Ages 62-65: ACA marketplace
- Budget $15,000-20,000/year for healthcare until Medicare

**Recommended Path:**
1. Work to 63-64 (significant impact)
2. Delay Social Security to 67 minimum
3. Consider part-time work 63-67
4. Review spending for potential reductions

**You're not far off, but a few adjustments make this work comfortably.**

*Get a detailed retirement projection from a CFP\u00ae to model different scenarios with your specific numbers.*""",
            "category": "persona"
        },
    ]

    return personas


# =============================================================================
# EXPANDED CORE CATEGORIES
# =============================================================================

def generate_expanded_retirement_qa() -> list[dict]:
    """Generate additional retirement Q&A to balance categories."""
    qa_pairs = []

    # Additional retirement questions
    additional = [
        {
            "q": "What is the difference between traditional and Roth retirement accounts?",
            "a": """**Traditional vs Roth: Complete Comparison**

**Traditional Accounts (401(k), IRA):**
- **Contributions:** Pre-tax (reduces taxable income now)
- **Growth:** Tax-deferred
- **Withdrawals:** Taxed as ordinary income
- **RMDs:** Required starting at 73
- **Best if:** Higher tax bracket now than in retirement

**Roth Accounts (Roth 401(k), Roth IRA):**
- **Contributions:** After-tax (no deduction now)
- **Growth:** Tax-free
- **Withdrawals:** Tax-FREE (if qualified)
- **RMDs:** None for Roth IRA (Roth 401k has RMDs until rolled to Roth IRA)
- **Best if:** Lower tax bracket now or want tax diversification

**Decision Framework:**

**Choose Traditional If:**
- Current income > $100,000
- Expect lower income in retirement
- Want to reduce this year's taxes
- State has high income tax (may move to low-tax state in retirement)

**Choose Roth If:**
- Early in career (lower bracket)
- Expect higher taxes in future
- Want tax-free withdrawals in retirement
- Already have large traditional balances

**The Real Answer:** Use BOTH for tax diversification
- Max employer match in traditional 401(k)
- Contribute to Roth IRA
- Mix gives flexibility in retirement

**Contribution Limits (2024):**
| Account | Under 50 | 50 and over |
|---------|----------|-------------|
| 401(k) | $23,000 | $30,500 |
| IRA | $7,000 | $8,000 |"""
        },
        {
            "q": "How do I catch up on retirement savings in my 40s?",
            "a": """**Retirement Catch-Up Strategy for Your 40s**

**The Good News:**
- 20-25 years until retirement
- Peak earning years ahead
- Catch-up contributions at 50

**The Math:**
If you're 45 with $50,000 saved, saving $20,000/year at 7%:
- Age 55: $331,000
- Age 65: $728,000
Add catch-up contributions at 50: **$800,000+**

**Aggressive Catch-Up Plan:**

**1. Max Everything**
- 401(k): $23,000 ($30,500 at 50+)
- Roth IRA: $7,000 ($8,000 at 50+)
- HSA: $4,150 ($5,150 at 55+)
- Total: $34,150/year ($43,650 with catch-up)

**2. Increase Savings Rate**
- Target 25-30% of income
- Every raise goes to retirement
- "Lifestyle creep" is your enemy

**3. Optimize Investments**
- Still have 20+ years - don't be too conservative
- 70-80% stocks appropriate for most
- Low-cost index funds

**4. Reduce Expenses**
- House payment should be gone by retirement
- Consider downsizing
- Avoid new car loans

**5. Increase Income**
- Career advancement
- Side business/consulting
- Rental property

**Critical Mistakes to Avoid:**
\u274c Prioritizing kids' college over retirement (they can borrow, you can't)
\u274c Being too conservative with investments
\u274c Taking 401(k) loans
\u274c Ignoring employer match

**Timeline:**
- Age 45-50: Aggressive saving, career maximization
- Age 50-55: Catch-up contributions, debt elimination
- Age 55-60: Final push, transition planning
- Age 60-65: Glide path to retirement"""
        },
    ]

    for item in additional:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": add_disclaimer(item["a"], "retirement_planning"),
            "category": "retirement_planning"
        })

    return qa_pairs


def generate_expanded_estate_qa() -> list[dict]:
    """Generate additional estate planning Q&A."""
    qa_pairs = []

    additional = [
        {
            "q": "What happens if I die without a will (intestate)?",
            "a": """**Dying Without a Will: Intestate Succession**

**What Happens:**
State law determines who gets your assets. You have NO control.

**Typical Distribution (varies by state):**

**If Married with Children:**
- Spouse gets 1/3 to 1/2
- Children split the rest
- Even minor children may inherit directly

**If Married, No Children:**
- Spouse may get 1/2 to all
- Parents or siblings may get portion

**If Single with Children:**
- Children inherit equally

**If Single, No Children:**
- Parents \u2192 siblings \u2192 extended family

**Problems with Intestacy:**

1. **No Say in Distribution**
- Ex-spouse could end up with assets
- Estranged family members may inherit
- Charities get nothing

2. **Minor Children Issues**
- May inherit directly at 18
- No trust protection
- Court appoints guardian (not your choice)

3. **Probate Required**
- Public process
- Expensive (3-7% of estate)
- Time-consuming (6-18 months)

4. **Business Complications**
- No succession plan
- Partners may be stuck with heirs
- Business may need to be sold

5. **Blended Family Chaos**
- Stepchildren typically get nothing
- Conflict between spouse and children from prior marriage

**What a Basic Will Does:**
- You choose beneficiaries
- You name guardian for minor children
- You pick executor
- You can create trusts for protection

**Cost of Basic Will:** $300-1,000
**Cost of Intestate Problems:** Potentially tens of thousands + family conflict

**Action:** Get a will. Today. No excuses."""
        },
        {
            "q": "Should I put my house in my children's names to avoid estate taxes?",
            "a": """**Don't Do This! Here's Why:**

\u274c **Major Problems with Gifting Your Home to Children:**

**1. Lost Step-Up in Basis**
This is the biggest mistake.

**Example:**
- You bought house for $100,000
- Now worth $500,000
- Gain: $400,000

**If you gift it:**
- Kids inherit YOUR $100,000 basis
- They sell for $500,000
- Capital gains tax on $400,000 = **$80,000+ in taxes**

**If they inherit it:**
- Basis "steps up" to $500,000
- They sell for $500,000
- Capital gains tax: **$0**

**2. Gift Tax Implications**
- $500,000 home exceeds annual exclusion ($18,000)
- Uses lifetime exemption
- Requires gift tax return filing

**3. Loss of Control**
- It's legally theirs now
- They could sell it
- Their creditors could take it
- Their divorce could affect it

**4. Medicaid Issues**
- 5-year lookback for Medicaid eligibility
- Gift may be penalized
- You could need nursing home care before 5 years

**5. Property Tax Loss**
- May lose homestead exemption
- Property taxes could increase significantly

**6. Capital Gains Exclusion Lost**
- Primary residence exclusion ($250k/$500k) doesn't apply to children

**Better Alternatives:**

**1. Revocable Living Trust**
- Avoids probate
- You keep control
- Kids inherit with step-up in basis

**2. Transfer on Death Deed (TOD)**
- Available in many states
- House passes outside probate
- Step-up in basis preserved
- You retain full control

**3. Life Estate Deed**
- More complex, but may work for Medicaid planning
- Consult elder law attorney

**Bottom Line:**
For most families, gifting your home to children is a $50,000-$100,000+ mistake. Consult an estate attorney before making ANY property transfers."""
        },
    ]

    for item in additional:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": add_disclaimer(item["a"], "estate_planning"),
            "category": "estate_planning"
        })

    return qa_pairs


def generate_expanded_tax_qa() -> list[dict]:
    """Generate tax planning Q&A."""
    qa_pairs = []

    tax_questions = [
        {
            "q": "What is tax-loss harvesting and how do I do it?",
            "a": """**Tax-Loss Harvesting: Reduce Taxes While Staying Invested**

**What It Is:**
Selling investments at a loss to offset capital gains and reduce taxes.

**How It Works:**

**Step 1:** Identify investments trading below your purchase price

**Step 2:** Sell the losing investment
- Realize the capital loss

**Step 3:** Immediately buy similar (not identical) investment
- Stay invested in the market
- Maintain your asset allocation

**Step 4:** Use losses to offset gains
- First offset capital gains
- Then offset up to $3,000 ordinary income
- Excess carries forward indefinitely

**Example:**
- You have $10,000 capital gain from selling Stock A
- Stock B is down $8,000 from purchase
- Sell Stock B, realize $8,000 loss
- Net taxable gain: only $2,000

**Wash Sale Rule (Critical!):**
- Can't buy "substantially identical" security within 30 days before or after sale
- If you do, loss is disallowed

**How to Avoid Wash Sale:**
- Wait 31 days to repurchase
- OR buy similar but not identical investment
  - Sell S&P 500 ETF (SPY) \u2192 Buy Total Stock Market (VTI)
  - Sell one company's fund \u2192 Buy competitor's similar fund

**When to Harvest:**
- Throughout the year (not just December)
- After significant market drops
- When you have gains to offset

**Who Benefits Most:**
- High-income earners (higher tax brackets)
- Active traders with gains
- Taxable brokerage accounts (NOT tax-advantaged accounts)

**Note:** Tax-loss harvesting only works in taxable accounts. Losses in 401(k) or IRA have no tax benefit."""
        },
        {
            "q": "How do I reduce my taxes legally?",
            "a": """**Legal Tax Reduction Strategies**

**1. Maximize Pre-Tax Retirement Contributions**
- 401(k): $23,000 ($30,500 if 50+)
- Traditional IRA: $7,000 ($8,000 if 50+) if eligible
- Every dollar reduces taxable income

**2. Use Health Savings Account (HSA)**
- Triple tax benefit:
  - Tax-deductible contribution
  - Tax-free growth
  - Tax-free withdrawal for medical
- 2024 limit: $4,150 individual / $8,300 family

**3. Take All Eligible Deductions**
**Standard vs. Itemized:**
- Standard (2024): $14,600 single / $29,200 married
- Itemize if you have more in:
  - Mortgage interest
  - State/local taxes (SALT) up to $10,000
  - Charitable donations
  - Medical expenses over 7.5% AGI

**4. Tax-Advantaged Investments**
- Municipal bonds (tax-free interest)
- Index funds (tax-efficient)
- Hold winners long-term (lower capital gains rate)

**5. Time Your Income and Deductions**
- Defer income to next year if possible
- Accelerate deductions into current year
- "Bunching" charitable donations

**6. Claim All Credits**
- Child Tax Credit: $2,000 per child
- Child and Dependent Care Credit
- Education credits (AOTC, Lifetime Learning)
- Earned Income Tax Credit
- Energy credits (solar, EV, heat pump)

**7. Business Owner Strategies**
- Home office deduction
- Vehicle expenses
- Retirement plans (SEP, Solo 401(k))
- Section 199A QBI deduction

**8. Investment Strategies**
- Tax-loss harvesting
- Asset location optimization
- Hold investments over 1 year for long-term rates

**What NOT to Do:**
\u274c Avoid earning more to stay in "lower bracket" (marginal rates!)
\u274c Overspend on deductible items
\u274c Hide income (tax evasion = criminal)

*Work with a CPA if your situation is complex.*"""
        },
    ]

    for item in tax_questions:
        qa_pairs.append({
            "instruction": item["q"],
            "input": "",
            "output": add_disclaimer(item["a"], "tax_planning"),
            "category": "tax_planning"
        })

    return qa_pairs


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Generate enhanced training data."""
    print("=" * 70)
    print("Elson Financial AI - Enhanced Training Data Generation v2")
    print("=" * 70)

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    all_qa = []

    # Generate all categories
    generators = [
        ("Multi-Turn Conversations", generate_multi_turn_conversations),
        ("Negative Examples", generate_negative_examples),
        ("Edge Cases", generate_edge_cases),
        ("Client Personas", generate_persona_qa),
        ("Expanded Retirement", generate_expanded_retirement_qa),
        ("Expanded Estate", generate_expanded_estate_qa),
        ("Tax Planning", generate_expanded_tax_qa),
    ]

    for name, generator in generators:
        qa = generator()
        print(f"  {name}: {len(qa)} pairs")
        all_qa.extend(qa)

    # Import and run original generator
    print("\n  Loading original generator...")
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_training_data import main as original_main
    original_qa = original_main()
    print(f"  Original generator: {len(original_qa)} pairs")
    all_qa.extend(original_qa)

    # Remove duplicates and shuffle
    seen = set()
    unique_qa = []
    for qa in all_qa:
        key = qa["instruction"][:100]
        if key not in seen:
            seen.add(key)
            unique_qa.append(qa)

    random.shuffle(unique_qa)

    print(f"\n{'=' * 70}")
    print(f"Total unique Q&A pairs: {len(unique_qa)}")
    print(f"{'=' * 70}")

    # Split
    total = len(unique_qa)
    train_size = int(total * 0.8)
    val_size = int(total * 0.1)

    train_data = unique_qa[:train_size]
    val_data = unique_qa[train_size:train_size + val_size]
    test_data = unique_qa[train_size + val_size:]

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    files = {
        "train": (train_data, f"train_v2_{timestamp}.json"),
        "val": (val_data, f"val_v2_{timestamp}.json"),
        "test": (test_data, f"test_v2_{timestamp}.json"),
        "complete": (unique_qa, "training_data_v2_complete.json"),
    }

    for name, (data, filename) in files.items():
        filepath = OUTPUT_PATH / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved: {filepath} ({len(data)} pairs)")

    # Category distribution
    print(f"\n{'=' * 70}")
    print("Category Distribution:")
    print(f"{'=' * 70}")
    categories = {}
    for qa in unique_qa:
        cat = qa.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = count / len(unique_qa) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    print(f"\n{'=' * 70}")
    print("Enhanced training data generation complete!")
    print(f"{'=' * 70}")

    return unique_qa


if __name__ == "__main__":
    main()
