#!/usr/bin/env python3
"""
Elson TB2 - Domain Classifier
Classifies Q&A pairs into the 62-domain taxonomy.

Features:
1. Keyword-based classification
2. Multi-domain support
3. Confidence scoring
4. Reclassification of legacy categories
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import Counter

# Complete 62-domain taxonomy
DOMAIN_TAXONOMY = {
    # TAX LAW (6)
    "federal_income_tax": {
        "keywords": ["irs", "internal revenue", "form 1040", "1099", "w-2", "federal tax", "income tax", "irc section", "tax code", "treasury regulation", "deduction", "taxable income", "adjusted gross income", "agi", "standard deduction", "itemized deduction"],
        "category": "tax_law",
        "weight": 1.0
    },
    "state_local_tax": {
        "keywords": ["salt", "state tax", "local tax", "property tax", "sales tax", "state income tax", "nexus", "apportionment", "domicile", "resident", "nonresident"],
        "category": "tax_law",
        "weight": 1.0
    },
    "international_tax": {
        "keywords": ["foreign tax credit", "transfer pricing", "fatca", "fbar", "pfic", "cfc", "gilti", "beat", "tax treaty", "withholding", "permanent establishment", "oecd", "beps", "subpart f"],
        "category": "tax_law",
        "weight": 1.2
    },
    "estate_gift_tax": {
        "keywords": ["estate tax", "gift tax", "unified credit", "annual exclusion", "marital deduction", "gst tax", "generation skipping", "portability", "bypass trust", "credit shelter", "taxable estate", "gross estate"],
        "category": "tax_law",
        "weight": 1.1
    },
    "corporate_tax": {
        "keywords": ["corporate tax", "c corporation", "subchapter c", "dividends received deduction", "consolidated return", "m-1 adjustment", "book-tax difference", "e&p", "earnings and profits", "corporate reorganization"],
        "category": "tax_law",
        "weight": 1.0
    },
    "tax_controversy": {
        "keywords": ["tax court", "irs audit", "notice of deficiency", "penalty abatement", "offer in compromise", "innocent spouse", "statute of limitations", "collection due process", "appeals", "tax litigation"],
        "category": "tax_law",
        "weight": 1.2
    },

    # ESTATE & WEALTH TRANSFER (5)
    "estate_planning": {
        "keywords": ["estate plan", "will", "trust", "beneficiary", "executor", "probate", "asset protection", "wealth transfer", "inheritance", "testamentary", "living trust", "revocable trust", "irrevocable trust"],
        "category": "estate_wealth",
        "weight": 1.0
    },
    "trust_administration": {
        "keywords": ["trust administration", "trustee", "fiduciary", "trust accounting", "distribution", "beneficiary", "trust corpus", "principal and income", "prudent investor", "trust situs"],
        "category": "estate_wealth",
        "weight": 1.0
    },
    "probate": {
        "keywords": ["probate", "intestate", "letters testamentary", "personal representative", "estate administration", "creditor claims", "probate court", "ancillary probate"],
        "category": "estate_wealth",
        "weight": 1.1
    },
    "charitable_planning": {
        "keywords": ["charitable", "philanthropy", "foundation", "donor advised fund", "daf", "charitable remainder trust", "crt", "charitable lead trust", "clt", "private foundation", "public charity", "501(c)(3)"],
        "category": "estate_wealth",
        "weight": 1.1
    },
    "gst_planning": {
        "keywords": ["generation skipping", "gst", "skip person", "dynasty trust", "gst exemption", "taxable distribution", "taxable termination", "direct skip"],
        "category": "estate_wealth",
        "weight": 1.2
    },

    # INSURANCE (8)
    "life_insurance": {
        "keywords": ["life insurance", "death benefit", "cash value", "whole life", "term life", "universal life", "variable life", "premium", "underwriting", "beneficiary designation", "ilit", "irrevocable life insurance trust"],
        "category": "insurance",
        "weight": 1.0
    },
    "health_insurance": {
        "keywords": ["health insurance", "aca", "affordable care act", "medicare", "medicaid", "hmo", "ppo", "deductible", "copay", "coinsurance", "out-of-pocket maximum", "cobra", "hipaa"],
        "category": "insurance",
        "weight": 1.0
    },
    "property_insurance": {
        "keywords": ["property insurance", "homeowners", "dwelling", "personal property", "replacement cost", "actual cash value", "peril", "exclusion", "flood insurance", "earthquake"],
        "category": "insurance",
        "weight": 1.0
    },
    "casualty_insurance": {
        "keywords": ["casualty insurance", "liability", "auto insurance", "umbrella", "professional liability", "e&o", "d&o", "general liability", "workers compensation", "bodily injury"],
        "category": "insurance",
        "weight": 1.0
    },
    "reinsurance": {
        "keywords": ["reinsurance", "treaty", "facultative", "retrocession", "ceding company", "reinsurer", "quota share", "excess of loss", "catastrophe bond", "cat bond"],
        "category": "insurance",
        "weight": 1.3
    },
    "annuities": {
        "keywords": ["annuity", "annuitization", "accumulation", "payout", "fixed annuity", "variable annuity", "indexed annuity", "immediate annuity", "deferred annuity", "surrender charge", "mortality charge"],
        "category": "insurance",
        "weight": 1.0
    },
    "ltc_insurance": {
        "keywords": ["long-term care", "ltc", "nursing home", "assisted living", "home health", "benefit trigger", "elimination period", "daily benefit", "inflation protection"],
        "category": "insurance",
        "weight": 1.1
    },
    "actuarial": {
        "keywords": ["actuary", "actuarial", "mortality table", "reserving", "loss ratio", "combined ratio", "pricing", "risk assessment", "soa", "cas", "fsa", "fcas"],
        "category": "insurance",
        "weight": 1.2
    },

    # BANKING & LENDING (5)
    "commercial_banking": {
        "keywords": ["commercial bank", "commercial lending", "line of credit", "term loan", "treasury services", "cash management", "occ", "fdic", "bank examination", "capital requirements"],
        "category": "banking",
        "weight": 1.0
    },
    "consumer_lending": {
        "keywords": ["consumer lending", "personal loan", "credit card", "auto loan", "tila", "truth in lending", "reg z", "cfpb", "fair lending", "ecoa", "equal credit"],
        "category": "banking",
        "weight": 1.0
    },
    "mortgage_finance": {
        "keywords": ["mortgage", "respa", "closing costs", "origination", "servicing", "fannie mae", "freddie mac", "conforming loan", "jumbo", "fha", "va loan", "escrow"],
        "category": "banking",
        "weight": 1.0
    },
    "credit_risk": {
        "keywords": ["credit risk", "credit analysis", "default", "probability of default", "loss given default", "credit score", "fico", "credit rating", "creditworthiness", "credit spread"],
        "category": "banking",
        "weight": 1.1
    },
    "treasury_management": {
        "keywords": ["treasury", "cash management", "liquidity", "working capital", "receivables", "payables", "concentration", "disbursement", "lockbox", "sweep account"],
        "category": "banking",
        "weight": 1.1
    },

    # SECURITIES & INVESTMENTS (10)
    "equities": {
        "keywords": ["stock", "equity", "shares", "common stock", "preferred stock", "dividend", "eps", "p/e ratio", "market cap", "ipo", "secondary offering", "stock split"],
        "category": "securities",
        "weight": 0.9
    },
    "fixed_income": {
        "keywords": ["bond", "fixed income", "yield", "coupon", "maturity", "duration", "convexity", "credit spread", "treasury", "municipal bond", "corporate bond", "yield curve"],
        "category": "securities",
        "weight": 1.0
    },
    "derivatives": {
        "keywords": ["derivative", "option", "future", "forward", "swap", "strike price", "expiration", "call", "put", "delta", "gamma", "theta", "vega", "black-scholes", "greeks"],
        "category": "securities",
        "weight": 1.1
    },
    "commodities": {
        "keywords": ["commodity", "futures contract", "spot price", "contango", "backwardation", "oil", "gold", "silver", "agricultural", "energy trading", "physical delivery"],
        "category": "securities",
        "weight": 1.1
    },
    "forex": {
        "keywords": ["forex", "foreign exchange", "fx", "currency", "exchange rate", "pip", "carry trade", "currency pair", "spot rate", "forward rate"],
        "category": "securities",
        "weight": 1.1
    },
    "alternatives": {
        "keywords": ["alternative investment", "real assets", "infrastructure", "timber", "farmland", "collectibles", "art investment", "wine", "illiquid"],
        "category": "securities",
        "weight": 1.1
    },
    "private_equity": {
        "keywords": ["private equity", "lbo", "leveraged buyout", "growth equity", "buyout", "portfolio company", "carried interest", "management fee", "capital call", "distribution", "j-curve"],
        "category": "securities",
        "weight": 1.1
    },
    "venture_capital": {
        "keywords": ["venture capital", "vc", "startup", "seed", "series a", "series b", "term sheet", "valuation", "dilution", "cap table", "convertible note", "safe"],
        "category": "securities",
        "weight": 1.1
    },
    "hedge_funds": {
        "keywords": ["hedge fund", "long/short", "market neutral", "global macro", "event driven", "arbitrage", "prime broker", "fund of funds", "2 and 20", "high water mark"],
        "category": "securities",
        "weight": 1.1
    },
    "cryptocurrency": {
        "keywords": ["cryptocurrency", "bitcoin", "ethereum", "blockchain", "defi", "nft", "wallet", "exchange", "mining", "staking", "smart contract", "token"],
        "category": "securities",
        "weight": 1.0
    },

    # PORTFOLIO & ASSET MANAGEMENT (5)
    "portfolio_construction": {
        "keywords": ["portfolio", "diversification", "asset allocation", "modern portfolio theory", "efficient frontier", "sharpe ratio", "optimization", "rebalancing", "correlation"],
        "category": "portfolio",
        "weight": 1.0
    },
    "risk_management": {
        "keywords": ["risk management", "var", "value at risk", "stress test", "scenario analysis", "monte carlo", "risk metrics", "tail risk", "drawdown", "volatility"],
        "category": "portfolio",
        "weight": 1.0
    },
    "asset_allocation": {
        "keywords": ["asset allocation", "strategic allocation", "tactical allocation", "liability driven", "glide path", "target date", "risk parity", "factor exposure"],
        "category": "portfolio",
        "weight": 1.0
    },
    "performance_attribution": {
        "keywords": ["performance attribution", "brinson", "factor attribution", "benchmark", "alpha", "tracking error", "information ratio", "active return", "return decomposition"],
        "category": "portfolio",
        "weight": 1.2
    },
    "factor_investing": {
        "keywords": ["factor investing", "smart beta", "momentum", "value factor", "quality factor", "size factor", "low volatility", "factor exposure", "factor premium"],
        "category": "portfolio",
        "weight": 1.1
    },

    # QUANTITATIVE & TRADING (5)
    "quantitative_finance": {
        "keywords": ["quantitative", "quant", "stochastic calculus", "ito", "brownian motion", "monte carlo", "numerical methods", "pde", "mathematical finance"],
        "category": "quantitative",
        "weight": 1.1
    },
    "algorithmic_trading": {
        "keywords": ["algorithmic trading", "algo", "systematic", "backtesting", "signal", "execution algorithm", "trading strategy", "automated trading"],
        "category": "quantitative",
        "weight": 1.1
    },
    "hft": {
        "keywords": ["high frequency", "hft", "latency", "colocation", "market making", "nanosecond", "microsecond", "fpga", "order flow"],
        "category": "quantitative",
        "weight": 1.3
    },
    "market_microstructure": {
        "keywords": ["microstructure", "order book", "bid-ask", "spread", "liquidity", "price discovery", "market impact", "tick size", "dark pool"],
        "category": "quantitative",
        "weight": 1.2
    },
    "trade_execution": {
        "keywords": ["execution", "vwap", "twap", "implementation shortfall", "transaction cost", "slippage", "best execution", "order routing"],
        "category": "quantitative",
        "weight": 1.1
    },

    # CORPORATE FINANCE (4)
    "mergers_acquisitions": {
        "keywords": ["m&a", "merger", "acquisition", "due diligence", "synergy", "deal structure", "earnout", "closing", "integration", "hostile takeover", "friendly acquisition"],
        "category": "corporate",
        "weight": 1.0
    },
    "business_valuation": {
        "keywords": ["valuation", "dcf", "discounted cash flow", "multiples", "comparable", "enterprise value", "equity value", "wacc", "terminal value", "fair market value"],
        "category": "corporate",
        "weight": 1.0
    },
    "restructuring": {
        "keywords": ["restructuring", "bankruptcy", "chapter 11", "chapter 7", "workout", "distressed", "creditor", "debtor in possession", "reorganization plan"],
        "category": "corporate",
        "weight": 1.1
    },
    "capital_markets": {
        "keywords": ["capital markets", "ipo", "underwriting", "syndicate", "book building", "road show", "debt issuance", "equity offering", "secondary offering"],
        "category": "corporate",
        "weight": 1.0
    },

    # REGULATORY & COMPLIANCE (6)
    "securities_regulation": {
        "keywords": ["sec", "securities act", "exchange act", "reg d", "reg a", "blue sky", "finra", "broker-dealer", "investment adviser", "form adv", "reg bi"],
        "category": "regulatory",
        "weight": 1.0
    },
    "banking_regulation": {
        "keywords": ["banking regulation", "occ", "federal reserve", "fdic", "basel", "capital requirement", "stress test", "ccar", "dodd-frank", "volcker rule"],
        "category": "regulatory",
        "weight": 1.0
    },
    "insurance_regulation": {
        "keywords": ["insurance regulation", "naic", "state insurance", "solvency", "admitted", "surplus lines", "rate filing", "policy form", "market conduct"],
        "category": "regulatory",
        "weight": 1.0
    },
    "aml_kyc": {
        "keywords": ["aml", "anti-money laundering", "kyc", "know your customer", "bsa", "bank secrecy", "ctr", "sar", "suspicious activity", "fincen", "ofac", "cip"],
        "category": "regulatory",
        "weight": 1.1
    },
    "erisa_benefits": {
        "keywords": ["erisa", "employee benefits", "qualified plan", "401k", "pension", "defined benefit", "defined contribution", "fiduciary", "prohibited transaction", "dol"],
        "category": "regulatory",
        "weight": 1.0
    },
    "data_privacy": {
        "keywords": ["gdpr", "ccpa", "privacy", "data protection", "personal data", "consent", "breach notification", "data subject", "right to erasure"],
        "category": "regulatory",
        "weight": 1.1
    },

    # OPERATIONS & INFRASTRUCTURE (4)
    "prime_brokerage": {
        "keywords": ["prime broker", "prime brokerage", "margin", "securities lending", "short selling", "rehypothecation", "custody", "clearing"],
        "category": "operations",
        "weight": 1.2
    },
    "custodial": {
        "keywords": ["custodian", "custody", "safekeeping", "settlement", "corporate actions", "proxy", "asset servicing"],
        "category": "operations",
        "weight": 1.1
    },
    "fund_administration": {
        "keywords": ["fund administration", "nav", "net asset value", "investor services", "transfer agent", "fund accounting", "shareholder services"],
        "category": "operations",
        "weight": 1.1
    },
    "fintech": {
        "keywords": ["fintech", "financial technology", "payment", "regtech", "insurtech", "robo-advisor", "neobank", "digital banking", "api banking"],
        "category": "operations",
        "weight": 1.0
    },

    # PLANNING & ADVISORY (4)
    "financial_planning": {
        "keywords": ["financial planning", "cfp", "comprehensive plan", "financial goals", "budget", "cash flow", "net worth", "financial statement"],
        "category": "planning",
        "weight": 0.9
    },
    "retirement_planning": {
        "keywords": ["retirement", "401k", "ira", "roth", "rmd", "required minimum distribution", "social security", "pension", "annuity", "retirement income", "sequence of returns"],
        "category": "planning",
        "weight": 1.0
    },
    "college_planning": {
        "keywords": ["college planning", "529", "education savings", "fafsa", "financial aid", "tuition", "scholarship", "coverdell", "education ira"],
        "category": "planning",
        "weight": 1.0
    },
    "family_office": {
        "keywords": ["family office", "sfo", "mfo", "family governance", "investment policy", "family meeting", "next generation", "family wealth", "family council"],
        "category": "planning",
        "weight": 1.1
    }
}

# Legacy category mappings
LEGACY_MAPPINGS = {
    "general_finance": "financial_planning",
    "tax": "federal_income_tax",
    "fiduciary": "trust_administration",
    "compliance": "securities_regulation",
    "investment_strategy": "portfolio_construction",
    "high_frequency_trading": "hft",
    "data_engineering": "fintech",
    "ai_ml": "fintech",
    "infrastructure": "fintech",
    "professional_roles": "financial_planning",
    "goal_planning": "financial_planning",
    "generational_wealth": "estate_planning",
    "succession_planning": "estate_planning",
    "markets": "equities",
    "banking": "commercial_banking",
    "insurance": "life_insurance"
}


def classify_text(text: str) -> Tuple[str, float, List[str]]:
    """
    Classify text into a domain from the 62-domain taxonomy.

    Returns:
        Tuple of (primary_domain, confidence_score, all_matched_domains)
    """
    text_lower = text.lower()
    domain_scores = {}

    for domain, config in DOMAIN_TAXONOMY.items():
        keywords = config["keywords"]
        weight = config["weight"]

        # Count keyword matches
        matches = 0
        for keyword in keywords:
            if keyword in text_lower:
                matches += 1
                # Bonus for exact word match (not part of larger word)
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    matches += 0.5

        if matches > 0:
            # Score = matches * weight, normalized by keyword count
            score = (matches / len(keywords)) * weight * 100
            domain_scores[domain] = score

    if not domain_scores:
        return "financial_planning", 0.1, []

    # Sort by score
    sorted_domains = sorted(domain_scores.items(), key=lambda x: -x[1])
    primary_domain = sorted_domains[0][0]
    confidence = min(sorted_domains[0][1] / 100, 1.0)

    # Return domains with significant scores (>50% of primary)
    threshold = sorted_domains[0][1] * 0.5
    matched_domains = [d for d, s in sorted_domains if s >= threshold]

    return primary_domain, confidence, matched_domains


def classify_qa_pair(pair: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a single Q&A pair."""
    # Combine instruction and output for classification
    text = pair.get("instruction", "") + " " + pair.get("output", "")

    primary_domain, confidence, matched_domains = classify_text(text)

    # Check if current category is a legacy category
    current_category = pair.get("category", "")
    if current_category in LEGACY_MAPPINGS:
        # Use legacy mapping if no strong classification
        if confidence < 0.3:
            primary_domain = LEGACY_MAPPINGS[current_category]

    # Update pair with classification
    classified_pair = pair.copy()
    classified_pair["category"] = primary_domain
    classified_pair["domain_confidence"] = round(confidence, 3)
    classified_pair["related_domains"] = matched_domains[:3]  # Top 3 related
    classified_pair["original_category"] = current_category

    return classified_pair


