#!/usr/bin/env python3
"""
Elson Financial AI - Comprehensive Training Data Generator v3
Target: 2000+ Q&A pairs with balanced distribution
"""

import json
import random
from pathlib import Path
from datetime import datetime

KNOWLEDGE_DIR = Path(__file__).parent.parent / "app/knowledge_base/wealth_management/data"
OUTPUT_DIR = Path(__file__).parent.parent / "training_data"

COMPLIANCE_DISCLAIMERS = [
    "\n\n*This is general educational information. Consult a qualified professional for personalized advice.*",
    "\n\n*Individual circumstances vary. Please consult with a licensed professional before making financial decisions.*",
    "\n\n*This information is for educational purposes only and does not constitute financial, legal, or tax advice.*",
]

def load_knowledge_base():
    """Load all knowledge base JSON files."""
    knowledge = {}
    for f in KNOWLEDGE_DIR.glob("*.json"):
        with open(f) as fp:
            knowledge[f.stem] = json.load(fp)
        print(f"  Loaded: {f.name}")
    return knowledge

def generate_professional_roles_qa(data: dict) -> list:
    """Generate Q&A from professional roles data."""
    qa_pairs = []

    for category, roles in data.items():
        if category == "metadata":
            continue
        if not isinstance(roles, dict):
            continue

        for role_key, role_info in roles.items():
            if not isinstance(role_info, dict):
                continue

            title = role_info.get("title", role_key.replace("_", " ").title())
            responsibilities = role_info.get("key_responsibilities", [])
            credentials = role_info.get("credentials", {})
            tier = role_info.get("min_service_tier", "growth")
            authority = role_info.get("decision_authority", "ADVISORY")

            # Q1: What does this role do?
            if responsibilities:
                qa_pairs.append({
                    "instruction": f"What are the key responsibilities of a {title}?",
                    "input": "",
                    "output": f"A {title} is responsible for: " + "; ".join(responsibilities[:5]) + "." + random.choice(COMPLIANCE_DISCLAIMERS),
                    "category": "professional_roles"
                })

            # Q2: What credentials are needed?
            if isinstance(credentials, dict):
                req_creds = credentials.get("required", [])
                pref_creds = credentials.get("preferred", [])
            elif isinstance(credentials, list):
                req_creds = credentials
                pref_creds = []
            else:
                req_creds = []
                pref_creds = []
            if req_creds or pref_creds:
                cred_text = f"To become a {title}, you need: "
                if req_creds:
                    cred_text += f"Required: {', '.join(req_creds)}. "
                if pref_creds:
                    cred_text += f"Preferred: {', '.join(pref_creds)}."
                qa_pairs.append({
                    "instruction": f"What credentials does a {title} need?",
                    "input": "",
                    "output": cred_text + random.choice(COMPLIANCE_DISCLAIMERS),
                    "category": "professional_roles"
                })

            # Q3: When do I need this professional?
            qa_pairs.append({
                "instruction": f"When should I hire a {title}?",
                "input": "",
                "output": f"A {title} is typically needed at the {tier} tier (${get_tier_range(tier)}). Their decision authority level is {authority}, meaning their guidance is {'binding and must be followed' if authority == 'BINDING' else 'advisory and helps inform your decisions'}." + random.choice(COMPLIANCE_DISCLAIMERS),
                "category": "professional_roles"
            })

    return qa_pairs

def get_tier_range(tier: str) -> str:
    tiers = {
        "foundation": "0-10K",
        "builder": "10K-75K",
        "growth": "75K-500K",
        "affluent": "500K-5M",
        "hnw_uhnw": "5M+"
    }
    return tiers.get(tier, "varies")

def generate_certifications_qa(data: dict) -> list:
    """Generate Q&A from certifications data."""
    qa_pairs = []

    for cert_key, cert_info in data.items():
        if cert_key == "metadata" or not isinstance(cert_info, dict):
            continue

        name = cert_info.get("name", cert_key)
        full_name = cert_info.get("full_name", name)
        study_hours = cert_info.get("study_hours", "varies")
        focus = cert_info.get("focus_areas", [])
        prereqs = cert_info.get("prerequisites", [])

        # Q1: What is this certification?
        qa_pairs.append({
            "instruction": f"What is the {name} certification?",
            "input": "",
            "output": f"The {name} ({full_name}) is a professional financial certification. It requires approximately {study_hours} of study and focuses on: {', '.join(focus[:4]) if focus else 'comprehensive financial planning'}." + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "certifications"
        })

        # Q2: How do I get this certification?
        qa_pairs.append({
            "instruction": f"How do I become a {name}?",
            "input": "",
            "output": f"To earn the {name} certification: 1) Complete {study_hours} of study, 2) Pass the required exam(s), 3) Meet experience requirements. Prerequisites: {', '.join(prereqs) if prereqs else 'Check with the certifying body'}." + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "certifications"
        })

        # Q3: Compare with other certifications
        qa_pairs.append({
            "instruction": f"Should I get a {name} or another certification?",
            "input": "",
            "output": f"The {name} is ideal if you want to focus on {', '.join(focus[:2]) if focus else 'financial planning'}. Consider your career goals: CFP for comprehensive planning, CFA for investment analysis, CPA for tax/accounting." + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "certifications"
        })

    return qa_pairs

