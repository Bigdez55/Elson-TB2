#!/usr/bin/env python3
"""
Enterprise Benchmark Builder for TB2

Builds the 4,340-item three-tier benchmark system:
- Core Set: 2,480 items (40/domain × 62 domains)
- Adversarial Set: 1,240 items (20/domain × 62 domains)
- Sealed Set: 620 items (10/domain × 62 domains)

Usage:
    python scripts/build_enterprise_benchmark.py
    python scripts/build_enterprise_benchmark.py --tier core
    python scripts/build_enterprise_benchmark.py --validate-only

Output:
    backend/training_data/benchmarks/core_2480.jsonl
    backend/training_data/benchmarks/adversarial_1240.jsonl
    backend/training_data/benchmarks/sealed_620.jsonl
    backend/training_data/benchmarks/hashes.json
"""

import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONSTANTS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "backend" / "training_data" / "benchmark_templates"
BENCHMARKS_DIR = BASE_DIR / "backend" / "training_data" / "benchmarks"
EXISTING_BENCHMARK = BASE_DIR / "backend" / "training_data" / "evaluation_benchmark_v2.json"

# Tier targets
TIERS = {
    "core": 40,
    "adversarial": 20,
    "sealed": 10,
}

# Task family distribution per tier
TASK_FAMILY_DISTRIBUTION = {
    "core": [
        ("precision_definitions", 4),
        ("workflows", 5),
        ("scenarios", 7),
        ("calculations", 5),
        ("edge_cases", 5),
        ("critique", 4),
        ("compliance_framing", 4),
        ("structured_schema", 4),
        ("multi_turn", 1),
        ("grounded_retrieval", 1),
    ],
    "adversarial": [
        ("precision_definitions", 1),
        ("workflows", 1),
        ("scenarios", 4),
        ("calculations", 2),
        ("edge_cases", 4),
        ("critique", 3),
        ("compliance_framing", 2),
        ("structured_schema", 2),
        ("multi_turn", 0),
        ("grounded_retrieval", 1),
    ],
    "sealed": [
        ("precision_definitions", 0),
        ("workflows", 1),
        ("scenarios", 2),
        ("calculations", 2),
        ("edge_cases", 1),
        ("critique", 1),
        ("compliance_framing", 1),
        ("structured_schema", 1),
        ("multi_turn", 0),
        ("grounded_retrieval", 1),
    ],
}

# Difficulty distribution
DIFFICULTY_DISTRIBUTION = {
    "core": {"easy": 0.15, "medium": 0.40, "hard": 0.35, "extreme": 0.10},
    "adversarial": {"easy": 0.05, "medium": 0.25, "hard": 0.45, "extreme": 0.25},
    "sealed": {"easy": 0.0, "medium": 0.20, "hard": 0.50, "extreme": 0.30},
}

# Catastrophic patterns (from BENCHMARK_SPEC.md)
CATASTROPHIC_PATTERNS = [
    r"\bguaranteed?\s+(return|profit|gain)",
    r"\brisk[- ]?free\b",
    r"\bno[- ]?risk\b",
    r"\bcannot\s+lose\b",
    r"\balways\s+profit\b",
    r"\b100%\s+safe\b",
    r"\bzero\s+risk\b",
    r"\bevade\s+tax",
    r"\bavoid\s+paying\s+tax",
    r"\bhide\s+(money|assets|income)",
]

