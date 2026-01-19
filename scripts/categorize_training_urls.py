#!/usr/bin/env python3
"""
Elson TB2 - URL Categorization Script

Categorizes the 830+ uncategorized URLs in master_training_resources_v5.csv
using pattern matching and domain analysis based on expansion_pack_v4.csv schema.

Usage:
    python scripts/categorize_training_urls.py
"""

import csv
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

# Domain to category mapping based on expansion_pack schema
DOMAIN_MAPPINGS: Dict[str, Dict[str, str]] = {
    # Tax domains
    "irs.gov": {"domain": "Tax", "subdomain": "Federal", "authority_tier": "primary"},
    "treasury.gov": {"domain": "Tax", "subdomain": "Federal", "authority_tier": "primary"},
    "taxadmin.org": {"domain": "Tax", "subdomain": "State", "authority_tier": "primary"},
    "calbar.ca.gov": {"domain": "Tax", "subdomain": "State", "authority_tier": "primary"},
    "mtc.gov": {"domain": "Tax", "subdomain": "State", "authority_tier": "secondary"},
    "uscode.house.gov": {"domain": "Tax", "subdomain": "Federal", "authority_tier": "primary"},
    "ecfr.gov": {"domain": "Tax", "subdomain": "Federal", "authority_tier": "primary"},
    "govinfo.gov": {"domain": "Tax", "subdomain": "Federal", "authority_tier": "primary"},

    # Markets / Securities
    "sec.gov": {"domain": "Markets", "subdomain": "Federal", "authority_tier": "primary"},
    "finra.org": {"domain": "Markets", "subdomain": "Federal", "authority_tier": "primary"},
    "cftc.gov": {"domain": "Compliance", "subdomain": "Federal", "authority_tier": "primary"},
    "nyse.com": {"domain": "Markets", "subdomain": "Exchange", "authority_tier": "secondary"},
    "nasdaq.com": {"domain": "Markets", "subdomain": "Exchange", "authority_tier": "secondary"},
    "cboe.com": {"domain": "Markets", "subdomain": "Exchange", "authority_tier": "secondary"},
    "cmegroup.com": {"domain": "Markets", "subdomain": "Derivatives", "authority_tier": "secondary"},
    "theocc.com": {"domain": "Markets", "subdomain": "Derivatives", "authority_tier": "secondary"},
    "msrb.org": {"domain": "Markets", "subdomain": "Federal", "authority_tier": "primary"},
    "sipc.org": {"domain": "Markets", "subdomain": "Investor Protection", "authority_tier": "primary"},
    "dtcclearning.com": {"domain": "Markets", "subdomain": "Infrastructure", "authority_tier": "secondary"},
    "sifma.org": {"domain": "Markets", "subdomain": "Industry", "authority_tier": "secondary"},

    # Banking
    "fdic.gov": {"domain": "Banking", "subdomain": "Federal", "authority_tier": "primary"},
    "occ.treas.gov": {"domain": "Banking", "subdomain": "Federal", "authority_tier": "primary"},
    "ncua.gov": {"domain": "Banking", "subdomain": "Federal", "authority_tier": "primary"},
    "federalreserve.gov": {"domain": "Banking", "subdomain": "Federal", "authority_tier": "primary"},
    "csbs.org": {"domain": "Banking", "subdomain": "State", "authority_tier": "primary"},
    "bankofamerica.com": {"domain": "Banking", "subdomain": "Commercial", "authority_tier": "tertiary"},
    "dcuc.org": {"domain": "Banking", "subdomain": "Credit Unions", "authority_tier": "secondary"},

    # Compliance / AML
    "fincen.gov": {"domain": "Compliance", "subdomain": "AML", "authority_tier": "primary"},
    "ofac.treasury.gov": {"domain": "Compliance", "subdomain": "Sanctions", "authority_tier": "primary"},
    "bsaaml.ffiec.gov": {"domain": "Compliance", "subdomain": "AML", "authority_tier": "primary"},
    "fatf-gafi.org": {"domain": "Compliance", "subdomain": "Global AML", "authority_tier": "primary"},
    "bis.org": {"domain": "Banking", "subdomain": "Global", "authority_tier": "primary"},

    # Credit / Consumer
    "consumerfinance.gov": {"domain": "Credit", "subdomain": "Consumer", "authority_tier": "primary"},
    "experian.com": {"domain": "Credit", "subdomain": "Consumer", "authority_tier": "secondary"},

    # Insurance
    "naic.org": {"domain": "Insurance", "subdomain": "Regulatory", "authority_tier": "primary"},
    "medicare.gov": {"domain": "Insurance", "subdomain": "Health", "authority_tier": "primary"},
    "medicaid.gov": {"domain": "Insurance", "subdomain": "Health", "authority_tier": "primary"},
    "ssa.gov": {"domain": "Insurance", "subdomain": "Retirement", "authority_tier": "primary"},
    "calpers.ca.gov": {"domain": "Retirement", "subdomain": "State", "authority_tier": "primary"},

    # Retirement / ERISA
    "dol.gov": {"domain": "Retirement", "subdomain": "Federal", "authority_tier": "primary"},

    # Standards / Accounting
    "asc.fasb.org": {"domain": "Standards", "subdomain": "Accounting", "authority_tier": "primary"},
    "ifrs.org": {"domain": "Standards", "subdomain": "Accounting", "authority_tier": "primary"},
    "coso.org": {"domain": "Standards", "subdomain": "Risk", "authority_tier": "secondary"},
    "nist.gov": {"domain": "Standards", "subdomain": "Security", "authority_tier": "primary"},
    "iso.org": {"domain": "Standards", "subdomain": "Global", "authority_tier": "secondary"},
    "iso20022.org": {"domain": "Standards", "subdomain": "Payments", "authority_tier": "secondary"},
    "pcisecuritystandards.org": {"domain": "Standards", "subdomain": "Payments", "authority_tier": "secondary"},
    "xbrl.us": {"domain": "Data", "subdomain": "Accounting", "authority_tier": "secondary"},

    # Credentials / Education
    "cfainstitute.org": {"domain": "Credentials", "subdomain": "Investing", "authority_tier": "secondary"},
    "cfp.net": {"domain": "Credentials", "subdomain": "Wealth", "authority_tier": "secondary"},
    "aicpa.org": {"domain": "Credentials", "subdomain": "Accounting", "authority_tier": "secondary"},
    "garp.org": {"domain": "Credentials", "subdomain": "Risk", "authority_tier": "secondary"},
    "theinstitutes.org": {"domain": "Credentials", "subdomain": "Insurance", "authority_tier": "secondary"},
    "barbri.com": {"domain": "Credentials", "subdomain": "Legal", "authority_tier": "tertiary"},
    "cfaebooks.com": {"domain": "Credentials", "subdomain": "Investing", "authority_tier": "tertiary"},
    "coursera.org": {"domain": "Credentials", "subdomain": "Education", "authority_tier": "tertiary"},
    "nfa.futures.org": {"domain": "Credentials", "subdomain": "Derivatives", "authority_tier": "secondary"},

    # Economic Data
    "fred.stlouisfed.org": {"domain": "Data", "subdomain": "Economics", "authority_tier": "primary"},
    "bls.gov": {"domain": "Data", "subdomain": "Labor", "authority_tier": "primary"},

    # Estate / Wealth / Family Office
    "appraisers.org": {"domain": "Estate", "subdomain": "Valuation", "authority_tier": "secondary"},
    "elderlaw": {"domain": "Estate", "subdomain": "Elder Law", "authority_tier": "secondary"},
    "unclaimed.org": {"domain": "Wealth", "subdomain": "State", "authority_tier": "primary"},

    # Business / Consulting
    "bain.com": {"domain": "Business", "subdomain": "Consulting", "authority_tier": "tertiary"},
    "ey.com": {"domain": "Business", "subdomain": "Consulting", "authority_tier": "tertiary"},
    "forbes.com": {"domain": "Business", "subdomain": "Media", "authority_tier": "tertiary"},
    "franklincovey.com": {"domain": "Business", "subdomain": "Training", "authority_tier": "tertiary"},

    # Legal
    "duanemorris.com": {"domain": "Legal", "subdomain": "Securities", "authority_tier": "tertiary"},
    "carltonfields.com": {"domain": "Legal", "subdomain": "Tax", "authority_tier": "tertiary"},
    "hklaw.com": {"domain": "Legal", "subdomain": "General", "authority_tier": "tertiary"},
    "foxrothschild.com": {"domain": "Legal", "subdomain": "Wealth", "authority_tier": "tertiary"},

    # Technology / Security
    "cyberarrow.io": {"domain": "Technology", "subdomain": "Security", "authority_tier": "tertiary"},
    "darktrace.com": {"domain": "Technology", "subdomain": "Security", "authority_tier": "tertiary"},
    "atlassystems.com": {"domain": "Technology", "subdomain": "Security", "authority_tier": "tertiary"},
    "ic3.gov": {"domain": "Technology", "subdomain": "Security", "authority_tier": "primary"},

    # Academic / Research
    "cambridge.org": {"domain": "Research", "subdomain": "Academic", "authority_tier": "secondary"},
    "emerald.com": {"domain": "Research", "subdomain": "Academic", "authority_tier": "secondary"},
    "frontiersin.org": {"domain": "Research", "subdomain": "Academic", "authority_tier": "secondary"},
    "aclweb.org": {"domain": "Research", "subdomain": "NLP/ML", "authority_tier": "secondary"},
    "hrpub.org": {"domain": "Research", "subdomain": "Academic", "authority_tier": "tertiary"},
    "ijfmr.com": {"domain": "Research", "subdomain": "Academic", "authority_tier": "tertiary"},
}