def generate_estate_planning_qa(data: dict) -> list:
    """Generate Q&A from estate planning data."""
    qa_pairs = []
    topics = data.get("topics", data)

    if isinstance(topics, dict):
        for topic_key, topic_info in topics.items():
            if topic_key == "metadata":
                continue
            if isinstance(topic_info, dict):
                title = topic_info.get("title", topic_key.replace("_", " ").title())
                description = topic_info.get("description", "")
                benefits = topic_info.get("benefits", [])

                if description:
                    qa_pairs.append({
                        "instruction": f"What is {title} in estate planning?",
                        "input": "",
                        "output": description + random.choice(COMPLIANCE_DISCLAIMERS),
                        "category": "estate_planning"
                    })

                if benefits:
                    qa_pairs.append({
                        "instruction": f"What are the benefits of {title}?",
                        "input": "",
                        "output": f"Benefits of {title}: " + "; ".join(benefits[:4]) + "." + random.choice(COMPLIANCE_DISCLAIMERS),
                        "category": "estate_planning"
                    })

    # Add synthetic estate planning Q&A
    estate_qa = [
        ("What documents do I need for estate planning?", "Essential estate planning documents include: 1) Will - directs asset distribution, 2) Revocable Living Trust - avoids probate, 3) Durable Power of Attorney - financial decisions if incapacitated, 4) Healthcare Directive/Living Will - medical decisions, 5) HIPAA Authorization - medical information access. Consider updating these every 3-5 years or after major life events."),
        ("What's the difference between a will and a trust?", "A will takes effect after death and goes through probate (public, can take months). A trust takes effect immediately when funded, avoids probate (private, faster distribution), and can manage assets during incapacity. Trusts cost more upfront but often save money and time long-term."),
        ("How do I avoid estate taxes?", "Estate tax strategies include: 1) Annual gift exclusion ($18,000/person in 2024), 2) Lifetime exemption ($13.61M in 2024), 3) Irrevocable Life Insurance Trust (ILIT), 4) Grantor Retained Annuity Trust (GRAT), 5) Charitable remainder trusts. Work with an estate planning attorney and CPA for your situation."),
        ("What is probate and how do I avoid it?", "Probate is the court-supervised process of validating a will and distributing assets. It's public, time-consuming (6-24 months), and costly (2-7% of estate). Avoid it with: 1) Revocable living trust, 2) Joint ownership with right of survivorship, 3) Beneficiary designations on accounts, 4) Transfer-on-death deeds."),
        ("When should I update my estate plan?", "Update your estate plan after: marriage, divorce, birth/adoption, death of beneficiary, significant asset changes, moving to a new state, major tax law changes, or every 3-5 years. Review beneficiary designations annually on retirement accounts and insurance policies."),
    ]

    for q, a in estate_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "estate_planning"
        })

    return qa_pairs

def generate_trust_administration_qa(data: dict) -> list:
    """Generate Q&A from trust administration data."""
    qa_pairs = []

    trust_qa = [
        ("What is a trustee's fiduciary duty?", "A trustee has three core fiduciary duties: 1) Duty of Care - manage trust assets prudently, 2) Duty of Loyalty - act solely in beneficiaries' interest, avoid conflicts, 3) Duty of Good Faith - act honestly and fairly. Breach of fiduciary duty can result in personal liability, removal, and legal action."),
        ("What is a Trust Protector?", "A Trust Protector serves as oversight to the trustee with powers including: removing/replacing trustees, approving/vetoing investments, amending trust terms for unforeseen circumstances, changing trust situs, and resolving disputes. Should be an independent professional (attorney, CPA), not a family member."),
        ("What's the difference between revocable and irrevocable trusts?", "Revocable trusts: you maintain control, can modify/revoke, assets remain in your estate for taxes. Irrevocable trusts: you give up control, generally can't modify, assets removed from estate (tax benefits), creditor protection. Choose based on your goals for control vs. protection."),
        ("What are a trustee's responsibilities?", "Trustee responsibilities include: 1) Managing trust assets prudently, 2) Keeping accurate records, 3) Filing trust tax returns (Form 1041), 4) Issuing K-1s to beneficiaries, 5) Making distributions per trust terms, 6) Communicating with beneficiaries, 7) Avoiding conflicts of interest."),
        ("Should I use a corporate or individual trustee?", "Corporate trustees offer: professional management, continuity, institutional expertise, liability coverage. Individual trustees offer: personal knowledge of family, lower fees, flexibility. Many use co-trustees (one of each) for balance. Consider the trust's complexity and family dynamics."),
    ]

    for q, a in trust_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "trust_administration"
        })

    return qa_pairs

def generate_retirement_qa(data: dict) -> list:
    """Generate comprehensive retirement planning Q&A."""
    qa_pairs = []

    retirement_qa = [
        ("What's the difference between a 401k and IRA?", "401(k): employer-sponsored, higher limits ($23,000 in 2024, +$7,500 catch-up if 50+), possible employer match. IRA: individual account, lower limits ($7,000 in 2024, +$1,000 catch-up), more investment options. Both have Traditional (pre-tax) and Roth (after-tax) versions. Contribute to both if possible."),
        ("Should I choose Traditional or Roth?", "Traditional: tax deduction now, pay taxes in retirement. Roth: pay taxes now, tax-free in retirement. Choose Roth if: you expect higher taxes later, want tax-free growth, are young with lower income. Choose Traditional if: you need the deduction now, expect lower taxes in retirement, are in peak earning years."),
        ("How much do I need to retire?", "The 4% rule suggests you need 25x annual expenses. Example: $60,000/year expenses = $1.5M needed. Factors: desired lifestyle, healthcare costs, Social Security, pension, life expectancy. A more conservative 3.5% withdrawal rate means 28.5x expenses. Run projections with different scenarios."),
        ("What is a Roth conversion?", "A Roth conversion moves money from Traditional IRA/401k to Roth IRA. You pay taxes now on the converted amount, then it grows tax-free forever. Best when: your income is temporarily low, you expect higher future taxes, you want to reduce required minimum distributions (RMDs), you have cash to pay the taxes."),
        ("What are Required Minimum Distributions (RMDs)?", "RMDs are mandatory withdrawals from Traditional retirement accounts starting at age 73 (75 in 2033). Calculated based on account balance and life expectancy. Penalty for missing: 25% of amount not withdrawn. Roth IRAs have no RMDs for the original owner, making them excellent for estate planning."),
        ("How should I invest for retirement?", "Asset allocation depends on timeline: 30+ years out: 80-90% stocks, 10-20% bonds. 20 years: 70-80% stocks. 10 years: 60-70% stocks. In retirement: 40-60% stocks for growth. Use target-date funds for automatic rebalancing, or build a diversified portfolio of low-cost index funds."),
        ("What is FIRE (Financial Independence, Retire Early)?", "FIRE aims for early retirement through high savings rates (50-70% of income). Variations: LeanFIRE ($40k/year), FIRE ($40-100k), FatFIRE ($100k+), CoastFIRE (enough saved that growth alone funds retirement), BaristaFIRE (part-time work for benefits). Requires 25-33x annual expenses saved."),
        ("How does Social Security work?", "Social Security is based on your highest 35 years of earnings. Claim at 62 (reduced ~30%), full retirement age 66-67 (100%), or delay to 70 (+24-32% increase). Spousal benefits up to 50% of partner's. Strategy: higher earner delay to 70, lower earner may claim earlier. Run SSA.gov calculator."),
        ("What should I do with my old 401k?", "Options: 1) Leave it (if fees are low, balance >$5k), 2) Roll to new employer's 401k, 3) Roll to IRA (most flexibility), 4) Cash out (avoid - 10% penalty + taxes). Rolling to IRA gives you the most investment options. Never cash out unless absolute emergency."),
        ("How do I catch up on retirement savings?", "Strategies: 1) Max out catch-up contributions (extra $7,500 for 401k at 50+), 2) Contribute to HSA for medical expenses, 3) Open taxable brokerage account, 4) Delay retirement or work part-time, 5) Reduce expenses to save more, 6) Consider downsizing home to free up equity."),
    ]

    for q, a in retirement_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "retirement_planning"
        })

    return qa_pairs

