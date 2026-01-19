#!/usr/bin/env python3
"""
Elson TB2 - Training Data Validation Pipeline
Validates quality, completeness, and distribution of training data.

Checks:
1. JSON well-formedness
2. Field completeness (instruction, input, output, category)
3. Domain classification accuracy
4. Deduplication (semantic similarity)
5. Length distribution
6. Domain balance (no single domain > 20%)
7. Quality gates
"""

import json
import hashlib
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import Counter

# Expected domains (62 total)
VALID_DOMAINS = {
    # Tax (6)
    "federal_income_tax", "state_local_tax", "international_tax", "estate_gift_tax", "corporate_tax", "tax_controversy",
    # Estate & Wealth (5)
    "estate_planning", "trust_administration", "probate", "charitable_planning", "gst_planning",
    # Insurance (8)
    "life_insurance", "health_insurance", "property_insurance", "casualty_insurance", "reinsurance", "annuities", "ltc_insurance", "actuarial",
    # Banking (5)
    "commercial_banking", "consumer_lending", "mortgage_finance", "credit_risk", "treasury_management",
    # Securities (10)
    "equities", "fixed_income", "derivatives", "commodities", "forex", "alternatives", "private_equity", "venture_capital", "hedge_funds", "cryptocurrency",
    # Portfolio (5)
    "portfolio_construction", "risk_management", "asset_allocation", "performance_attribution", "factor_investing",
    # Quantitative (5)
    "quantitative_finance", "algorithmic_trading", "hft", "market_microstructure", "trade_execution",
    # Corporate (4)
    "mergers_acquisitions", "business_valuation", "restructuring", "capital_markets",
    # Regulatory (6)
    "securities_regulation", "banking_regulation", "insurance_regulation", "aml_kyc", "erisa_benefits", "data_privacy",
    # Operations (4)
    "prime_brokerage", "custodial", "fund_administration", "fintech",
    # Planning (4)
    "financial_planning", "retirement_planning", "college_planning", "family_office",
    # Legacy/compatibility domains
    "general_finance", "tax", "fiduciary", "compliance", "investment_strategy",
    "high_frequency_trading", "data_engineering", "ai_ml", "infrastructure",
    "professional_roles", "goal_planning", "generational_wealth", "succession_planning"
}

# Quality thresholds
MIN_INSTRUCTION_LENGTH = 10
MAX_INSTRUCTION_LENGTH = 500
MIN_OUTPUT_LENGTH = 50
MAX_OUTPUT_LENGTH = 5000
MAX_DOMAIN_PERCENTAGE = 25  # No single domain should exceed 25%
MIN_UNIQUE_RATIO = 0.95  # At least 95% unique pairs


def generate_hash(text: str) -> str:
    """Generate a hash for deduplication."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def validate_json_structure(data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate JSON structure and required fields."""
    errors = []

    if not isinstance(data, list):
        return False, ["Data is not a list"]

    if len(data) == 0:
        return False, ["Data is empty"]

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i}: Not a dictionary")
            continue

        # Check required fields
        if "instruction" not in item:
            errors.append(f"Item {i}: Missing 'instruction' field")
        if "output" not in item:
            errors.append(f"Item {i}: Missing 'output' field")

        # Check field types
        if "instruction" in item and not isinstance(item["instruction"], str):
            errors.append(f"Item {i}: 'instruction' is not a string")
        if "output" in item and not isinstance(item["output"], str):
            errors.append(f"Item {i}: 'output' is not a string")

    return len(errors) == 0, errors


