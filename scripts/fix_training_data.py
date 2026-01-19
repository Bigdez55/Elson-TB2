#!/usr/bin/env python3
"""
Training Data Fixer for Elson Financial AI

Addresses critical issues before next training run:
1. Removes guaranteed/risk-free language from training data
2. Implements weighted sampling by domain
3. Creates proper validation split
4. Forces structured output in 20%+ of training data

Usage:
    python scripts/fix_training_data.py
"""

import json
import random
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
import hashlib

# Paths
TRAINING_DATA_DIR = Path(__file__).parent.parent / "backend" / "training_data"
OUTPUT_DIR = TRAINING_DATA_DIR

# Random seed for reproducibility
random.seed(42)

# =============================================================================
# COMPLIANCE PATTERNS TO REMOVE
# =============================================================================

# Patterns that violate compliance (guaranteed returns, risk-free, etc.)
VIOLATION_PATTERNS = [
    # Guaranteed returns
    (r'\bguaranteed?\s+(return|profit|gain|income|yield)s?\b', 'guaranteed_returns'),
    (r'\brisk[\-\s]?free\s+(return|investment|profit)s?\b', 'risk_free_claims'),
    (r'\b(will|shall)\s+(?:definitely|certainly|always)\s+(?:make|earn|get)\b', 'certain_outcomes'),
    (r'\b(never|cannot|won\'t)\s+lose\s+(?:money|value|principal)\b', 'no_loss_claims'),
    (r'\b100%\s+(?:safe|secure|guaranteed)\b', 'absolute_safety'),

    # Certainty language that shouldn't be used
    (r'\balways\s+(?:increase|grow|appreciate|profit)\b', 'always_positive'),
    (r'\bnever\s+(?:decrease|fall|lose|decline)\b', 'never_negative'),
    (r'\b(?:sure|certain)\s+thing\b', 'sure_thing'),
    (r'\brisk[\-\s]?free\b(?!\s+rate)', 'risk_free_general'),  # Allow "risk-free rate"

    # Improper advice language
    (r'\byou\s+(?:must|should|need\s+to)\s+(?:buy|sell|invest\s+in)\s+[A-Z]{1,5}\b', 'specific_security_advice'),
    (r'\b(?:buy|sell)\s+(?:now|immediately|today)\b', 'urgency_trading'),

    # Tax advice violations
    (r'\bthis\s+will\s+(?:reduce|lower|eliminate)\s+your\s+taxes?\b', 'tax_guarantee'),
    (r'\byou\s+(?:will|can)\s+(?:definitely|certainly)\s+(?:deduct|claim)\b', 'tax_certainty'),
]

# Replacement fixes for common violations
VIOLATION_FIXES = {
    'guaranteed_returns': 'potential returns',
    'risk_free_claims': 'lower-risk investment',
    'certain_outcomes': 'may potentially',
    'no_loss_claims': 'investments carry risk',
    'absolute_safety': 'considered relatively safe',
    'always_positive': 'historically has tended to',
    'never_negative': 'has shown resilience but can',
    'sure_thing': 'appears favorable but carries risk',
    'risk_free_general': 'lower-risk',
    'specific_security_advice': 'consider discussing with an advisor',
    'urgency_trading': 'consider your options carefully',
    'tax_guarantee': 'may potentially reduce',
    'tax_certainty': 'may be able to',
}

# Compiled patterns
COMPILED_VIOLATIONS = [(re.compile(p, re.IGNORECASE), t) for p, t in VIOLATION_PATTERNS]


# =============================================================================
# DOMAIN CLASSIFICATION
# =============================================================================