def generate_tax_planning_qa() -> list:
    """Generate tax planning Q&A."""
    qa_pairs = []

    tax_qa = [
        ("What is tax-loss harvesting?", "Tax-loss harvesting sells investments at a loss to offset capital gains. Rules: 1) Wash sale rule - can't buy same/substantially identical security within 30 days, 2) Net losses offset gains, then up to $3,000 of ordinary income, 3) Excess losses carry forward. Automate with direct indexing or tax-managed funds."),
        ("How can I reduce my taxable income?", "Legal strategies: 1) Max retirement contributions (401k, IRA), 2) HSA contributions, 3) 529 plan contributions (state deduction), 4) Charitable giving (bunching, DAFs), 5) Tax-loss harvesting, 6) Business deductions if self-employed, 7) Real estate depreciation. Work with a CPA for your situation."),
        ("What's the difference between long-term and short-term capital gains?", "Short-term gains (held <1 year) taxed as ordinary income (10-37%). Long-term gains (held >1 year) taxed at preferential rates: 0% (up to $47,025 single), 15% ($47,025-$518,900), 20% (above). Hold investments >1 year when possible for significant tax savings."),
        ("Should I contribute to traditional or Roth accounts?", "Traditional reduces taxes now; Roth provides tax-free withdrawals later. Factors: current vs. future tax rate, income phase-outs, RMD requirements. Strategy: contribute to both (tax diversification). If income is high, backdoor Roth IRA ($7k) and mega backdoor Roth 401k ($46k+) are options."),
        ("What is a Donor-Advised Fund (DAF)?", "A DAF is a charitable giving account. Benefits: 1) Immediate tax deduction when contributed, 2) Grants to charities anytime, 3) Donate appreciated stock (avoid capital gains), 4) Bunch multiple years' giving for itemization, 5) Investment growth is tax-free. Minimum varies by provider ($5k-$25k typical)."),
        ("How does the estate tax work?", "Federal estate tax applies to estates over $13.61M (2024, $27.22M for married couples). Rate is 40% on amounts above exemption. Strategies: annual gifts ($18k/person), lifetime gifts (uses exemption), trusts (GRAT, ILIT, SLAT), charitable giving. State estate taxes may have lower thresholds."),
        ("What tax forms do I need for trusts?", "Trusts file Form 1041 (trust income tax return). Beneficiaries receive Schedule K-1 showing their share of income. Grantor trusts report on grantor's personal return. Deadlines: April 15 (same as individuals). Complex trusts may need estimated payments quarterly."),
        ("How do I minimize taxes on stock options?", "ISO (Incentive Stock Options): exercise and hold >1 year for LTCG treatment, but watch AMT. NSO (Non-Qualified): taxed as ordinary income at exercise. Strategies: 1) Exercise in low-income years, 2) 83(b) election for early exercise, 3) Qualified Small Business Stock exclusion, 4) Charitable donation of appreciated shares."),
    ]

    for q, a in tax_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "tax_planning"
        })

    return qa_pairs

def generate_college_planning_qa(data: dict) -> list:
    """Generate college planning Q&A."""
    qa_pairs = []

    college_qa = [
        ("What is a 529 plan?", "A 529 is a tax-advantaged education savings account. Benefits: 1) Tax-free growth, 2) Tax-free withdrawals for qualified education expenses, 3) High contribution limits ($300k+), 4) State tax deduction in many states, 5) Anyone can contribute, 6) Can change beneficiaries. Start early for maximum compound growth."),
        ("Should I use a 529 or Coverdell ESA?", "529: higher limits (no annual cap), broader state benefits, newer rules allow K-12 use. Coverdell: $2,000/year limit, income restrictions, more investment flexibility. For most families, 529 is better due to higher limits. Consider both if you want more investment control."),
        ("How does financial aid work?", "FAFSA determines Expected Family Contribution (EFC). Considers: income (heavily weighted), assets (counted less), family size, number in college. Parent assets count ~5.6%, student assets ~20%. Strategies: spend down student assets, maximize retirement contributions, understand CSS Profile for private schools."),
        ("How much should I save for college?", "Average 4-year public: ~$25k/year. Private: ~$55k/year. Aim to save 1/3, borrow 1/3, pay from income 1/3. Monthly savings needed (18 years, 7% return): $250/month = ~$100k; $500/month = ~$200k. Start early - compound growth does the heavy lifting."),
        ("What if my child doesn't go to college?", "529 options: 1) Change beneficiary to sibling, cousin, yourself, 2) Use for trade school, apprenticeship programs, 3) Pay student loans ($10k lifetime limit per beneficiary), 4) Roll to Roth IRA (new rule: up to $35k after 15 years), 5) Withdraw (10% penalty + taxes on earnings only)."),
        ("What are qualified education expenses?", "529 qualified expenses: tuition, room & board, books & supplies, computers & software, internet, K-12 tuition ($10k/year limit), student loan payments ($10k lifetime). Not qualified: transportation, health insurance, extracurriculars (penalty + taxes on earnings if used)."),
    ]

    for q, a in college_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "college_planning"
        })

    return qa_pairs