def classify_training_data(
    input_path: str,
    output_path: str,
    min_confidence: float = 0.0
) -> Dict[str, Any]:
    """
    Classify all Q&A pairs in a training data file.

    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
        min_confidence: Minimum confidence threshold (pairs below this are flagged)

    Returns:
        Classification statistics
    """
    print(f"Loading training data from {input_path}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded {len(data)} Q&A pairs")
    print("Classifying into 62-domain taxonomy...")

    classified_data = []
    domain_counts = Counter()
    category_counts = Counter()
    low_confidence = []
    reclassified = []

    for i, pair in enumerate(data):
        classified = classify_qa_pair(pair)
        classified_data.append(classified)

        domain = classified["category"]
        domain_counts[domain] += 1
        category_counts[DOMAIN_TAXONOMY.get(domain, {}).get("category", "unknown")] += 1

        if classified["domain_confidence"] < min_confidence:
            low_confidence.append({
                "index": i,
                "instruction": pair.get("instruction", "")[:100],
                "confidence": classified["domain_confidence"],
                "domain": domain
            })

        if classified["original_category"] != domain:
            reclassified.append({
                "index": i,
                "from": classified["original_category"],
                "to": domain,
                "confidence": classified["domain_confidence"]
            })

        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(data)} pairs...")

    # Save classified data
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(classified_data, f, indent=2, ensure_ascii=False)
    print(f"\nClassified data saved to: {output_path}")

    # Also save JSONL
    jsonl_path = str(output_path).replace('.json', '.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for pair in classified_data:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')

    # Calculate statistics
    stats = {
        "timestamp": datetime.now().isoformat(),
        "total_pairs": len(data),
        "domains_used": len(domain_counts),
        "domain_distribution": dict(domain_counts.most_common()),
        "category_distribution": dict(category_counts.most_common()),
        "reclassified_count": len(reclassified),
        "low_confidence_count": len(low_confidence),
        "avg_confidence": sum(p["domain_confidence"] for p in classified_data) / len(classified_data) if classified_data else 0,
        "reclassified_samples": reclassified[:20],
        "low_confidence_samples": low_confidence[:20]
    }

    # Save statistics
    stats_path = str(output_path).replace('.json', '_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_path}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Classify Elson TB2 training data into 62 domains")
    parser.add_argument("--input", "-i",
                        default="backend/training_data/final_training_data.json",
                        help="Input training data JSON file")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/classified_training_data.json",
                        help="Output classified JSON file")
    parser.add_argument("--min-confidence", type=float, default=0.2,
                        help="Minimum confidence threshold for flagging")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Only analyze without saving")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    input_path = project_root / args.input
    output_path = project_root / args.output

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    stats = classify_training_data(
        str(input_path),
        str(output_path),
        min_confidence=args.min_confidence
    )

    # Print summary
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total pairs: {stats['total_pairs']}")
    print(f"Domains used: {stats['domains_used']}/62")
    print(f"Average confidence: {stats['avg_confidence']:.1%}")
    print(f"Reclassified: {stats['reclassified_count']}")
    print(f"Low confidence: {stats['low_confidence_count']}")
    print("\nTop 10 domains:")
    for domain, count in list(stats['domain_distribution'].items())[:10]:
        pct = count / stats['total_pairs'] * 100
        print(f"  {domain}: {count} ({pct:.1f}%)")
    print("\nCategory distribution:")
    for cat, count in stats['category_distribution'].items():
        pct = count / stats['total_pairs'] * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
