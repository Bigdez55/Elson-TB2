#!/usr/bin/env python3
"""
Domain Bucket Builder for Elson Financial AI

Takes consolidated training data and outputs separate JSONL files per domain and difficulty.
This enables the curriculum-based training approach:
- Layer 1: Domain mastery blocks (train one domain at a time)
- Layer 2: Mixed domain randomization
- Layer 3: Stress testing with complex scenarios

Usage:
    python scripts/domain_bucket_builder.py
    python scripts/domain_bucket_builder.py --input path/to/data.json --output-dir buckets/

Output Structure:
    buckets/
    ├── federal_income_tax/
    │   ├── easy.jsonl
    │   ├── medium.jsonl
    │   ├── hard.jsonl
    │   └── extremely_complex.jsonl
    ├── securities_regulation/
    │   └── ...
    └── manifest.json  (summary of all buckets)
"""

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib

# Paths
DEFAULT_INPUT = Path(__file__).parent.parent / "backend" / "training_data" / "consolidated_all.json"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "backend" / "training_data" / "domain_buckets"

# =============================================================================
# DOMAIN DEFINITIONS AND MINIMUMS
# =============================================================================

# Critical domains requiring 3,000-5,000 pairs each
CRITICAL_DOMAINS = {
    "federal_income_tax",
    "securities_regulation",
    "aml_kyc",
    "derivatives",
    "fixed_income",
    "risk_management",
    "trade_execution",
    "market_microstructure",
    "compliance",
    "insurance",  # Added due to suitability requirements
}

# Target minimums by domain type
DOMAIN_MINIMUMS = {
    "critical": {"easy": 500, "medium": 1000, "hard": 1500, "extremely_complex": 500},
    "standard": {"easy": 300, "medium": 500, "hard": 500, "extremely_complex": 200},
}

# Difficulty tier definitions
DIFFICULTY_TIERS = ["easy", "medium", "hard", "extremely_complex"]


# =============================================================================
# DIFFICULTY CLASSIFICATION
# =============================================================================

# Patterns indicating difficulty levels
EASY_PATTERNS = [
    r'^what (is|are|does)\b',
    r'^define\b',
    r'^explain the (basics?|concept)\b',
    r'^what\'s the (meaning|definition)\b',
    r'\b(simple|basic|introduction|overview)\b',
]

MEDIUM_PATTERNS = [
    r'^how (do|does|should|can|would)\b',
    r'^when should\b',
    r'\b(example|scenario|situation)\b',
    r'\b(compare|versus|difference between)\b',
    r'\b(practical|apply|application)\b',
]

HARD_PATTERNS = [
    r'\b(calculate|compute|determine the)\b',
    r'\b(multiple|several|various) (factors|considerations|constraints)\b',
    r'\b(edge case|exception|special case)\b',
    r'\b(optimize|maximize|minimize)\b',
    r'\b(strategy|approach) for\b',
    r'\b(pros and cons|trade-?offs?|advantages and disadvantages)\b',
]

EXTREMELY_COMPLEX_PATTERNS = [
    r'\b(multi-?party|multiple (parties|stakeholders))\b',
    r'\b(conflicting|competing) (interests?|goals?|objectives?)\b',
    r'\b(compliance|regulatory|legal) (issue|concern|requirement)s?\b',
    r'\b(what if|scenario analysis|sensitivity)\b',
    r'\b(combined|integrated|holistic) (approach|strategy|plan)\b',
    r'\band\b.*\band\b.*\band\b',  # Multiple AND conditions
    r'\b(estate|trust|tax|insurance)\b.*\b(estate|trust|tax|insurance)\b',  # Multi-domain
]

# Compile patterns
EASY_COMPILED = [re.compile(p, re.IGNORECASE) for p in EASY_PATTERNS]
MEDIUM_COMPILED = [re.compile(p, re.IGNORECASE) for p in MEDIUM_PATTERNS]
HARD_COMPILED = [re.compile(p, re.IGNORECASE) for p in HARD_PATTERNS]
COMPLEX_COMPILED = [re.compile(p, re.IGNORECASE) for p in EXTREMELY_COMPLEX_PATTERNS]