def generate_investment_qa() -> list:
    """Generate investment-related Q&A."""
    qa_pairs = []

    investment_qa = [
        ("What is asset allocation?", "Asset allocation divides investments among asset classes (stocks, bonds, cash, alternatives) based on goals, timeline, and risk tolerance. Common rule: 110 minus age = stock percentage. Example: age 30 = 80% stocks, 20% bonds. Rebalance annually to maintain target allocation."),
        ("Should I use index funds or actively managed funds?", "Index funds: lower fees (0.03-0.20%), match market returns, tax-efficient. Active funds: higher fees (0.50-1.5%), most underperform indexes long-term. Research shows ~90% of active funds underperform over 15+ years. Use index funds for core holdings; consider active for specific sectors or alternatives."),
        ("What is diversification?", "Diversification spreads risk across investments so poor performance in one doesn't devastate your portfolio. Diversify across: asset classes (stocks, bonds), geography (US, international), sectors (tech, healthcare), company size (large, mid, small cap). A diversified portfolio reduces volatility without sacrificing returns."),
        ("What's the difference between ETFs and mutual funds?", "ETFs: trade like stocks (intraday), lower minimums, more tax-efficient, typically lower fees. Mutual funds: trade once daily at NAV, may have minimums ($1k-$3k), automatic investing easier. For taxable accounts, ETFs are usually better. In retirement accounts, either works."),
        ("How do I start investing with little money?", "Start with: 1) Employer 401k (especially for match), 2) IRA ($7,000/year), 3) Brokerage with no minimums (Fidelity, Schwab), 4) Fractional shares ($1 minimum). Prioritize: emergency fund first, then retirement accounts for tax benefits, then taxable brokerage. Consistency matters more than amount."),
        ("What is rebalancing?", "Rebalancing restores your target asset allocation when market movements shift it. Example: 80/20 stocks/bonds drifts to 85/15, you sell stocks and buy bonds. Methods: 1) Calendar (annually), 2) Threshold (when >5% off target), 3) Cash flows (direct new money to underweight assets)."),
        ("What are alternative investments?", "Alternatives include: real estate (REITs, direct), private equity, hedge funds, commodities, cryptocurrency. Benefits: diversification, potentially higher returns. Risks: less liquidity, higher fees, complexity. Most investors should keep alternatives to 10-20% max. Start with REITs or commodity funds for simplicity."),
        ("How do I evaluate investment risk?", "Key metrics: 1) Standard deviation (volatility), 2) Beta (market sensitivity), 3) Sharpe ratio (risk-adjusted return), 4) Maximum drawdown (worst peak-to-trough). Your risk tolerance depends on: timeline, income stability, sleeping at night factor. Younger investors can take more risk; those near retirement should be more conservative."),
    ]

    for q, a in investment_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "investment"
        })

    return qa_pairs

def generate_financial_literacy_qa() -> list:
    """Generate financial literacy basics Q&A."""
    qa_pairs = []

    literacy_qa = [
        ("How do I create a budget?", "Follow the 50/30/20 rule: 50% needs (housing, food, utilities), 30% wants (entertainment, dining), 20% savings/debt. Steps: 1) Track spending for 30 days, 2) Categorize expenses, 3) Set limits per category, 4) Automate savings first, 5) Review monthly. Apps like YNAB or Mint can help."),
        ("How much should I have in an emergency fund?", "3-6 months of essential expenses. 6+ months if: self-employed, single income household, volatile industry. Keep in high-yield savings account (4-5% APY currently). Build gradually - start with $1,000, then 1 month, then full fund. Don't invest emergency fund."),
        ("How do I pay off debt?", "Two strategies: 1) Avalanche (highest interest first) - mathematically optimal, saves most interest. 2) Snowball (smallest balance first) - psychological wins keep you motivated. Always pay minimums on all debts. For high-interest debt (>7%), prioritize payoff over investing beyond employer match."),
        ("What's the difference between good and bad debt?", "Good debt: low interest, builds assets or income (mortgage, student loans, business loans). Bad debt: high interest, depreciating assets (credit cards, car loans, payday loans). Focus on eliminating bad debt quickly. Good debt is fine to carry if rate is below investment returns (~7-10%)."),
        ("How do I build credit?", "Steps: 1) Get a secured credit card, 2) Become authorized user on parent's card, 3) Pay in full every month (or keep <30% utilization), 4) Keep old accounts open, 5) Mix of credit types helps. Never miss payments - payment history is 35% of score. Check free score at Credit Karma."),
        ("What insurance do I need?", "Essential: health insurance, auto (if you drive), renters/homeowners. Important: life (if dependents), disability (protects income), umbrella (liability protection). Optional: long-term care (consider at 50+). Get quotes from multiple providers. Higher deductibles = lower premiums but more out-of-pocket."),
        ("How do I negotiate salary?", "Preparation: research market rates (Glassdoor, Levels.fyi), know your value, have competing offers if possible. Strategy: 1) Let them name first number, 2) Counter 10-20% higher, 3) Negotiate total comp (base, bonus, equity, PTO), 4) Get it in writing. Practice your pitch. Silence is powerful."),
        ("What's the best way to save money?", "Automate first: set up direct deposit to savings before you see it. Cut big 3: housing (<30% income), transportation, food. Shop insurance annually. Use cash back cards (pay in full). Batch errands, meal prep. The goal is sustainable habits, not deprivation. Save raises and windfalls."),
    ]

    for q, a in literacy_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "financial_literacy"
        })

    return qa_pairs

def generate_succession_qa() -> list:
    """Generate business succession planning Q&A."""
    qa_pairs = []

    succession_qa = [
        ("How do I plan business succession?", "Key steps: 1) Identify successors (family, employees, outside buyers), 2) Get business valuation, 3) Structure the deal (sale, gift, installment), 4) Minimize taxes (GRAT, ESOP, installment sale), 5) Train successors (3-5 years), 6) Update estate plan. The 'Dream Team': CFP (quarterback), M&A attorney, CPA, valuation expert, estate attorney."),
        ("What is a buy-sell agreement?", "A buy-sell agreement is a contract that determines what happens to business ownership when an owner dies, becomes disabled, retires, or wants to sell. Types: 1) Cross-purchase (owners buy each other out), 2) Redemption (company buys shares), 3) Hybrid. Fund with life insurance. Review annually."),
        ("How do I value my business?", "Methods: 1) Asset-based (net asset value), 2) Market approach (comparable sales), 3) Income approach (discounted cash flow). Factors: revenue, profit margins, growth rate, industry, customer concentration, management depth. Get a formal valuation from ASA or CVA credentialed appraiser for tax and legal purposes."),
        ("Should I sell to family or outsiders?", "Family sale: preserves legacy, flexible terms, may get discount. Risks: family conflict, capable successor available? Outside sale: market price, clean break, professional buyers. Consider: family readiness, your retirement needs, business sustainability. Many do hybrid: management to family, equity to private equity."),
        ("What is an ESOP?", "Employee Stock Ownership Plan lets employees become owners. Benefits: tax-deductible contributions, seller can defer capital gains, motivates employees, preserves company culture. Works best for: profitable companies, 20+ employees, owners wanting to exit gradually. Complex to set up - need specialized attorney."),
    ]

    for q, a in succession_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "succession_planning"
        })

    return qa_pairs