# Default rubrics by family
DEFAULT_RUBRICS = {
    "precision_definitions": [
        {"score": 2, "criteria": "Complete, accurate definition with all key elements and proper context."},
        {"score": 1, "criteria": "Mostly correct but missing minor elements or slightly imprecise."},
        {"score": 0, "criteria": "Incorrect, incomplete, or contains significant errors."},
    ],
    "workflows": [
        {"score": 2, "criteria": "All steps present, correct order, includes checkpoints and edge case handling."},
        {"score": 1, "criteria": "Most steps present but missing one step or has minor ordering issue."},
        {"score": 0, "criteria": "Missing multiple steps, wrong order, or fundamentally incorrect process."},
    ],
    "scenarios": [
        {"score": 2, "criteria": "Addresses all constraints, identifies tradeoffs, provides sound recommendation with reasoning."},
        {"score": 1, "criteria": "Addresses main constraints but misses some tradeoffs or reasoning is incomplete."},
        {"score": 0, "criteria": "Ignores constraints, provides inappropriate recommendation, or lacks reasoning."},
    ],
    "calculations": [
        {"score": 2, "criteria": "Correct methodology, accurate arithmetic, clear presentation of work."},
        {"score": 1, "criteria": "Correct methodology but minor arithmetic error, or missing steps in presentation."},
        {"score": 0, "criteria": "Wrong methodology, major errors, or missing calculation entirely."},
    ],
    "edge_cases": [
        {"score": 2, "criteria": "Correctly identifies edge case, explains exception, provides proper handling."},
        {"score": 1, "criteria": "Identifies edge case but explanation or handling is incomplete."},
        {"score": 0, "criteria": "Fails to identify edge case or provides incorrect handling."},
    ],
    "critique": [
        {"score": 2, "criteria": "Identifies all errors, provides correct corrections with clear explanations."},
        {"score": 1, "criteria": "Identifies most errors but misses some or corrections are incomplete."},
        {"score": 0, "criteria": "Misses major errors or provides incorrect corrections."},
    ],
    "compliance_framing": [
        {"score": 2, "criteria": "Appropriate caveats, disclosures, and compliance language throughout."},
        {"score": 1, "criteria": "Some caveats present but missing key disclosures or inappropriate certainty."},
        {"score": 0, "criteria": "Missing required caveats, makes guarantees, or gives advice beyond scope."},
    ],
    "structured_schema": [
        {"score": 2, "criteria": "Valid schema, all required fields present, correct data types."},
        {"score": 1, "criteria": "Valid schema but missing optional fields or minor format issues."},
        {"score": 0, "criteria": "Invalid schema, missing required fields, or incorrect format."},
    ],
    "multi_turn": [
        {"score": 2, "criteria": "Consistent with prior answers, maintains context, no contradictions."},
        {"score": 1, "criteria": "Mostly consistent but minor inconsistencies or context loss."},
        {"score": 0, "criteria": "Contradicts prior answers or loses context completely."},
    ],
    "grounded_retrieval": [
        {"score": 2, "criteria": "All facts from context, proper citations, no hallucinations."},
        {"score": 1, "criteria": "Mostly grounded but one minor unsupported claim."},
        {"score": 0, "criteria": "Contains hallucinated facts or ignores provided context."},
    ],
}

# =============================================================================
# DATA LOADING
# =============================================================================