DOMAIN_PATTERNS = {
    'general_finance': [
        r'\b(money|finance|financial|wealth)\b',
        r'\b(bank|account|credit|debit)\b',
    ],
    'budgeting': [
        r'\bbudget\b', r'\bspending\b', r'\b50.?30.?20\b',
        r'\bexpense\b', r'\btrack\b.*\b(money|spend)\b',
    ],
    'savings': [
        r'\b(save|saving|savings)\b', r'\bemergency fund\b',
        r'\bhigh.?yield\b',
    ],
    'debt_management': [
        r'\bdebt\b', r'\bloan\b', r'\bcredit card\b',
        r'\b(snowball|avalanche)\b', r'\bmortgage\b',
    ],
    'retirement': [
        r'\bretire\b', r'\b401k\b', r'\bira\b', r'\broth\b',
        r'\bpension\b', r'\bsocial security\b',
    ],
    'insurance': [
        r'\binsurance\b', r'\bpolicy\b', r'\bpremium\b',
        r'\bcoverage\b', r'\bdeductible\b',
    ],
    'tax_education': [
        r'\btax\b', r'\birs\b', r'\bdeduction\b',
        r'\bwithholding\b', r'\bfiling\b',
    ],
    'investing_basics': [
        r'\b(stock|bond|etf|fund)\b', r'\bmarket\b',
        r'\bdiversif\b', r'\binvest\b',
    ],
    'portfolio_management': [
        r'\bportfolio\b', r'\ballocation\b', r'\brebalance\b',
        r'\basset class\b', r'\brisk tolerance\b',
    ],
    'trading': [
        r'\btrade\b', r'\bentry\b', r'\bexit\b',
        r'\bstop.?loss\b', r'\bposition\b',
    ],
    'compliance': [
        r'\bcompliance\b', r'\bregulation\b', r'\bfiduciary\b',
        r'\bsuitability\b', r'\bdisclosure\b',
    ],
    'estate_planning': [
        r'\bestate\b', r'\binheritance\b', r'\btrust\b',
        r'\bwill\b', r'\bprobate\b',
    ],
    'tool_use': [
        r'\bget_quote\b', r'\bget_ratios\b', r'\btool_call\b',
        r'\bopenbb\b', r'\bfinancetoolkit\b',
    ],
    'accounting': [
        r'\bbook\s?keeping\b', r'\bledger\b', r'\breconcil\b',
        r'\baccounts\s+(payable|receivable)\b',
    ],
}

COMPILED_DOMAINS = {
    domain: [re.compile(p, re.IGNORECASE) for p in patterns]
    for domain, patterns in DOMAIN_PATTERNS.items()
}


# =============================================================================
# TARGET SAMPLING WEIGHTS
# =============================================================================