def generate_compliance_qa() -> list:
    """Generate compliance and regulatory Q&A."""
    qa_pairs = []

    compliance_qa = [
        ("What is AML/KYC compliance?", "Anti-Money Laundering (AML) and Know Your Customer (KYC) are regulatory requirements. Five pillars: 1) Customer Identification Program (CIP), 2) Customer Due Diligence (CDD), 3) Suspicious Activity Reporting (SAR), 4) PEP screening, 5) Beneficial ownership verification. SAR required for transactions over $10,000."),
        ("What are fiduciary duties?", "Fiduciary duties are legal obligations to act in another's best interest. Three core duties: 1) Duty of Care (prudent decision-making), 2) Duty of Loyalty (avoid conflicts of interest), 3) Duty of Good Faith (act honestly). Applies to trustees, investment advisers (RIAs), ERISA plans. Breach can result in personal liability."),
        ("What's the difference between fiduciary and suitability?", "Fiduciary: must act in client's BEST interest, disclose conflicts, fee transparency (RIAs, some advisors). Suitability: recommendation must be SUITABLE, not necessarily best (brokers, insurance agents). Ask your advisor: 'Are you a fiduciary?' Get it in writing."),
        ("What are RMD rules?", "Required Minimum Distributions begin at age 73 (75 starting 2033) for Traditional IRA, 401k, 403b. Calculated: account balance / life expectancy factor. Penalty: 25% of missed amount (reduced from 50%). Roth IRAs have no RMDs. Inherited IRAs now follow 10-year rule for most non-spouse beneficiaries."),
        ("What records should I keep?", "Tax records: 7 years (IRS can audit 3 years, 6 if >25% underreporting). Investment records: cost basis until sold + 7 years. Property records: entire ownership + 7 years. Estate documents: permanent. Digital backup recommended. Organize by year and category."),
    ]

    for q, a in compliance_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "compliance"
        })

    return qa_pairs

def generate_multi_turn_conversations() -> list:
    """Generate multi-turn conversation examples."""
    conversations = [
        # Retirement planning conversation
        {
            "instruction": "I'm 35 and want to retire early. Where do I start?",
            "input": "",
            "output": "Great goal! Let's assess your situation. First, what's your current annual income and savings rate? For early retirement (FIRE), you typically need to save 50-70% of income and accumulate 25-33x annual expenses. What are your current retirement account balances and monthly expenses?",
            "category": "multi_turn"
        },
        {
            "instruction": "I make $120k, save about 20%, have $150k in 401k. Monthly expenses around $4k.",
            "input": "Previous context: User is 35, wants early retirement",
            "output": "Good foundation! At $4k/month ($48k/year), you need roughly $1.2M-$1.6M (25-33x). With $150k and current savings, you're on track for traditional retirement but need to boost savings for early retirement. Recommendations: 1) Increase savings to 40%+ ($48k/year), 2) Max 401k ($23k), open Roth IRA ($7k), and use taxable brokerage for the rest, 3) At 7% returns with increased savings, you could hit $1.2M by age 50. Want to discuss how to find that extra savings?",
            "category": "multi_turn"
        },
        # Estate planning conversation
        {
            "instruction": "My parents are getting older. How do I help them with estate planning?",
            "input": "",
            "output": "This is a sensitive but important conversation. Start by understanding what documents they already have. Key questions: 1) Do they have a will? 2) Is there a power of attorney (financial and healthcare)? 3) Are beneficiary designations updated on accounts? What do you know about their current planning?",
            "category": "multi_turn"
        },
        {
            "instruction": "They have old wills from 20 years ago. Not sure about the rest.",
            "input": "Previous context: Helping aging parents with estate planning",
            "output": "Twenty-year-old wills likely need updating - laws change, situations change. Priority actions: 1) Schedule estate attorney consultation to update wills, 2) Establish Durable Power of Attorney (financial) naming you or sibling, 3) Create Healthcare Directive/Living Will, 4) Review all account beneficiaries, 5) Consider revocable living trust if assets >$100k (avoids probate). Would you like guidance on how to start this conversation with them?",
            "category": "multi_turn"
        },
        # Investment conversation
        {
            "instruction": "I have $50k to invest. What should I do with it?",
            "input": "",
            "output": "Before recommending investments, I need to understand your situation. Key questions: 1) What's this money for? (retirement, house, general wealth), 2) When will you need it? (timeline), 3) Do you have an emergency fund? 4) Any high-interest debt? 5) Are you maxing retirement accounts? What are your answers to these?",
            "category": "multi_turn"
        },
        {
            "instruction": "It's for long-term wealth, 20+ years. Have 6 months emergency, no debt, maxing 401k.",
            "input": "Previous context: $50k to invest, long-term horizon",
            "output": "Excellent position! For 20+ year horizon with retirement covered, a taxable brokerage account makes sense. Recommended allocation: 1) 60% US total market (VTI/VTSAX), 2) 25% International (VXUS/VTIAX), 3) 15% bonds (BND) for stability. Tax-efficient strategy: put bonds in 401k if possible, keep stocks in taxable (better for tax-loss harvesting, lower cap gains rates). Invest all at once (lump sum beats DCA 2/3 of time) or split over 3-6 months if nervous. Which approach feels right?",
            "category": "multi_turn"
        },
    ]

    return conversations