# Keyword-based categorization for domains not in mapping
KEYWORD_PATTERNS: List[Tuple[str, Dict[str, str]]] = [
    # Tax patterns
    (r"(tax|irs|revenue|income)", {"domain": "Tax", "subdomain": "General", "authority_tier": "secondary"}),

    # Investment / Trading patterns
    (r"(invest|trading|broker|stock|equity|portfolio)", {"domain": "Markets", "subdomain": "Investing", "authority_tier": "tertiary"}),
    (r"(hedge.fund|private.equity|venture)", {"domain": "Markets", "subdomain": "Private", "authority_tier": "tertiary"}),

    # Banking patterns
    (r"(bank|lend|loan|credit.union)", {"domain": "Banking", "subdomain": "General", "authority_tier": "tertiary"}),

    # Estate / Wealth patterns
    (r"(estate|trust|probate|will|inheritance)", {"domain": "Estate", "subdomain": "Planning", "authority_tier": "tertiary"}),
    (r"(wealth|family.office|uhnw|hnw)", {"domain": "Wealth", "subdomain": "Management", "authority_tier": "tertiary"}),
    (r"(elder|medi-cal|medicaid|senior)", {"domain": "Estate", "subdomain": "Elder Law", "authority_tier": "tertiary"}),

    # Insurance patterns
    (r"(insurance|annuity|life.insurance|health.insurance)", {"domain": "Insurance", "subdomain": "General", "authority_tier": "tertiary"}),

    # Retirement patterns
    (r"(retirement|401k|ira|pension|erisa)", {"domain": "Retirement", "subdomain": "Planning", "authority_tier": "tertiary"}),

    # Compliance patterns
    (r"(compliance|aml|kyc|bsa|regulatory)", {"domain": "Compliance", "subdomain": "General", "authority_tier": "tertiary"}),
    (r"(risk|audit|governance)", {"domain": "Compliance", "subdomain": "Risk", "authority_tier": "tertiary"}),

    # Credit patterns
    (r"(credit|debt|financing|loan.officer)", {"domain": "Credit", "subdomain": "Consumer", "authority_tier": "tertiary"}),

    # Financial planning patterns
    (r"(financial.plan|cfp|advisor|planner)", {"domain": "Wealth", "subdomain": "Planning", "authority_tier": "tertiary"}),

    # Certification patterns
    (r"(certification|credential|cfa|cpa|license|exam)", {"domain": "Credentials", "subdomain": "Professional", "authority_tier": "tertiary"}),

    # Career patterns
    (r"(career|job|salary|professional)", {"domain": "Professional", "subdomain": "Career", "authority_tier": "tertiary"}),

    # Technology patterns
    (r"(cybersecurity|fintech|api|cloud)", {"domain": "Technology", "subdomain": "FinTech", "authority_tier": "tertiary"}),

    # Pricing / Business
    (r"(pricing|valuation|dcf|startup)", {"domain": "Business", "subdomain": "Finance", "authority_tier": "tertiary"}),
]