# Target distribution (percentages) - general_finance reduced from 61% to 15%
TARGET_WEIGHTS = {
    'general_finance': 0.10,      # Reduced from 61%
    'budgeting': 0.08,
    'savings': 0.08,
    'debt_management': 0.08,
    'retirement': 0.10,
    'insurance': 0.10,
    'tax_education': 0.08,
    'investing_basics': 0.08,
    'portfolio_management': 0.08,
    'trading': 0.05,
    'compliance': 0.05,
    'estate_planning': 0.05,
    'tool_use': 0.04,
    'accounting': 0.03,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_training_data(filepath: Path) -> List[Dict]:
    """Load training data from JSON file"""
    if not filepath.exists():
        print(f"Warning: {filepath} not found")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'data' in data:
        return data['data']
    else:
        return [data]


def classify_domain(example: Dict) -> str:
    """Classify an example into a domain"""
    # Check explicit domain/category
    if 'domain' in example and example['domain']:
        return example['domain']
    if 'category' in example and example['category']:
        return example['category']

    # Classify by content
    text = f"{example.get('instruction', '')} {example.get('output', '')}".lower()

    best_domain = 'general_finance'
    best_score = 0

    for domain, patterns in COMPILED_DOMAINS.items():
        score = sum(1 for p in patterns if p.search(text))
        if score > best_score:
            best_score = score
            best_domain = domain

    return best_domain


def check_violations(text: str) -> List[Tuple[str, str, str]]:
    """Check text for compliance violations"""
    violations = []
    for pattern, violation_type in COMPILED_VIOLATIONS:
        matches = pattern.findall(text)
        for match in matches:
            violations.append((violation_type, match if isinstance(match, str) else match[0], text[:50]))
    return violations


def fix_violations(text: str) -> Tuple[str, int]:
    """Fix compliance violations in text"""
    fixed_text = text
    fix_count = 0

    for pattern, violation_type in COMPILED_VIOLATIONS:
        if pattern.search(fixed_text):
            fix = VIOLATION_FIXES.get(violation_type, 'consult a professional')
            fixed_text = pattern.sub(fix, fixed_text)
            fix_count += 1

    return fixed_text, fix_count


def add_structured_output_marker(example: Dict) -> Dict:
    """Add structured output requirement to an example"""
    # Determine appropriate schema based on domain
    domain = classify_domain(example)

    schema_mapping = {
        'budgeting': 'FinancialPlan',
        'savings': 'FinancialPlan',
        'debt_management': 'FinancialPlan',
        'retirement': 'FinancialPlan',
        'portfolio_management': 'PortfolioPolicy',
        'trading': 'TradePlan',
        'compliance': 'ComplianceCheck',
        'estate_planning': 'ScenarioAnalysis',
        'tax_education': 'ScenarioAnalysis',
    }

    schema = schema_mapping.get(domain)
    if schema:
        example['required_schema'] = schema
        example['structured_output'] = True

    return example


def create_validation_split(
    examples: List[Dict],
    val_ratio: float = 0.1
) -> Tuple[List[Dict], List[Dict]]:
    """Create train/validation split maintaining domain distribution"""
    # Group by domain
    by_domain = defaultdict(list)
    for ex in examples:
        domain = classify_domain(ex)
        by_domain[domain].append(ex)

    train_examples = []
    val_examples = []

    for domain, domain_examples in by_domain.items():
        random.shuffle(domain_examples)
        val_count = max(1, int(len(domain_examples) * val_ratio))

        val_examples.extend(domain_examples[:val_count])
        train_examples.extend(domain_examples[val_count:])

    random.shuffle(train_examples)
    random.shuffle(val_examples)

    return train_examples, val_examples


def apply_weighted_sampling(
    examples: List[Dict],
    target_total: int,
    weights: Dict[str, float]
) -> List[Dict]:
    """Apply weighted sampling to achieve target distribution"""
    # Group by domain
    by_domain = defaultdict(list)
    for ex in examples:
        domain = classify_domain(ex)
        by_domain[domain].append(ex)

    sampled = []

    for domain, target_weight in weights.items():
        target_count = int(target_total * target_weight)
        available = by_domain.get(domain, [])

        if len(available) >= target_count:
            # Sample without replacement
            sampled.extend(random.sample(available, target_count))
        else:
            # Oversample with replacement if needed
            sampled.extend(available)
            if target_count > len(available) and available:
                extra_needed = target_count - len(available)
                sampled.extend(random.choices(available, k=extra_needed))

    # Add any domains not in weights
    for domain, domain_examples in by_domain.items():
        if domain not in weights:
            # Add small sample of unknown domains
            sample_size = min(len(domain_examples), int(target_total * 0.01))
            sampled.extend(random.sample(domain_examples, sample_size))

    random.shuffle(sampled)
    return sampled


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def main():
    print("=" * 60)
    print("Elson Financial AI - Training Data Fixer")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Load all training data
    print("\n[1/6] Loading training data...")
    all_examples = []

    training_files = [
        "consolidated_all.json",
    ]

    for filename in training_files:
        filepath = TRAINING_DATA_DIR / filename
        examples = load_training_data(filepath)
        print(f"  Loaded {len(examples):,} from {filename}")
        all_examples.extend(examples)

    print(f"  Total examples: {len(all_examples):,}")

    # Check for violations
    print("\n[2/6] Checking for compliance violations...")
    violation_counts = defaultdict(int)
    examples_with_violations = []

    for ex in all_examples:
        text = f"{ex.get('instruction', '')} {ex.get('output', '')}"
        violations = check_violations(text)
        if violations:
            examples_with_violations.append((ex, violations))
            for v_type, _, _ in violations:
                violation_counts[v_type] += 1

    print(f"  Examples with violations: {len(examples_with_violations):,}")
    print("  Violation types:")
    for v_type, count in sorted(violation_counts.items(), key=lambda x: -x[1]):
        print(f"    {v_type}: {count}")

    # Fix violations
    print("\n[3/6] Fixing compliance violations...")
    fixed_examples = []
    total_fixes = 0

    for ex in all_examples:
        new_ex = ex.copy()

        # Fix instruction
        if 'instruction' in new_ex:
            new_ex['instruction'], fixes = fix_violations(new_ex['instruction'])
            total_fixes += fixes

        # Fix output
        if 'output' in new_ex:
            new_ex['output'], fixes = fix_violations(new_ex['output'])
            total_fixes += fixes

        fixed_examples.append(new_ex)

    print(f"  Total fixes applied: {total_fixes:,}")

    # Verify fixes
    remaining_violations = 0
    for ex in fixed_examples:
        text = f"{ex.get('instruction', '')} {ex.get('output', '')}"
        violations = check_violations(text)
        remaining_violations += len(violations)

    print(f"  Remaining violations: {remaining_violations:,}")

    # Classify domains
    print("\n[4/6] Classifying domains...")
    domain_counts = defaultdict(int)
    for ex in fixed_examples:
        domain = classify_domain(ex)
        ex['domain'] = domain
        domain_counts[domain] += 1

    print("  Domain distribution (before weighting):")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(fixed_examples)
        print(f"    {domain}: {count:,} ({pct:.1f}%)")

    # Apply weighted sampling
    print("\n[5/6] Applying weighted sampling...")
    target_size = min(len(fixed_examples), 30000)  # Cap at 30K for manageability
    weighted_examples = apply_weighted_sampling(fixed_examples, target_size, TARGET_WEIGHTS)

    # Recount domains after weighting
    weighted_domain_counts = defaultdict(int)
    for ex in weighted_examples:
        weighted_domain_counts[ex.get('domain', 'unknown')] += 1

    print(f"  Weighted sample size: {len(weighted_examples):,}")
    print("  Domain distribution (after weighting):")
    for domain, count in sorted(weighted_domain_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(weighted_examples)
        print(f"    {domain}: {count:,} ({pct:.1f}%)")

    # Add structured output requirements to 20%+
    print("\n[5b/6] Adding structured output requirements...")
    structured_count = 0
    for i, ex in enumerate(weighted_examples):
        if i % 4 == 0:  # 25% get structured output requirement
            add_structured_output_marker(ex)
            structured_count += 1

    print(f"  Examples with structured output requirement: {structured_count:,} ({100*structured_count/len(weighted_examples):.1f}%)")

    # Create train/val split
    print("\n[6/6] Creating train/validation split...")
    train_examples, val_examples = create_validation_split(weighted_examples, val_ratio=0.1)

    print(f"  Training examples: {len(train_examples):,}")
    print(f"  Validation examples: {len(val_examples):,}")

    # Save outputs
    print("\n[SAVING] Writing output files...")

    # Training data
    train_path = OUTPUT_DIR / "train_fixed.json"
    with open(train_path, 'w', encoding='utf-8') as f:
        json.dump(train_examples, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {train_path}")

    # Training JSONL
    train_jsonl_path = OUTPUT_DIR / "train_fixed.jsonl"
    with open(train_jsonl_path, 'w', encoding='utf-8') as f:
        for ex in train_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    print(f"  Saved: {train_jsonl_path}")

    # Validation data
    val_path = OUTPUT_DIR / "val_fixed.json"
    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_examples, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {val_path}")

    # Validation JSONL
    val_jsonl_path = OUTPUT_DIR / "val_fixed.jsonl"
    with open(val_jsonl_path, 'w', encoding='utf-8') as f:
        for ex in val_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    print(f"  Saved: {val_jsonl_path}")

    # Statistics
    stats = {
        "generated_at": datetime.now().isoformat(),
        "original_count": len(all_examples),
        "violations_found": len(examples_with_violations),
        "fixes_applied": total_fixes,
        "remaining_violations": remaining_violations,
        "weighted_count": len(weighted_examples),
        "train_count": len(train_examples),
        "val_count": len(val_examples),
        "structured_output_count": structured_count,
        "domain_distribution_before": dict(domain_counts),
        "domain_distribution_after": dict(weighted_domain_counts),
        "target_weights": TARGET_WEIGHTS,
    }

    stats_path = OUTPUT_DIR / "training_data_fix_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"  Saved: {stats_path}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Original examples:      {len(all_examples):,}")
    print(f"Violations fixed:       {total_fixes:,}")
    print(f"Remaining violations:   {remaining_violations:,}")
    print(f"Training examples:      {len(train_examples):,}")
    print(f"Validation examples:    {len(val_examples):,}")
    print(f"Structured output:      {structured_count:,} ({100*structured_count/len(weighted_examples):.1f}%)")
    print(f"\nGeneral finance reduced from ~61% to {100*weighted_domain_counts.get('general_finance', 0)/len(weighted_examples):.1f}%")
    print("\nReady for DoRA v3 training!")


if __name__ == "__main__":
    main()