def generate_negative_examples() -> list:
    """Generate examples of what NOT to recommend."""
    negative_examples = [
        {
            "instruction": "Should I put my emergency fund in Bitcoin for higher returns?",
            "input": "",
            "output": "No, this is a poor strategy. Emergency funds must be: 1) Highly liquid (accessible within days), 2) Stable (not volatile), 3) Safe (no risk of loss). Bitcoin fails all three - it can drop 50%+ overnight. Keep emergency funds in high-yield savings (currently 4-5% APY) or money market. Crypto is for money you can afford to lose, not money you need for emergencies.",
            "category": "negative_example"
        },
        {
            "instruction": "My friend says I should take out my 401k early to invest in real estate.",
            "input": "",
            "output": "This is generally bad advice. Early 401k withdrawal triggers: 1) 10% penalty (if under 59.5), 2) Income tax on full amount (could be 22-37%), 3) Lost compound growth. A $100k withdrawal might net only $60k after penalties/taxes. Better options: HELOC, 401k loan (must repay), save separately for down payment, or SDIRA for real estate. Keep retirement funds for retirement.",
            "category": "negative_example"
        },
        {
            "instruction": "I'm 28 and want to buy a whole life insurance policy as an investment.",
            "input": "",
            "output": "Whole life insurance is rarely a good investment for young people. Issues: 1) High fees (often 50%+ of first year premiums go to commissions), 2) Low returns (2-4% typical), 3) Complexity, 4) Surrender penalties for years. Better approach: buy cheap term life if you have dependents, invest the difference in index funds. A 28-year-old's $500/month is better in a Roth IRA than whole life.",
            "category": "negative_example"
        },
        {
            "instruction": "I want to day trade my retirement account to grow it faster.",
            "input": "",
            "output": "Day trading retirement accounts is extremely risky. Problems: 1) Studies show 70-90% of day traders lose money, 2) Pattern Day Trader rules require $25k minimum, 3) Tax-advantaged growth is lost to frequent trading, 4) You're competing against algorithms. For retirement: use buy-and-hold index investing, which beats most active traders. If you want to trade, use a small (<5%) play money account you can afford to lose.",
            "category": "negative_example"
        },
        {
            "instruction": "Should I cash out my 401k to pay off my mortgage early?",
            "input": "",
            "output": "Almost never a good idea. Math doesn't work: 1) 10% penalty + 22-37% taxes = losing 32-47% immediately, 2) Mortgage rates around 6-7% are lower than market returns (7-10%), 3) You lose tax-advantaged compound growth forever. Exception: bankruptcy imminent (401k is protected). Better: make extra payments from cash flow if you want mortgage paid off, keep 401k growing.",
            "category": "negative_example"
        },
        {
            "instruction": "A financial advisor said I should put 50% of my portfolio in their proprietary fund.",
            "input": "",
            "output": "This is a red flag. Concerns: 1) Proprietary funds often have higher fees benefiting the advisor, 2) 50% in one fund lacks diversification, 3) Advisor may have conflicts of interest. Ask: What are the fees? Are you a fiduciary? Can I see alternatives? A good advisor recommends low-cost diversified funds, not concentrated positions in their own products. Consider fee-only fiduciary advisors instead.",
            "category": "negative_example"
        },
        {
            "instruction": "I heard I should always avoid all debt.",
            "input": "",
            "output": "This is overly simplistic. Strategic debt can build wealth. Good debt examples: 1) Mortgage (builds equity, tax-deductible), 2) Student loans for high-ROI degree (if reasonable amount), 3) Business loans (invest in growth), 4) 0% financing (invest the cash instead). Key: debt cost should be less than what the money can earn. Avoid: credit cards, payday loans, car loans on depreciating assets.",
            "category": "negative_example"
        },
    ]

    return negative_examples

def generate_edge_cases() -> list:
    """Generate edge case scenarios."""
    edge_cases = [
        {
            "instruction": "I just inherited $500,000. What should I do?",
            "input": "",
            "output": "First, don't rush - take 6-12 months to process and plan. Immediate steps: 1) Park in high-yield savings, 2) Understand tax implications (inherited IRAs have 10-year rule), 3) Pay off high-interest debt. Then: 1) Max all retirement accounts, 2) Establish/bolster emergency fund, 3) Consider a fee-only financial planner for this amount, 4) Invest per your timeline (index funds for long-term). Common mistake: lifestyle inflation - this amount can generate $20k/year forever at 4%.",
            "category": "edge_case"
        },
        {
            "instruction": "I'm getting divorced. What happens to our retirement accounts?",
            "input": "",
            "output": "Retirement accounts are typically marital property, divided per state law and settlement. Process: 1) 401k/pension requires QDRO (Qualified Domestic Relations Order) - a legal document ordering the plan to divide, 2) IRA can be transferred directly via divorce decree (no QDRO needed), 3) Transfers under divorce settlement avoid early withdrawal penalties. Critical: ensure QDRO is filed and accepted before divorce is finalized. Get a QDRO specialist - errors can be costly.",
            "category": "edge_case"
        },
        {
            "instruction": "I'm a gig worker with irregular income. How do I plan finances?",
            "input": "",
            "output": "Gig work requires extra planning. Strategies: 1) Larger emergency fund (6-12 months, not 3-6), 2) Pay yourself a 'salary' from a separate account to smooth income, 3) Set aside 25-30% for taxes immediately (quarterly estimated payments), 4) SEP-IRA or Solo 401k for retirement (25% of net self-employment income), 5) Get your own health insurance (marketplace or professional association), 6) Consider incorporation for liability and taxes.",
            "category": "edge_case"
        },
        {
            "instruction": "I'm 55 and have almost nothing saved for retirement. Is it too late?",
            "input": "",
            "output": "It's not too late, but requires aggressive action. Strategies: 1) Max 401k with catch-up ($30,500 total), 2) Max IRA with catch-up ($8,000), 3) Delay Social Security to 70 (+24-32%), 4) Plan to work longer or part-time in retirement, 5) Aggressively reduce expenses and save 30-50% of income, 6) Consider downsizing home, relocating to lower-cost area. In 10 years, $38,500/year at 7% = ~$540k. Combined with Social Security and reduced expenses, retirement is possible.",
            "category": "edge_case"
        },
        {
            "instruction": "I won $50,000 in a lawsuit settlement. Is this taxable?",
            "input": "",
            "output": "It depends on the settlement type. Generally: 1) Physical injury/sickness compensation = not taxable, 2) Emotional distress (not from physical injury) = taxable, 3) Lost wages = taxable, 4) Punitive damages = taxable, 5) Interest on settlement = taxable. Check your settlement agreement for how it's characterized. Consult a CPA - incorrect reporting can trigger IRS issues. If taxable, set aside 25-30% for federal and state taxes.",
            "category": "edge_case"
        },
    ]

    return edge_cases