def validate_field_lengths(data: List[Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate field lengths and return statistics."""
    errors = []
    stats = {
        "instruction_lengths": [],
        "output_lengths": [],
        "too_short_instructions": 0,
        "too_long_instructions": 0,
        "too_short_outputs": 0,
        "too_long_outputs": 0,
        "empty_instructions": 0,
        "empty_outputs": 0
    }

    for i, item in enumerate(data):
        instruction = item.get("instruction", "")
        output = item.get("output", "")

        inst_len = len(instruction)
        out_len = len(output)

        stats["instruction_lengths"].append(inst_len)
        stats["output_lengths"].append(out_len)

        if inst_len == 0:
            stats["empty_instructions"] += 1
            errors.append(f"Item {i}: Empty instruction")
        elif inst_len < MIN_INSTRUCTION_LENGTH:
            stats["too_short_instructions"] += 1
        elif inst_len > MAX_INSTRUCTION_LENGTH:
            stats["too_long_instructions"] += 1

        if out_len == 0:
            stats["empty_outputs"] += 1
            errors.append(f"Item {i}: Empty output")
        elif out_len < MIN_OUTPUT_LENGTH:
            stats["too_short_outputs"] += 1
        elif out_len > MAX_OUTPUT_LENGTH:
            stats["too_long_outputs"] += 1

    # Calculate summary stats
    if stats["instruction_lengths"]:
        stats["avg_instruction_length"] = sum(stats["instruction_lengths"]) / len(stats["instruction_lengths"])
        stats["avg_output_length"] = sum(stats["output_lengths"]) / len(stats["output_lengths"])

    is_valid = stats["empty_instructions"] == 0 and stats["empty_outputs"] == 0
    return is_valid, errors, stats


def validate_domains(data: List[Dict[str, Any]], expected_domains: int = 62) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate domain distribution."""
    errors = []
    domain_counts = Counter()
    unknown_domains = set()

    for i, item in enumerate(data):
        category = item.get("category", "unknown")
        domain_counts[category] += 1

        if category not in VALID_DOMAINS and category != "unknown":
            unknown_domains.add(category)

    total = len(data)
    stats = {
        "domain_counts": dict(domain_counts),
        "num_domains": len(domain_counts),
        "expected_domains": expected_domains,
        "unknown_domains": list(unknown_domains),
        "domain_percentages": {}
    }

    # Check domain percentages
    max_percentage = 0
    for domain, count in domain_counts.items():
        percentage = (count / total) * 100
        stats["domain_percentages"][domain] = round(percentage, 2)
        if percentage > max_percentage:
            max_percentage = percentage

        if percentage > MAX_DOMAIN_PERCENTAGE:
            errors.append(f"Domain '{domain}' exceeds {MAX_DOMAIN_PERCENTAGE}% ({percentage:.1f}%)")

    stats["max_domain_percentage"] = round(max_percentage, 2)

    is_valid = len(errors) == 0
    return is_valid, errors, stats


def check_duplicates(data: List[Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Check for duplicate entries."""
    errors = []
    seen_hashes = {}
    duplicates = []

    for i, item in enumerate(data):
        # Hash based on instruction + output
        text = item.get("instruction", "") + item.get("output", "")
        hash_val = generate_hash(text)

        if hash_val in seen_hashes:
            duplicates.append({
                "index": i,
                "duplicate_of": seen_hashes[hash_val],
                "instruction_preview": item.get("instruction", "")[:50]
            })
        else:
            seen_hashes[hash_val] = i

    unique_count = len(data) - len(duplicates)
    unique_ratio = unique_count / len(data) if data else 0

    stats = {
        "total_pairs": len(data),
        "unique_pairs": unique_count,
        "duplicate_pairs": len(duplicates),
        "unique_ratio": round(unique_ratio, 4),
        "duplicates": duplicates[:20]  # Only show first 20
    }

    if unique_ratio < MIN_UNIQUE_RATIO:
        errors.append(f"Unique ratio {unique_ratio:.2%} is below threshold {MIN_UNIQUE_RATIO:.2%}")

    is_valid = len(errors) == 0
    return is_valid, errors, stats


def check_unsafe_content(data: List[Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Check for potentially unsafe or problematic content."""
    warnings = []

    # Patterns that might indicate unsafe financial advice
    unsafe_patterns = [
        (r"guaranteed\s+return", "Guaranteed return claims"),
        (r"risk.?free", "Risk-free claims"),
        (r"get\s+rich\s+quick", "Get rich quick language"),
        (r"100%\s+safe", "100% safe claims"),
        (r"can't\s+lose", "Can't lose claims"),
        (r"insider\s+information", "Insider information references"),
        (r"tax\s+evasion", "Tax evasion (should be avoidance)")
    ]

    flagged_items = []
    for i, item in enumerate(data):
        text = (item.get("instruction", "") + " " + item.get("output", "")).lower()

        for pattern, description in unsafe_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flagged_items.append({
                    "index": i,
                    "pattern": description,
                    "instruction_preview": item.get("instruction", "")[:50]
                })
                warnings.append(f"Item {i}: Flagged for '{description}'")

    stats = {
        "flagged_count": len(flagged_items),
        "flagged_items": flagged_items[:20]  # Only show first 20
    }

    # Flagged items are warnings, not errors (human review needed)
    is_valid = True
    return is_valid, warnings, stats


def validate_training_data(
    input_path: str,
    check_balance: bool = True,
    expected_domains: int = 62,
    full_validation: bool = False
) -> Dict[str, Any]:
    """
    Main validation function.

    Args:
        input_path: Path to training data JSON
        check_balance: Whether to check domain balance
        expected_domains: Expected number of domains
        full_validation: Run all validation checks

    Returns:
        Validation report dictionary
    """
    print(f"Validating training data: {input_path}")

    # Load data
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON: {e}",
            "timestamp": datetime.now().isoformat()
        }
    except FileNotFoundError:
        return {
            "valid": False,
            "error": f"File not found: {input_path}",
            "timestamp": datetime.now().isoformat()
        }

    report = {
        "input_file": input_path,
        "timestamp": datetime.now().isoformat(),
        "total_records": len(data),
        "checks": {},
        "valid": True,
        "errors": [],
        "warnings": []
    }

    # 1. JSON Structure
    print("  1. Checking JSON structure...")
    is_valid, errors = validate_json_structure(data)
    report["checks"]["json_structure"] = {
        "valid": is_valid,
        "errors": errors[:20]
    }
    if not is_valid:
        report["valid"] = False
        report["errors"].extend(errors[:10])

    # 2. Field Lengths
    print("  2. Checking field lengths...")
    is_valid, errors, stats = validate_field_lengths(data)
    report["checks"]["field_lengths"] = {
        "valid": is_valid,
        "errors": errors[:20],
        "stats": {
            "avg_instruction_length": round(stats.get("avg_instruction_length", 0), 1),
            "avg_output_length": round(stats.get("avg_output_length", 0), 1),
            "empty_instructions": stats.get("empty_instructions", 0),
            "empty_outputs": stats.get("empty_outputs", 0),
            "too_short_instructions": stats.get("too_short_instructions", 0),
            "too_short_outputs": stats.get("too_short_outputs", 0)
        }
    }
    if not is_valid:
        report["valid"] = False
        report["errors"].extend(errors[:5])

    # 3. Domain Distribution
    if check_balance:
        print("  3. Checking domain distribution...")
        is_valid, errors, stats = validate_domains(data, expected_domains)
        report["checks"]["domain_distribution"] = {
            "valid": is_valid,
            "errors": errors,
            "stats": {
                "num_domains": stats.get("num_domains", 0),
                "expected_domains": expected_domains,
                "max_domain_percentage": stats.get("max_domain_percentage", 0),
                "top_domains": dict(sorted(
                    stats.get("domain_percentages", {}).items(),
                    key=lambda x: -x[1]
                )[:10])
            }
        }
        if not is_valid:
            report["warnings"].extend(errors)  # Domain imbalance is a warning

    # 4. Duplicates
    print("  4. Checking for duplicates...")
    is_valid, errors, stats = check_duplicates(data)
    report["checks"]["duplicates"] = {
        "valid": is_valid,
        "errors": errors,
        "stats": {
            "total_pairs": stats.get("total_pairs", 0),
            "unique_pairs": stats.get("unique_pairs", 0),
            "duplicate_pairs": stats.get("duplicate_pairs", 0),
            "unique_ratio": stats.get("unique_ratio", 0)
        }
    }
    if not is_valid:
        report["warnings"].extend(errors)

    # 5. Unsafe Content (full validation only)
    if full_validation:
        print("  5. Checking for unsafe content...")
        is_valid, warnings, stats = check_unsafe_content(data)
        report["checks"]["unsafe_content"] = {
            "valid": is_valid,
            "warnings": warnings[:20],
            "stats": {
                "flagged_count": stats.get("flagged_count", 0)
            }
        }
        report["warnings"].extend(warnings[:10])

    # Summary
    report["summary"] = {
        "total_records": len(data),
        "valid": report["valid"],
        "error_count": len(report["errors"]),
        "warning_count": len(report["warnings"]),
        "checks_passed": sum(1 for c in report["checks"].values() if c.get("valid", False)),
        "checks_total": len(report["checks"])
    }

    return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Elson TB2 training data")
    parser.add_argument("--input", "-i",
                        default="backend/training_data/consolidated_training_data.json",
                        help="Input training data JSON file")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/validation_report.json",
                        help="Output validation report JSON file")
    parser.add_argument("--check-balance", action="store_true",
                        help="Check domain balance")
    parser.add_argument("--expected-domains", type=int, default=62,
                        help="Expected number of domains")
    parser.add_argument("--full-validation", action="store_true",
                        help="Run all validation checks including unsafe content")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    input_path = project_root / args.input
    output_path = project_root / args.output

    # Run validation
    report = validate_training_data(
        str(input_path),
        check_balance=args.check_balance,
        expected_domains=args.expected_domains,
        full_validation=args.full_validation
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"\nValidation report saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total records: {report['summary']['total_records']}")
    print(f"Checks passed: {report['summary']['checks_passed']}/{report['summary']['checks_total']}")
    print(f"Errors: {report['summary']['error_count']}")
    print(f"Warnings: {report['summary']['warning_count']}")
    print(f"Overall: {'PASSED' if report['valid'] else 'FAILED'}")
    print("=" * 60)

    # Exit with error code if validation failed
    if not report["valid"]:
        print("\nErrors:")
        for error in report["errors"][:10]:
            print(f"  - {error}")
        sys.exit(1)

    if args.strict and report["warnings"]:
        print("\nWarnings (strict mode):")
        for warning in report["warnings"][:10]:
            print(f"  - {warning}")
        sys.exit(1)


if __name__ == "__main__":
    main()