def classify_difficulty(example: Dict) -> str:
    """
    Classify the difficulty tier of a training example.

    Uses multiple signals:
    1. Explicit difficulty field if present
    2. Question/instruction complexity patterns
    3. Output length and structure
    4. Domain risk level
    """
    # Check for explicit difficulty
    if 'difficulty' in example and example['difficulty'] in DIFFICULTY_TIERS:
        return example['difficulty']

    instruction = example.get('instruction', '').lower()
    output = example.get('output', '')
    domain = example.get('domain', example.get('category', 'general'))

    # Count pattern matches
    easy_score = sum(1 for p in EASY_COMPILED if p.search(instruction))
    medium_score = sum(1 for p in MEDIUM_COMPILED if p.search(instruction))
    hard_score = sum(1 for p in HARD_COMPILED if p.search(instruction))
    complex_score = sum(1 for p in COMPLEX_COMPILED if p.search(instruction))

    # Output complexity signals
    output_len = len(output)
    has_json = '{' in output and '}' in output
    has_multiple_sections = output.count('\n\n') >= 3
    has_calculations = bool(re.search(r'\d+\s*[+\-*/]\s*\d+', output))
    has_disclaimer = 'disclaimer' in output.lower() or 'consult' in output.lower()

    # Boost scores based on output characteristics
    if output_len > 1500:
        hard_score += 1
    if output_len > 2500:
        complex_score += 1
    if has_json:
        hard_score += 1
    if has_multiple_sections:
        medium_score += 1
    if has_calculations:
        hard_score += 1
    if has_disclaimer:
        complex_score += 0.5

    # Domain-based adjustments
    if domain in CRITICAL_DOMAINS:
        # Critical domains default to at least medium
        if easy_score > medium_score and easy_score > hard_score:
            medium_score = easy_score + 0.5

    # Determine tier
    scores = {
        'extremely_complex': complex_score,
        'hard': hard_score,
        'medium': medium_score,
        'easy': easy_score,
    }

    # Find highest scoring tier
    max_tier = max(scores, key=scores.get)
    max_score = scores[max_tier]

    # Default to medium if no clear signal
    if max_score < 0.5:
        return 'medium'

    return max_tier


def classify_task_type(example: Dict) -> str:
    """Classify the task type of an example."""
    instruction = example.get('instruction', '').lower()

    if 'calculate' in instruction or 'compute' in instruction or 'how much' in instruction:
        return 'calculation'
    if 'compare' in instruction or 'versus' in instruction or 'difference' in instruction:
        return 'comparison'
    if 'what is' in instruction or 'define' in instruction or 'explain' in instruction:
        return 'explanation'
    if 'should' in instruction or 'recommend' in instruction or 'best' in instruction:
        return 'recommendation'
    if 'how to' in instruction or 'steps' in instruction or 'process' in instruction:
        return 'procedural'
    if 'scenario' in instruction or 'case' in instruction or 'situation' in instruction:
        return 'scenario_analysis'

    return 'general'


def assess_risk_level(example: Dict) -> str:
    """Assess the risk level of an example."""
    instruction = example.get('instruction', '').lower()
    output = example.get('output', '').lower()
    domain = example.get('domain', example.get('category', 'general'))

    high_risk_domains = {'tax', 'federal_income_tax', 'compliance', 'securities_regulation',
                        'aml_kyc', 'insurance', 'estate_planning', 'derivatives'}

    high_risk_terms = ['specific', 'exact', 'must', 'required', 'guarantee', 'certain',
                      'should buy', 'should sell', 'recommend']

    if domain in high_risk_domains:
        return 'high'

    if any(term in instruction or term in output for term in high_risk_terms):
        return 'high'

    medium_risk_terms = ['strategy', 'plan', 'approach', 'consider', 'option']
    if any(term in instruction for term in medium_risk_terms):
        return 'medium'

    return 'low'