def generate_persona_qa() -> list:
    """Generate Q&A for different client personas."""
    personas = [
        # Young professional
        {
            "instruction": "I'm 25, just started my first job making $65k. What should I prioritize financially?",
            "input": "",
            "output": "Congratulations! Priority order: 1) 401k up to employer match (free money), 2) Build 3-month emergency fund in high-yield savings, 3) Pay off any high-interest debt (>7%), 4) Increase 401k to 15% or max, 5) Open Roth IRA ($7k/year - tax-free growth for 40 years!), 6) Additional goals (house down payment, etc.). At 25, time is your superpower - $500/month invested now = $1.3M+ by 65 at 7% returns. Start the habit early.",
            "category": "persona"
        },
        {
            "instruction": "I'm a single parent with two kids. How do I balance saving for their college and my retirement?",
            "input": "",
            "output": "Important principle: prioritize your retirement over college - kids can get loans/scholarships, you can't borrow for retirement. Strategy: 1) Max employer 401k match first, 2) Then fund 529 (even $100-200/month helps), 3) Increase retirement contributions, 4) Apply for financial aid regardless of income. If choosing between the two, retirement wins. Kids can work, get scholarships, attend community college then transfer, or take loans. You being financially secure helps them more long-term.",
            "category": "persona"
        },
        {
            "instruction": "I'm 60, planning to retire at 65. How should I adjust my portfolio?",
            "input": "",
            "output": "Five years out, start transitioning but don't be too conservative - you need 30 years of retirement income! Suggested allocation: 1) Shift to 55-65% stocks, 35-45% bonds (not all bonds), 2) Build 2-3 years of expenses in stable investments (bonds, money market), 3) Plan Social Security strategy (delay if possible), 4) Calculate retirement income needs: multiply expenses by 25, 5) Review healthcare bridge (Medicare starts at 65), 6) Consider sequence of returns risk - bad returns early in retirement hurt more.",
            "category": "persona"
        },
        {
            "instruction": "I'm a small business owner. How is retirement planning different for me?",
            "input": "",
            "output": "Business owners have unique options. Retirement vehicles: 1) SEP-IRA: simple, contribute up to 25% of net self-employment income (max $69k for 2024), 2) Solo 401k: higher contribution potential (employee + employer = $69k + $7,500 catch-up), Roth option, 3) SIMPLE IRA: if you have employees, lower limits. Also: 1) Your business is NOT your retirement plan - diversify, 2) Consider selling the business as part of retirement, 3) Work with CPA for tax optimization between business and personal.",
            "category": "persona"
        },
    ]

    return personas

def generate_goal_planning_qa() -> list:
    """Generate goal-based planning Q&A."""
    goal_qa = [
        ("How do I save for a house down payment?", "Target: 20% down payment (avoids PMI) + 3-5% closing costs. For $400k home: need $80-100k. Strategy: 1) High-yield savings or CD ladder (no risk), 2) Timeline <3 years = keep safe, 3) Timeline 5+ years = consider conservative investments (60/40), 4) First-time buyer programs may allow 3-10% down, 5) Automate monthly savings. $1,500/month for 5 years at 4% = ~$100k."),
        ("Should I pay off debt or invest?", "Compare after-tax interest rate vs expected returns. General rules: 1) High-interest debt (>7%): pay off first, 2) Low-interest debt (<4%): invest instead, 3) 4-7%: do both (get 401k match, then pay debt, then invest more). Always: make minimum payments, get employer match (100% return), keep emergency fund. The math often favors investing, but peace of mind matters too."),
        ("How do I set financial goals?", "Use SMART framework: Specific, Measurable, Achievable, Relevant, Time-bound. Example: 'Save $20k for emergency fund in 18 months' not 'save more money.' Steps: 1) List goals by timeline (short <1yr, medium 1-5yr, long 5+yr), 2) Calculate amounts needed, 3) Assign monthly savings to each, 4) Automate transfers, 5) Review quarterly. Prioritize: emergency fund → employer match → high-interest debt → retirement → other goals."),
        ("What is the financial order of operations?", "The Money Guy Show's 'Financial Order of Operations': 1) Deductibles covered (emergency starter), 2) Employer match (401k), 3) High-interest debt (>6%), 4) Emergency fund (3-6 months), 5) Roth IRA/HSA, 6) Max retirement (401k to $23k), 7) Hyper-accumulation (25%+ of income), 8) Prepay mortgage, 9) Low-interest debt. This optimizes returns while building security."),
        ("How much do I need for financial independence?", "Formula: Annual expenses × 25 = FIRE number (4% rule). Conservative: expenses × 33 (3% rule). Example: $60k/year expenses = $1.5M-$2M needed. Factors: 1) Healthcare before Medicare (add $15-20k/year), 2) Taxes on withdrawals, 3) Inflation, 4) Desired lifestyle. Calculate your number, then work backwards to determine savings rate needed."),
    ]

    qa_pairs = []
    for q, a in goal_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "goal_planning"
        })

    return qa_pairs

