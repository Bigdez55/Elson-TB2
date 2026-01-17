#!/usr/bin/env python3
"""Expand training data to 2000+ pairs with balanced distribution."""

import json
import random
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent.parent / "training_data"

DISCLAIMERS = [
    "\n\n*This is general educational information. Consult a qualified professional.*",
    "\n\n*Individual circumstances vary. Consult a licensed professional.*",
    "\n\n*For educational purposes only. Not financial, legal, or tax advice.*",
]

# Additional Q&A pairs to balance distribution
ADDITIONAL_QA = {
    "estate_planning": [
        ("What is a pour-over will?", "A pour-over will directs any assets not already in your trust to 'pour over' into it at death. It catches assets you forgot to retitle. These assets still go through probate, so the trust should be the primary vehicle."),
        ("What is a GRAT?", "A Grantor Retained Annuity Trust (GRAT) transfers appreciation to heirs tax-free. You put assets in, receive annuity payments back, and any growth above the IRS rate passes to beneficiaries with no gift tax."),
        ("What is an ILIT?", "An Irrevocable Life Insurance Trust (ILIT) keeps life insurance proceeds out of your estate. The trust owns the policy, pays premiums from gifts, and distributes death benefit to beneficiaries tax-free."),
        ("What is a SLAT?", "A Spousal Lifetime Access Trust (SLAT) removes assets from your estate while your spouse can still access them. One spouse is the grantor, the other a beneficiary. Popular for using lifetime exemption."),
        ("What powers of attorney do I need?", "Two types: 1) Durable Financial POA - handles banking, investments, property, bills if incapacitated. 2) Healthcare POA - makes medical decisions. Both should be 'durable' (continue through incapacity). Choose trusted agents."),
        ("What is a living will vs healthcare proxy?", "Living will states your wishes for end-of-life care (life support, feeding tubes). Healthcare proxy names someone to make medical decisions. Most people need both - your wishes documented plus someone to implement them."),
        ("What is probate?", "Probate is the court process of validating a will and distributing assets. Takes 6-24 months, costs 2-7% of estate, and is public record. Avoid with: trusts, beneficiary designations, joint ownership."),
        ("How do I fund a living trust?", "Retitle assets to the trust: real estate via new deed, bank accounts by changing ownership, brokerage accounts via transfer form. Retirement accounts name trust as beneficiary (has tax implications - consult advisor)."),
        ("What is a charitable remainder trust?", "A CRT pays you income for life, then remainder goes to charity. Benefits: income tax deduction now, capital gains avoidance, income stream, charity support. Good for appreciated assets you want to diversify."),
        ("What is the annual gift exclusion?", "In 2024, you can give $18,000 per person per year with no gift tax or reporting. Married couples can give $36,000 jointly. Gifts above this use your lifetime exemption ($13.61M)."),
    ],
    "trust_administration": [
        ("What is trust decanting?", "Decanting pours assets from one trust into a new trust with different terms. Used to fix outdated trusts, add flexibility, or extend duration. State laws vary - consult attorney."),
        ("What is a trust situs?", "Trust situs is the state governing the trust. Changing situs can provide better asset protection, tax benefits, or trust laws. Many families move trusts to Delaware, Nevada, or South Dakota."),
        ("What is a directed trust?", "A directed trust separates trustee duties: one entity handles investments, another handles distributions, another handles administration. Provides specialized expertise for each function."),
        ("What are trustee removal provisions?", "These allow beneficiaries or trust protector to remove a trustee without court involvement. Important for family flexibility - trustees can become unresponsive or have conflicts."),
        ("What is a dynasty trust?", "A dynasty trust lasts for multiple generations (perpetually in some states), keeping assets out of estate taxes at each generational transfer. Uses GST exemption."),
        ("What are Crummey powers?", "Crummey powers give beneficiaries temporary right to withdraw gifts to a trust, qualifying them for annual gift exclusion. Typically 30 days. Used in ILITs."),
        ("What is a QTIP trust?", "Qualified Terminable Interest Property trust provides income to surviving spouse, then passes to your chosen beneficiaries (often children from prior marriage). Controls ultimate distribution."),
        ("What is a special needs trust?", "SNT holds assets for a disabled beneficiary without disqualifying them from Medicaid or SSI. Third-party SNT (from family gifts) vs first-party (beneficiary's own assets)."),
    ],
    "tax_planning": [
        ("What is the kiddie tax?", "Unearned income above $2,500 (2024) for children under 19 (or 24 if student) is taxed at parent's rate. Limits benefits of shifting investments to children."),
        ("What is NIIT?", "Net Investment Income Tax is 3.8% on investment income (interest, dividends, capital gains) for individuals over $200K ($250K married). Applies on top of regular tax."),
        ("What is AMT?", "Alternative Minimum Tax is a parallel tax system that disallows certain deductions. Calculate tax both ways, pay the higher. Affects those with high state taxes, ISOs, or certain deductions."),
        ("What is Section 1031 exchange?", "Like-kind exchange defers capital gains when selling investment real estate and buying replacement property. Rules: identify replacement in 45 days, close in 180 days, similar or greater value."),
        ("What is QSBS exclusion?", "Qualified Small Business Stock exclusion lets you exclude up to $10M (or 10x basis) in gains from federal tax if you held C-corp stock 5+ years. Huge benefit for startup founders."),
        ("What is the wash sale rule?", "You can't deduct a loss if you buy same or substantially identical security within 30 days before or after the sale. Loss is added to cost basis of new shares."),
        ("What is a backdoor Roth?", "Contribute to non-deductible Traditional IRA, then convert to Roth. Bypasses Roth income limits. Must have no other Traditional IRA balances (pro-rata rule). $7K/year limit."),
        ("What is mega backdoor Roth?", "Contribute after-tax to 401k above the $23K limit (up to $69K total), then convert to Roth. Requires plan to allow after-tax contributions and in-service withdrawals."),
        ("What is tax alpha?", "Tax alpha is the extra return from tax-efficient investing strategies: asset location, tax-loss harvesting, holding period management. Can add 0.5-1%+ annually."),
        ("What is a QLAC?", "Qualified Longevity Annuity Contract lets you use up to $200K of retirement funds for a deferred annuity starting as late as 85. Reduces RMDs and provides longevity protection."),
    ],
    "investment": [
        ("What is factor investing?", "Factor investing targets specific return drivers: value, momentum, size, quality, low volatility. Factor ETFs provide exposure. Combine for diversification - factors perform differently over time."),
        ("What is direct indexing?", "Direct indexing owns individual stocks instead of ETFs, enabling personalized tax-loss harvesting, ESG customization, and avoiding concentrated positions. Usually requires $100K+ minimum."),
        ("What is sequence of returns risk?", "Poor returns early in retirement hurt more than later. A 20% drop in year 1 is worse than year 10 because you're withdrawing from a depleted base. Mitigate with bond tent or guardrails."),
        ("What is a bond ladder?", "A bond ladder staggers maturity dates (1-10 years). As each bond matures, reinvest in longest rung. Provides liquidity, reduces interest rate risk, and matches cash flows."),
        ("What are I-bonds?", "Series I savings bonds pay inflation rate plus fixed rate, currently ~5%. $10K annual limit per person. Tax-deferred, state tax-free. Good for emergency fund or short-term savings."),
        ("What is tax-loss harvesting?", "Sell investments at a loss to offset gains. Losses offset gains dollar-for-dollar, then up to $3K ordinary income. Excess carries forward. Mind wash sale rule - wait 31 days."),
        ("What is the 4% rule?", "Withdraw 4% of portfolio in year 1, adjust for inflation thereafter. Based on 30-year retirement with 50/50 stocks/bonds. More conservative: 3-3.5%. More aggressive if flexible."),
        ("What is a target date fund?", "TDFs automatically shift from stocks to bonds as you approach retirement. Choose the year closest to when you'll retire. Set-it-and-forget-it option. Check the 'glide path' - varies by provider."),
        ("What is dollar cost averaging?", "DCA invests fixed amounts at regular intervals regardless of price. Reduces timing risk but mathematically, lump sum beats DCA 2/3 of time. DCA is behavioral - helps you invest instead of waiting."),
        ("What are REITs?", "Real Estate Investment Trusts own income-producing real estate. Required to pay 90% of income as dividends. Types: equity (own property), mortgage (own loans), public/private. Adds diversification."),
    ],
    "financial_literacy": [
        ("What is compound interest?", "Interest earning interest. $10K at 7% for 30 years = $76K. Rule of 72: divide 72 by rate to get doubling time (72/7 = ~10 years). Start early - time matters more than amount."),
        ("What is net worth?", "Assets minus liabilities. Track monthly. Include: home equity, investments, cash, cars, retirement accounts. Subtract: mortgage, loans, credit cards. Benchmark: age x income / 10."),
        ("What is an adjustable rate mortgage?", "ARM rate changes after initial fixed period (5/1 ARM = fixed 5 years, then adjusts annually). Lower initial rate but risk of increases. Good if moving soon or expecting income growth."),
        ("What is refinancing?", "Replace existing loan with new one, usually for lower rate or different term. Costs 2-5% of loan. Rule of thumb: refinance if rate drops 0.75-1%+ and you'll stay long enough to recoup costs."),
        ("What is umbrella insurance?", "Extra liability coverage beyond home/auto limits. Protects assets from lawsuits. Typical: $1M policy costs $150-300/year. Get if: net worth > auto/home limits, own rental property, have risk factors."),
        ("What is term vs whole life insurance?", "Term: coverage for specific period (20-30 years), much cheaper, no cash value. Whole: lifetime coverage, builds cash value, expensive. Most people only need term - invest the difference."),
        ("What is disability insurance?", "Replaces income if you can't work. Short-term (employer often provides) vs long-term (usually need to buy). Own-occupation: pays if can't do YOUR job. Aim for 60% of income."),
        ("What is an HSA?", "Health Savings Account: triple tax advantage (deduction, growth, withdrawals for medical). Requires high-deductible health plan. 2024 limits: $4,150 individual, $8,300 family. Best retirement account after 65."),
        ("What is FICO score?", "Credit score from 300-850. Components: payment history (35%), amounts owed (30%), length of history (15%), new credit (10%), mix (10%). Over 740 gets best rates."),
        ("How do I negotiate a raise?", "Document accomplishments and market rate. Request meeting, present value you've added, cite market data. Ask for specific number 10-15% above target. Be prepared to hear no. Consider total comp."),
    ],
    "succession_planning": [
        ("What is a family limited partnership?", "FLP allows senior generation to transfer business/investment assets to heirs at discounted value (lack of control/marketability). Maintains control while reducing estate."),
        ("What is management buyout?", "MBO: existing management buys the company, often with private equity backing. Owner gets liquidity, management gets ownership, business continuity maintained."),
        ("What is earnout?", "Part of purchase price contingent on future performance. Bridges valuation gap between buyer and seller. Can be complex - define metrics clearly."),
        ("What is seller financing?", "Seller provides loan to buyer for part of purchase price. Benefits: higher price, interest income, installment sale tax treatment. Risks: buyer default."),
        ("What is key person insurance?", "Life/disability insurance on essential employees. Proceeds help company survive loss of critical person. Consider for founders, salespeople, technical experts."),
        ("What is a phantom stock plan?", "Employees get value of shares without actual ownership. Pays out at liquidity event or vesting. Simpler than actual equity, no dilution, still aligns incentives."),
        ("What is 409A valuation?", "IRS-required independent appraisal of private company stock for equity compensation. Must be done at least annually or after material events. Avoids tax penalties."),
        ("What is a stay bonus?", "Cash incentive for key employees to remain through ownership transition. Usually pays out at closing or after retention period. Critical for buyer confidence."),
    ],
    "compliance": [
        ("What is beneficial ownership?", "Under Corporate Transparency Act (2024), most companies must report beneficial owners (25%+ ownership or substantial control) to FinCEN. Penalties for non-compliance."),
        ("What is SOX compliance?", "Sarbanes-Oxley requires public companies to maintain internal controls over financial reporting. CEO/CFO certify accuracy. Applies after IPO."),
        ("What is Regulation D?", "SEC exemption allowing private companies to raise capital without full registration. 506(b): unlimited accredited investors, no advertising. 506(c): allows advertising, must verify accreditation."),
        ("What is accredited investor?", "$200K+ income ($300K joint) for 2 years, or $1M+ net worth excluding home, or certain professional credentials. Required for many private investments."),
        ("What is ERISA?", "Employee Retirement Income Security Act governs employer retirement plans. Requires fiduciary responsibility, disclosures, vesting schedules. 401k plans must comply."),
        ("What is PDT rule?", "Pattern Day Trader: 4+ day trades in 5 days triggers $25K minimum balance requirement in margin account. Doesn't apply to cash accounts but need settled funds."),
        ("What is wash sale rule?", "Can't claim loss if you buy substantially identical security within 30 days before or after sale. Loss is added to new cost basis. Applies across all accounts."),
        ("What is the prudent investor rule?", "Fiduciary standard for trustees: must invest with care, skill, and caution of prudent investor. Consider portfolio as a whole, diversify unless reason not to."),
    ],
    "credit_financing": [
        ("What is SBA 7(a) loan?", "Most common SBA loan: up to $5M for working capital, equipment, real estate. SBA guarantees 75-85%, reducing lender risk. Requires good credit and business plan."),
        ("What is asset-based lending?", "Loan secured by accounts receivable, inventory, or equipment. Advance rate: 70-90% of AR, 50% of inventory. Higher rates than traditional loans but more available."),
        ("What is mezzanine financing?", "Subordinated debt between senior debt and equity. Higher interest (12-20%) plus warrants. Used for growth or acquisitions when bank financing maxed."),
        ("What is venture debt?", "Debt financing for VC-backed startups, often alongside equity round. Extends runway without dilution. Usually 25-30% of equity raised."),
        ("What is DSCR for loans?", "Debt Service Coverage Ratio: Net Operating Income / Total Debt Service. Lenders want 1.25x+ for commercial loans. Higher is better."),
        ("What is personal guarantee?", "Lender requires owner to personally repay if business defaults. Standard for small business loans. Some SBA loans have partial or no guarantee options."),
        ("What is UCC filing?", "Lender files UCC-1 to claim collateral rights. Check for existing liens before borrowing - first position gets paid first in default."),
        ("What is PAYDEX score?", "Dun & Bradstreet business credit score (1-100). Based on payment history with suppliers. 80+ is excellent. Build by establishing trade lines and paying early."),
    ],
    "generational_wealth": [
        ("What is family governance?", "Structures for family decision-making: family council, constitution, policies. Prevents conflict, prepares next generation, aligns values. Critical as wealth grows."),
        ("What is the shirt-sleeves proverb?", "'Shirtsleeves to shirtsleeves in three generations' - wealth typically dissipates by third generation. Combat with: education, governance, involvement, values."),
        ("What is a family bank?", "Internal lending facility for family members. Provides capital at below-market rates for education, business, homes. Builds responsibility, keeps wealth in family."),
        ("What is a family office?", "Dedicated team managing wealthy family's financial affairs: investments, tax, estate, philanthropy, concierge. Single-family ($100M+) or multi-family ($10M+)."),
        ("What is next-gen education?", "Financial education for heirs: budgeting, investing, philanthropy, family values. Start young with allowance, grow to investment accounts, include in family meetings."),
        ("What is a family mission statement?", "Document articulating family values, purpose, and goals for wealth. Guides decisions, unites generations. Review and update periodically with family input."),
        ("What is a family council?", "Regular meetings of family members to discuss finances, governance, values. Structured agenda, professional facilitation for large families. Builds cohesion."),
        ("What is family employment policy?", "Rules for family working in family business: qualifications required, compensation standards, advancement criteria. Prevents entitlement, maintains meritocracy."),
    ],
    "goal_planning": [
        ("What is Coast FIRE?", "You've saved enough that compound growth alone will fund traditional retirement - no more contributions needed. Can reduce income/hours now. Example: $250K at 30 = $2M+ at 65."),
        ("What is Barista FIRE?", "Semi-retired, working part-time for benefits and some income while investments grow. Lower stress than full FIRE, health insurance solved."),
        ("What is Lean FIRE?", "FIRE with minimal annual spending ($40K or less). Requires frugality but achievable with lower savings. May feel restrictive for some."),
        ("What is Fat FIRE?", "FIRE with comfortable spending ($100K+/year). Requires larger portfolio ($2.5M+) but maintains lifestyle. Takes longer to achieve."),
        ("What is the money dial concept?", "Spend lavishly on what brings joy, cut ruthlessly elsewhere. Identify your 2-3 'money dials' (travel, food, housing) and optimize spending around them."),
        ("What is a wealth waterfall?", "Prioritized allocation: 1) Match (free money), 2) High-interest debt, 3) Emergency fund, 4) HSA, 5) Roth IRA, 6) Max 401k, 7) Taxable. Follow the order."),
        ("What is your savings rate?", "Percentage of income saved. 10% = retire in 50 years. 20% = 37 years. 50% = 17 years. Track gross savings rate for meaningful comparison."),
        ("What is lifestyle creep?", "Spending increases as income increases. Combat by: automating savings on raises, keeping fixed costs low, defining 'enough'. A raise doesn't require spending more."),
    ],
}