def requires_tools(example: Dict) -> bool:
    """Determine if the example requires tool calls."""
    instruction = example.get('instruction', '').lower()
    output = example.get('output', '').lower()

    tool_indicators = [
        'current price', 'current value', 'today', 'real-time',
        'p/e ratio', 'pe ratio', 'market cap', 'dividend yield',
        'get_quote', 'get_ratios', 'openbb', 'financetoolkit',
        'look up', 'check the', 'what is the current'
    ]

    return any(ind in instruction or ind in output for ind in tool_indicators)


def requires_retrieval(example: Dict) -> bool:
    """Determine if the example requires retrieval."""
    domain = example.get('domain', example.get('category', 'general'))
    instruction = example.get('instruction', '').lower()

    retrieval_domains = {'compliance', 'securities_regulation', 'aml_kyc', 'insurance',
                        'federal_income_tax', 'estate_planning'}

    retrieval_terms = ['regulation', 'rule', 'law', 'irs', 'sec', 'finra',
                      'requirement', 'guideline', 'standard']

    if domain in retrieval_domains:
        return True

    return any(term in instruction for term in retrieval_terms)


def enrich_example(example: Dict) -> Dict:
    """Add metadata fields to an example."""
    enriched = example.copy()

    # Classify difficulty if not present
    if 'difficulty' not in enriched or enriched['difficulty'] not in DIFFICULTY_TIERS:
        enriched['difficulty'] = classify_difficulty(example)

    # Add task type
    if 'task_type' not in enriched:
        enriched['task_type'] = classify_task_type(example)

    # Add risk level
    if 'risk_level' not in enriched:
        enriched['risk_level'] = assess_risk_level(example)

    # Add tool/retrieval flags
    if 'requires_tools' not in enriched:
        enriched['requires_tools'] = requires_tools(example)

    if 'requires_retrieval' not in enriched:
        enriched['requires_retrieval'] = requires_retrieval(example)

    return enriched


# =============================================================================
# BUCKET BUILDING
# =============================================================================

def load_training_data(input_path: Path) -> List[Dict]:
    """Load training data from JSON or JSONL file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        if input_path.suffix == '.jsonl':
            return [json.loads(line) for line in f if line.strip()]
        else:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data['data']
            else:
                return [data]


def build_domain_buckets(examples: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Build domain buckets organized by domain and difficulty.

    Returns:
        {
            "federal_income_tax": {
                "easy": [...],
                "medium": [...],
                "hard": [...],
                "extremely_complex": [...]
            },
            ...
        }
    """
    buckets = defaultdict(lambda: defaultdict(list))

    for example in examples:
        # Enrich with metadata
        enriched = enrich_example(example)

        # Get domain and difficulty
        domain = enriched.get('domain', enriched.get('category', 'general_finance'))
        difficulty = enriched.get('difficulty', 'medium')

        # Normalize domain name
        domain = domain.lower().replace(' ', '_').replace('-', '_')

        # Add to bucket
        buckets[domain][difficulty].append(enriched)

    return buckets