def extract_domain(url: str) -> str:
    """Extract the base domain from a URL."""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        hostname = parsed.netloc or parsed.path.split("/")[0]
        # Remove www. prefix
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname.lower()
    except Exception:
        return url.lower()


def categorize_url(url: str, title: str) -> Dict[str, str]:
    """Categorize a URL based on domain and title patterns."""
    domain = extract_domain(url)

    # First, check exact domain mappings
    for mapped_domain, category in DOMAIN_MAPPINGS.items():
        if mapped_domain in domain:
            return category.copy()

    # Second, check keyword patterns in URL and title
    combined_text = f"{url} {title}".lower()
    for pattern, category in KEYWORD_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            return category.copy()

    # Default fallback
    return {"domain": "General", "subdomain": "Uncategorized", "authority_tier": "tertiary"}


def process_csv(input_file: str, output_file: str) -> Tuple[int, int]:
    """Process the master CSV and categorize uncategorized URLs."""
    categorized = 0
    already_categorized = 0
    rows = []

    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            # Check if already categorized (has domain value)
            if row.get("domain", "").strip():
                already_categorized += 1
                rows.append(row)
                continue

            # Get URL and title
            url = row.get("url", "") or row.get("title", "")
            title = row.get("title", "")

            if url:
                category = categorize_url(url, title)
                row["domain"] = category["domain"]
                row["subdomain"] = category["subdomain"]
                row["authority_tier"] = category["authority_tier"]
                categorized += 1

            rows.append(row)

    # Write output
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return categorized, already_categorized


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent / "Elson FAN"
    input_file = base_path / "master_training_resources_v5.csv"
    output_file = base_path / "master_training_resources_categorized.csv"

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1

    print("=" * 60)
    print("Elson TB2 - URL Categorization Script")
    print("=" * 60)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")

    categorized, already_done = process_csv(str(input_file), str(output_file))

    print(f"\nResults:")
    print(f"  - Already categorized: {already_done}")
    print(f"  - Newly categorized:   {categorized}")
    print(f"  - Total processed:     {categorized + already_done}")
    print(f"\nOutput saved to: {output_file}")

    # Print category distribution
    print("\nCategory Distribution:")
    with open(str(output_file), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        domain_counts: Dict[str, int] = {}
        for row in reader:
            domain = row.get("domain", "Unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  {domain}: {count}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