def expand_with_variations(qa_pairs: list) -> list:
    """Create variations of existing Q&A pairs."""
    expanded = list(qa_pairs)

    # Add variations for high-value categories
    for category, questions in ADDITIONAL_QA.items():
        for q, a in questions:
            expanded.append({
                "instruction": q,
                "input": "",
                "output": a + random.choice(DISCLAIMERS),
                "category": category
            })

    return expanded


def main():
    print("=" * 70)
    print("Expanding Training Data to 2000+ pairs")
    print("=" * 70)

    # Load existing data
    v1 = json.load(open(OUTPUT_DIR / "training_data_complete.json"))
    v3 = json.load(open(OUTPUT_DIR / "training_data_v3_complete.json"))

    # Combine and dedupe
    seen = set()
    combined = []
    for item in v1 + v3:
        key = item.get("instruction", "")
        if key and key not in seen:
            seen.add(key)
            combined.append(item)

    print(f"\nExisting data: {len(combined)} pairs")

    # Expand with additional content
    expanded = expand_with_variations(combined)

    # Dedupe again
    seen = set()
    final = []
    for item in expanded:
        key = item.get("instruction", "")
        if key and key not in seen:
            seen.add(key)
            final.append(item)

    print(f"After expansion: {len(final)} pairs")

    # Category distribution
    print("\n" + "=" * 70)
    print("Category Distribution:")
    print("=" * 70)
    cats = {}
    for item in final:
        cat = item.get("category", "unknown")
        cats[cat] = cats.get(cat, 0) + 1

    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        pct = count / len(final) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    # Shuffle and split
    random.shuffle(final)
    n = len(final)
    train_n = int(n * 0.8)
    val_n = int(n * 0.1)

    train = final[:train_n]
    val = final[train_n:train_n + val_n]
    test = final[train_n + val_n:]

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(OUTPUT_DIR / f"train_final_{ts}.json", "w") as f:
        json.dump(train, f, indent=2)
    print(f"\nSaved: train_final_{ts}.json ({len(train)} pairs)")

    with open(OUTPUT_DIR / f"val_final_{ts}.json", "w") as f:
        json.dump(val, f, indent=2)
    print(f"Saved: val_final_{ts}.json ({len(val)} pairs)")

    with open(OUTPUT_DIR / f"test_final_{ts}.json", "w") as f:
        json.dump(test, f, indent=2)
    print(f"Saved: test_final_{ts}.json ({len(test)} pairs)")

    with open(OUTPUT_DIR / "training_data_final.json", "w") as f:
        json.dump(final, f, indent=2)
    print(f"Saved: training_data_final.json ({len(final)} pairs)")

    print("\n" + "=" * 70)
    print(f"TOTAL Q&A PAIRS: {len(final)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