def generate_credit_financing_qa() -> list:
    """Generate credit and financing Q&A."""
    credit_qa = [
        ("How do I build business credit?", "Steps: 1) Form LLC or corporation (separate from personal), 2) Get EIN from IRS, 3) Open business bank account and credit card, 4) Register with Dun & Bradstreet (PAYDEX score), 5) Establish trade lines with vendors that report, 6) Pay all bills early (best) or on time, 7) Monitor business credit reports. Takes 6-12 months to establish. Keep personal and business finances separate."),
        ("What SBA loan programs exist?", "Main SBA programs: 1) 7(a) loans: up to $5M, general business use, 2) CDC/504: up to $5.5M, real estate and equipment, 3) Microloans: up to $50k, newer businesses, 4) SBA Express: up to $500k, faster approval. Benefits: lower down payments (10-20%), longer terms, government guarantee reduces lender risk. Drawbacks: more paperwork, slower than conventional loans."),
        ("What is invoice factoring?", "Factoring sells invoices to a third party at a discount for immediate cash. You get 70-90% of invoice value upfront, rest (minus fees) when customer pays. Costs: 1-5% per month. Use when: need cash flow, have creditworthy customers, traditional financing unavailable. Alternative: invoice financing (borrow against invoices but keep ownership). Both are expensive - use short-term only."),
        ("Should I use personal or business credit for my startup?", "Avoid personal credit for business when possible. Risks: personal liability, mixed credit history, harder to track expenses. Reality: most startups need personal guarantees initially. Strategy: 1) Start building business credit immediately, 2) Get business credit card, 3) As business grows, transition to business-only financing, 4) Keep clear records, 5) Work toward removing personal guarantees. Protect personal assets with LLC structure."),
    ]

    qa_pairs = []
    for q, a in credit_qa:
        qa_pairs.append({
            "instruction": q,
            "input": "",
            "output": a + random.choice(COMPLIANCE_DISCLAIMERS),
            "category": "credit_financing"
        })

    return qa_pairs

def main():
    print("=" * 70)
    print("Elson Financial AI - Comprehensive Training Data Generator v3")
    print("Target: 2000+ balanced Q&A pairs")
    print("=" * 70)

    OUTPUT_DIR.mkdir(exist_ok=True)

    print("\nLoading knowledge base...")
    knowledge = load_knowledge_base()
    print(f"Loaded {len(knowledge)} knowledge files")

    all_qa = []

    # Generate from knowledge base
    print("\nGenerating Q&A from knowledge base...")

    if "professional_roles" in knowledge:
        roles_qa = generate_professional_roles_qa(knowledge["professional_roles"])
        print(f"  Professional Roles: {len(roles_qa)} pairs")
        all_qa.extend(roles_qa)

    if "certifications" in knowledge:
        cert_qa = generate_certifications_qa(knowledge["certifications"])
        print(f"  Certifications: {len(cert_qa)} pairs")
        all_qa.extend(cert_qa)

    if "estate_planning" in knowledge:
        estate_qa = generate_estate_planning_qa(knowledge["estate_planning"])
        print(f"  Estate Planning: {len(estate_qa)} pairs")
        all_qa.extend(estate_qa)

    trust_qa = generate_trust_administration_qa({})
    print(f"  Trust Administration: {len(trust_qa)} pairs")
    all_qa.extend(trust_qa)

    # Generate synthetic Q&A
    print("\nGenerating synthetic Q&A pairs...")

    retirement_qa = generate_retirement_qa({})
    print(f"  Retirement Planning: {len(retirement_qa)} pairs")
    all_qa.extend(retirement_qa)

    tax_qa = generate_tax_planning_qa()
    print(f"  Tax Planning: {len(tax_qa)} pairs")
    all_qa.extend(tax_qa)

    college_qa = generate_college_planning_qa({})
    print(f"  College Planning: {len(college_qa)} pairs")
    all_qa.extend(college_qa)

    investment_qa = generate_investment_qa()
    print(f"  Investment: {len(investment_qa)} pairs")
    all_qa.extend(investment_qa)

    literacy_qa = generate_financial_literacy_qa()
    print(f"  Financial Literacy: {len(literacy_qa)} pairs")
    all_qa.extend(literacy_qa)

    succession_qa = generate_succession_qa()
    print(f"  Succession Planning: {len(succession_qa)} pairs")
    all_qa.extend(succession_qa)

    compliance_qa = generate_compliance_qa()
    print(f"  Compliance: {len(compliance_qa)} pairs")
    all_qa.extend(compliance_qa)

    goal_qa = generate_goal_planning_qa()
    print(f"  Goal Planning: {len(goal_qa)} pairs")
    all_qa.extend(goal_qa)

    credit_qa = generate_credit_financing_qa()
    print(f"  Credit & Financing: {len(credit_qa)} pairs")
    all_qa.extend(credit_qa)

    # Generate special examples
    print("\nGenerating special examples...")

    multi_turn = generate_multi_turn_conversations()
    print(f"  Multi-turn Conversations: {len(multi_turn)} pairs")
    all_qa.extend(multi_turn)

    negative = generate_negative_examples()
    print(f"  Negative Examples: {len(negative)} pairs")
    all_qa.extend(negative)

    edge_cases = generate_edge_cases()
    print(f"  Edge Cases: {len(edge_cases)} pairs")
    all_qa.extend(edge_cases)

    personas = generate_persona_qa()
    print(f"  Client Personas: {len(personas)} pairs")
    all_qa.extend(personas)

    # Shuffle and split
    random.shuffle(all_qa)

    # Category distribution
    print("\n" + "=" * 70)
    print("Category Distribution:")
    print("=" * 70)
    categories = {}
    for qa in all_qa:
        cat = qa.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = count / len(all_qa) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    # Split: 80% train, 10% val, 10% test
    n = len(all_qa)
    train_n = int(n * 0.8)
    val_n = int(n * 0.1)

    train_data = all_qa[:train_n]
    val_data = all_qa[train_n:train_n + val_n]
    test_data = all_qa[train_n + val_n:]

    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    train_file = OUTPUT_DIR / f"train_v3_{timestamp}.json"
    val_file = OUTPUT_DIR / f"val_v3_{timestamp}.json"
    test_file = OUTPUT_DIR / f"test_v3_{timestamp}.json"
    complete_file = OUTPUT_DIR / "training_data_v3_complete.json"

    with open(train_file, "w") as f:
        json.dump(train_data, f, indent=2)
    print(f"\nSaved: {train_file} ({len(train_data)} pairs)")

    with open(val_file, "w") as f:
        json.dump(val_data, f, indent=2)
    print(f"Saved: {val_file} ({len(val_data)} pairs)")

    with open(test_file, "w") as f:
        json.dump(test_data, f, indent=2)
    print(f"Saved: {test_file} ({len(test_data)} pairs)")

    with open(complete_file, "w") as f:
        json.dump(all_qa, f, indent=2)
    print(f"Saved: {complete_file} ({len(all_qa)} pairs)")

    print("\n" + "=" * 70)
    print(f"TOTAL Q&A PAIRS GENERATED: {len(all_qa)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