def save_buckets(buckets: Dict, output_dir: Path) -> Dict:
    """Save buckets to separate JSONL files and return manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "created_at": datetime.now().isoformat(),
        "domains": {},
        "totals": {
            "total_examples": 0,
            "by_difficulty": defaultdict(int),
            "by_domain_type": {"critical": 0, "standard": 0},
        },
        "gaps": [],  # Domains below minimums
    }

    for domain, difficulties in sorted(buckets.items()):
        domain_dir = output_dir / domain
        domain_dir.mkdir(exist_ok=True)

        domain_stats = {
            "total": 0,
            "by_difficulty": {},
            "is_critical": domain in CRITICAL_DOMAINS,
            "below_minimum": False,
            "files": [],
        }

        for difficulty in DIFFICULTY_TIERS:
            examples = difficulties.get(difficulty, [])
            count = len(examples)

            # Save JSONL file
            file_path = domain_dir / f"{difficulty}.jsonl"
            with open(file_path, 'w', encoding='utf-8') as f:
                for ex in examples:
                    f.write(json.dumps(ex, ensure_ascii=False) + '\n')

            domain_stats["by_difficulty"][difficulty] = count
            domain_stats["total"] += count
            domain_stats["files"].append(str(file_path.relative_to(output_dir)))

            manifest["totals"]["by_difficulty"][difficulty] += count

        # Check against minimums
        minimums = DOMAIN_MINIMUMS["critical"] if domain in CRITICAL_DOMAINS else DOMAIN_MINIMUMS["standard"]
        gaps = []
        for diff, min_count in minimums.items():
            actual = domain_stats["by_difficulty"].get(diff, 0)
            if actual < min_count:
                gaps.append({
                    "difficulty": diff,
                    "current": actual,
                    "minimum": min_count,
                    "gap": min_count - actual,
                })

        if gaps:
            domain_stats["below_minimum"] = True
            manifest["gaps"].append({
                "domain": domain,
                "is_critical": domain in CRITICAL_DOMAINS,
                "gaps": gaps,
            })

        manifest["domains"][domain] = domain_stats
        manifest["totals"]["total_examples"] += domain_stats["total"]

        if domain in CRITICAL_DOMAINS:
            manifest["totals"]["by_domain_type"]["critical"] += domain_stats["total"]
        else:
            manifest["totals"]["by_domain_type"]["standard"] += domain_stats["total"]

    # Convert defaultdict to dict for JSON serialization
    manifest["totals"]["by_difficulty"] = dict(manifest["totals"]["by_difficulty"])

    # Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def print_summary(manifest: Dict):
    """Print summary of bucket building."""
    print("\n" + "=" * 60)
    print("DOMAIN BUCKET BUILD SUMMARY")
    print("=" * 60)

    totals = manifest["totals"]
    print(f"\nTotal Examples: {totals['total_examples']:,}")

    print("\nBy Difficulty:")
    for diff in DIFFICULTY_TIERS:
        count = totals["by_difficulty"].get(diff, 0)
        pct = 100 * count / totals["total_examples"] if totals["total_examples"] > 0 else 0
        print(f"  {diff}: {count:,} ({pct:.1f}%)")

    print("\nBy Domain Type:")
    print(f"  Critical domains: {totals['by_domain_type']['critical']:,}")
    print(f"  Standard domains: {totals['by_domain_type']['standard']:,}")

    print(f"\nTotal Domains: {len(manifest['domains'])}")
    print(f"Critical Domains: {sum(1 for d in manifest['domains'].values() if d.get('is_critical'))}")

    # Show gaps
    gaps = manifest.get("gaps", [])
    if gaps:
        print("\n" + "=" * 60)
        print("DOMAINS BELOW MINIMUMS (Action Required)")
        print("=" * 60)
        for gap_info in gaps[:10]:  # Show top 10
            domain = gap_info["domain"]
            is_critical = "CRITICAL" if gap_info["is_critical"] else "standard"
            print(f"\n  {domain} ({is_critical}):")
            for g in gap_info["gaps"]:
                print(f"    {g['difficulty']}: {g['current']:,} / {g['minimum']:,} (need {g['gap']:,} more)")

        if len(gaps) > 10:
            print(f"\n  ... and {len(gaps) - 10} more domains below minimums")
    else:
        print("\n✓ All domains meet minimum requirements!")


def main():
    parser = argparse.ArgumentParser(description="Build domain buckets for curriculum training")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                       help="Input training data file (JSON or JSONL)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT),
                       help="Output directory for domain buckets")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    print("=" * 60)
    print("Elson Financial AI - Domain Bucket Builder")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")

    # Load data
    print("\n[1/3] Loading training data...")
    examples = load_training_data(input_path)
    print(f"  Loaded {len(examples):,} examples")

    # Build buckets
    print("\n[2/3] Building domain buckets...")
    buckets = build_domain_buckets(examples)
    print(f"  Created buckets for {len(buckets)} domains")

    # Save buckets
    print("\n[3/3] Saving buckets...")
    manifest = save_buckets(buckets, output_dir)
    print(f"  Saved to {output_dir}")

    # Print summary
    print_summary(manifest)

    print("\nDone!")


if __name__ == "__main__":
    main()