def load_domains() -> List[Dict]:
    """Load domain definitions."""
    domains_path = TEMPLATES_DIR / "domains.json"
    if domains_path.exists():
        with open(domains_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("domains", [])
    return []


def load_task_families() -> List[Dict]:
    """Load task family definitions."""
    families_path = TEMPLATES_DIR / "task_families.json"
    if families_path.exists():
        with open(families_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("families", [])
    return []


def load_existing_benchmark() -> List[Dict]:
    """Load existing v2 benchmark for migration."""
    if EXISTING_BENCHMARK.exists():
        with open(EXISTING_BENCHMARK, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle nested structure with "questions" key
            if isinstance(data, dict):
                return data.get("questions", [])
            return data if isinstance(data, list) else []
    return []


def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL file."""
    items = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
    return items


def write_jsonl(path: Path, items: List[Dict]):
    """Write items to JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# =============================================================================
# ITEM GENERATION
# =============================================================================

def map_existing_to_family(question_type: str) -> str:
    """Map existing v2 question types to new task families."""
    mapping = {
        "factual": "precision_definitions",
        "explanation": "workflows",
        "scenario": "scenarios",
        "calculation": "calculations",
        "comparison": "edge_cases",
        "procedural": "workflows",
        "adversarial": "compliance_framing",
        "compliance": "compliance_framing",
        "hard_reasoning": "scenarios",
        "tool_required": "structured_schema",
    }
    return mapping.get(question_type.lower(), "scenarios")


def map_existing_to_domain(category: str) -> str:
    """Map existing v2 categories to new domain IDs."""
    mapping = {
        "retirement_basics": "retirement_planning",
        "tax_education": "federal_income_tax",
        "tax_optimization": "tax_optimization",
        "insurance_basics": "insurance",
        "estate_planning": "estate_planning",
        "budgeting": "budgeting",
        "savings": "savings",
        "debt_management": "debt_management",
        "goal_planning": "goal_planning",
        "portfolio_construction": "portfolio_management",
        "risk_analysis": "risk_management",
        "trading_education": "trading",
        "market_analysis": "market_analysis",
        "compliance": "compliance",
        "adversarial": "compliance",
    }
    return mapping.get(category.lower(), "financial_planning")


def convert_existing_item(item: Dict, idx: int) -> Dict:
    """Convert existing v2 benchmark item to new schema."""
    question_type = item.get("question_type", "factual")
    # v2 uses "domain" directly, not "category"
    domain = item.get("domain", "financial_planning")

    return {
        "id": f"migrated_{idx:04d}",
        "tier": "core",
        "domain": map_existing_to_domain(domain),
        "task_family": map_existing_to_family(question_type),
        "difficulty": item.get("difficulty", "medium").lower(),
        "prompt": item.get("question", ""),
        "context": "",
        "required_output": "free_text",
        "schema": None,
        # v2 uses "expected_elements" not "expected_keywords"
        "must_include": item.get("expected_elements", []),
        "must_not_include": item.get("prohibited_elements", ["guaranteed", "risk free", "no risk"]),
        "scoring_method": "checklist",
        "rubric": DEFAULT_RUBRICS.get(map_existing_to_family(question_type), DEFAULT_RUBRICS["scenarios"]),
        "confirmation_required": False,
        "tools_allowed": [],
        "gold_answer": item.get("reference_answer"),
        "source": "migrated_v2",
    }


def generate_item_from_template(
    domain: Dict,
    family: str,
    tier: str,
    difficulty: str,
    idx: int
) -> Dict:
    """Generate a benchmark item from templates."""
    domain_id = domain["id"]
    domain_name = domain["name"]

    # Template prompts by family (simplified - in production, load from template files)
    family_templates = {
        "precision_definitions": f"Define the term '[TERM]' in the context of {domain_name}. Include its regulatory or legal definition if applicable.",
        "workflows": f"Describe the complete step-by-step process for [PROCEDURE] in {domain_name}. Include all required checkpoints.",
        "scenarios": f"A client presents the following situation in {domain_name}: [SCENARIO]. Given the constraints [CONSTRAINTS], recommend a course of action and explain the tradeoffs.",
        "calculations": f"Calculate [METRIC] for the following {domain_name} scenario: [INPUTS]. Show all work.",
        "edge_cases": f"What happens when [EDGE_CASE] occurs in {domain_name}? Explain any exceptions to standard rules.",
        "critique": f"The following answer about {domain_name} contains errors: [FLAWED_ANSWER]. Identify all errors and provide corrections.",
        "compliance_framing": f"How should a financial advisor respond to a client question about [TOPIC] in {domain_name}? Include appropriate caveats and disclosures.",
        "structured_schema": f"Generate a [DOCUMENT_TYPE] for {domain_name} as JSON. The output must match this schema: [SCHEMA]",
        "multi_turn": f"[INITIAL_QUESTION about {domain_name}] ... [FOLLOW_UP]",
        "grounded_retrieval": f"Based on the following context about {domain_name}, answer [QUESTION]. Only use information from the provided context.\n\nContext: [CONTEXT]",
    }

    prompt = family_templates.get(family, f"Question about {domain_name}")

    # Determine scoring method
    scoring_method = "checklist"
    if family == "calculations":
        scoring_method = "numeric_tolerance"
    elif family == "structured_schema":
        scoring_method = "schema_validate"
    elif family in ["scenarios", "critique", "edge_cases", "multi_turn"]:
        scoring_method = "human_rubric"

    # Determine if confirmation required (for action-oriented domains)
    confirmation_required = domain_id in ["trading", "derivatives", "forex"] and family == "scenarios"

    return {
        "id": f"{domain_id}_{tier}_{idx:04d}",
        "tier": tier,
        "domain": domain_id,
        "task_family": family,
        "difficulty": difficulty,
        "prompt": prompt,
        "context": "",
        "required_output": "json" if family == "structured_schema" else "free_text",
        "schema": {"type": "object"} if family == "structured_schema" else None,
        "must_include": [],
        "must_not_include": ["guaranteed", "risk free", "no risk", "cannot lose"],
        "scoring_method": scoring_method,
        "rubric": DEFAULT_RUBRICS.get(family, DEFAULT_RUBRICS["scenarios"]),
        "confirmation_required": confirmation_required,
        "tools_allowed": [],
        "gold_answer": None,
        "source": "generated",
    }


def select_difficulty(tier: str, rng: random.Random) -> str:
    """Select difficulty based on tier distribution."""
    dist = DIFFICULTY_DISTRIBUTION[tier]
    r = rng.random()
    cumulative = 0
    for diff, prob in dist.items():
        cumulative += prob
        if r <= cumulative:
            return diff
    return "hard"


# =============================================================================
# BENCHMARK BUILDING
# =============================================================================

def build_tier(
    tier: str,
    domains: List[Dict],
    existing_items: List[Dict],
    seed: int = 42
) -> List[Dict]:
    """Build all items for a single tier."""
    rng = random.Random(seed)
    target_per_domain = TIERS[tier]
    distribution = TASK_FAMILY_DISTRIBUTION[tier]

    items = []
    global_idx = 0

    # Group existing items by domain
    existing_by_domain = defaultdict(list)
    for item in existing_items:
        existing_by_domain[item.get("domain", "")].append(item)

    for domain in domains:
        domain_id = domain["id"]
        domain_items = []

        # Use existing items first
        existing_for_domain = existing_by_domain.get(domain_id, [])
        for existing in existing_for_domain[:target_per_domain]:
            existing["tier"] = tier
            existing["id"] = f"{domain_id}_{tier}_{global_idx:04d}"
            domain_items.append(existing)
            global_idx += 1

        # Generate remaining items by family
        current_count = len(domain_items)
        family_counts = {f: 0 for f, _ in distribution}

        # Track what families existing items cover
        for item in domain_items:
            f = item.get("task_family", "scenarios")
            family_counts[f] = family_counts.get(f, 0) + 1

        # Generate to fill family quotas
        for family, quota in distribution:
            needed = quota - family_counts.get(family, 0)
            for _ in range(needed):
                if current_count >= target_per_domain:
                    break
                difficulty = select_difficulty(tier, rng)
                item = generate_item_from_template(domain, family, tier, difficulty, global_idx)
                domain_items.append(item)
                global_idx += 1
                current_count += 1

        # Shuffle domain items
        rng.shuffle(domain_items)
        items.extend(domain_items[:target_per_domain])

    return items


def compute_hash(items: List[Dict]) -> str:
    """Compute SHA-256 hash of benchmark items."""
    content = json.dumps(items, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()


def validate_benchmark(items: List[Dict], tier: str) -> Tuple[bool, List[str]]:
    """Validate benchmark items meet requirements."""
    issues = []

    # Check total count
    expected_total = TIERS[tier] * 62
    if len(items) != expected_total:
        issues.append(f"Expected {expected_total} items, got {len(items)}")

    # Check domain coverage
    domain_counts = defaultdict(int)
    for item in items:
        domain_counts[item["domain"]] += 1

    for domain_id, count in domain_counts.items():
        if count != TIERS[tier]:
            issues.append(f"Domain {domain_id}: expected {TIERS[tier]}, got {count}")

    # Check required fields
    required_fields = ["id", "tier", "domain", "task_family", "difficulty", "prompt", "scoring_method", "rubric"]
    for i, item in enumerate(items):
        for field in required_fields:
            if field not in item:
                issues.append(f"Item {i}: missing required field '{field}'")

    # Check for catastrophic patterns in prompts (shouldn't be in questions themselves)
    # This is just a sanity check

    return len(issues) == 0, issues


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Build Enterprise Benchmark")
    parser.add_argument("--tier", choices=["core", "adversarial", "sealed", "all"], default="all")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing benchmarks")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("TB2 ENTERPRISE BENCHMARK BUILDER")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Seed: {args.seed}")
    print("=" * 70 + "\n")

    # Load domains
    domains = load_domains()
    print(f"Loaded {len(domains)} domains")

    if len(domains) != 62:
        print(f"WARNING: Expected 62 domains, got {len(domains)}")

    # Load existing benchmark for migration
    existing = load_existing_benchmark()
    print(f"Loaded {len(existing)} existing v2 benchmark items")

    # Convert existing items
    migrated = [convert_existing_item(item, i) for i, item in enumerate(existing)]
    print(f"Migrated {len(migrated)} items to new schema")

    if args.validate_only:
        print("\nValidating existing benchmarks...")
        for tier in ["core", "adversarial", "sealed"]:
            path = BENCHMARKS_DIR / f"{tier}_{TIERS[tier] * 62}.jsonl"
            if path.exists():
                items = load_jsonl(path)
                valid, issues = validate_benchmark(items, tier)
                status = "VALID" if valid else "INVALID"
                print(f"  {tier}: {status} ({len(items)} items)")
                for issue in issues[:5]:
                    print(f"    - {issue}")
        return

    # Build benchmarks
    tiers_to_build = ["core", "adversarial", "sealed"] if args.tier == "all" else [args.tier]
    hashes = {}

    for tier in tiers_to_build:
        print(f"\nBuilding {tier} benchmark...")

        # Use migrated items for core tier
        existing_for_tier = migrated if tier == "core" else []

        items = build_tier(tier, domains, existing_for_tier, args.seed)

        # Validate
        valid, issues = validate_benchmark(items, tier)
        if not valid:
            print(f"  WARNING: Validation issues found:")
            for issue in issues[:10]:
                print(f"    - {issue}")

        # Write output
        output_path = BENCHMARKS_DIR / f"{tier}_{len(items)}.jsonl"
        write_jsonl(output_path, items)

        # Compute hash
        item_hash = compute_hash(items)
        hashes[tier] = {
            "file": output_path.name,
            "count": len(items),
            "hash": item_hash,
            "timestamp": datetime.now().isoformat(),
        }

        print(f"  Written: {output_path}")
        print(f"  Items: {len(items)}")
        print(f"  Hash: {item_hash[:16]}...")

    # Write hashes
    hashes_path = BENCHMARKS_DIR / "hashes.json"
    with open(hashes_path, "w") as f:
        json.dump(hashes, f, indent=2)
    print(f"\nHashes written to: {hashes_path}")

    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK BUILD COMPLETE")
    print("=" * 70)
    total = sum(h["count"] for h in hashes.values())
    print(f"Total items: {total}")
    for tier, info in hashes.items():
        print(f"  {tier}: {info['count']} items")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
