#!/usr/bin/env python3
"""
Elson TB2 - Merge All Training Data
Consolidates all training data sources into a single unified dataset.

Sources:
1. Original training data (training_data_final.json)
2. Strategic Q&A (strategic_qa_complete.json)
3. Augmented data (augmented_training_data.json)
4. Synthetic Q&A (synthetic_qa_pairs.json)
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime
from collections import Counter

# Standard schema for training data
STANDARD_SCHEMA = {
    "instruction": str,
    "input": str,
    "output": str,
    "category": str,
    "source": str
}


def generate_hash(text: str) -> str:
    """Generate a hash for deduplication."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()[:12]


def normalize_pair(pair: Dict[str, Any], source_name: str) -> Dict[str, Any]:
    """Normalize a Q&A pair to standard schema."""
    normalized = {
        "instruction": str(pair.get("instruction", pair.get("question", ""))).strip(),
        "input": str(pair.get("input", pair.get("context", ""))).strip(),
        "output": str(pair.get("output", pair.get("answer", pair.get("response", "")))).strip(),
        "category": str(pair.get("category", pair.get("domain", "general_finance"))).strip().lower(),
        "source": source_name
    }

    # Copy additional metadata if present
    for key in ["difficulty", "source_file", "original_hash", "hash"]:
        if key in pair:
            normalized[key] = pair[key]

    # Generate hash if not present
    if "hash" not in normalized:
        normalized["hash"] = generate_hash(normalized["instruction"] + normalized["output"])

    return normalized


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file (supports both array and JSONL formats)."""
    if not file_path.exists():
        print(f"  Warning: File not found: {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

            # Try to parse as JSON array
            if content.startswith('['):
                return json.loads(content)

            # Try to parse as JSONL
            data = []
            for line in content.split('\n'):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return data

    except Exception as e:
        print(f"  Error loading {file_path}: {e}")
        return []


def merge_training_data(
    sources: Dict[str, str],
    output_path: str,
    deduplicate: bool = True,
    balance_domains: bool = False,
    max_per_domain: int = None
) -> Dict[str, Any]:
    """
    Merge multiple training data sources into one.

    Args:
        sources: Dict mapping source name to file path
        output_path: Output JSON file path
        deduplicate: Whether to remove duplicates
        balance_domains: Whether to balance domain distribution
        max_per_domain: Maximum pairs per domain (if balancing)

    Returns:
        Merge statistics
    """
    print("Merging training data sources...")

    all_pairs = []
    seen_hashes: Set[str] = set()
    source_counts = {}

    # Load each source
    for source_name, file_path in sources.items():
        print(f"\n  Loading: {source_name} ({file_path})")

        path = Path(file_path)
        data = load_json_file(path)

        if not data:
            source_counts[source_name] = 0
            continue

        # Normalize and add pairs
        added = 0
        for pair in data:
            normalized = normalize_pair(pair, source_name)

            # Skip empty pairs
            if not normalized["instruction"] or not normalized["output"]:
                continue

            # Deduplicate
            if deduplicate:
                pair_hash = generate_hash(normalized["instruction"] + normalized["output"])
                if pair_hash in seen_hashes:
                    continue
                seen_hashes.add(pair_hash)
                normalized["hash"] = pair_hash

            all_pairs.append(normalized)
            added += 1

        source_counts[source_name] = added
        print(f"    Added {added} pairs (after deduplication)")

    print(f"\nTotal pairs before balancing: {len(all_pairs)}")

    # Balance domains if requested
    if balance_domains and max_per_domain:
        print(f"\nBalancing domains (max {max_per_domain} per domain)...")
        domain_pairs = {}
        for pair in all_pairs:
            domain = pair.get("category", "unknown")
            if domain not in domain_pairs:
                domain_pairs[domain] = []
            domain_pairs[domain].append(pair)

        balanced_pairs = []
        for domain, pairs in domain_pairs.items():
            if len(pairs) > max_per_domain:
                # Sample randomly to maintain diversity
                import random
                selected = random.sample(pairs, max_per_domain)
                balanced_pairs.extend(selected)
                print(f"    {domain}: {len(pairs)} -> {max_per_domain}")
            else:
                balanced_pairs.extend(pairs)

        all_pairs = balanced_pairs
        print(f"Total pairs after balancing: {len(all_pairs)}")

    # Calculate statistics
    category_counts = Counter(p.get("category", "unknown") for p in all_pairs)
    source_distribution = Counter(p.get("source", "unknown") for p in all_pairs)

    stats = {
        "timestamp": datetime.now().isoformat(),
        "total_pairs": len(all_pairs),
        "unique_pairs": len(seen_hashes) if deduplicate else len(all_pairs),
        "sources_loaded": source_counts,
        "category_distribution": dict(category_counts.most_common(50)),
        "source_distribution": dict(source_distribution),
        "num_categories": len(category_counts)
    }

    # Calculate average lengths
    if all_pairs:
        avg_instruction = sum(len(p["instruction"]) for p in all_pairs) / len(all_pairs)
        avg_output = sum(len(p["output"]) for p in all_pairs) / len(all_pairs)
        stats["avg_instruction_length"] = round(avg_instruction, 1)
        stats["avg_output_length"] = round(avg_output, 1)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save merged data
    print(f"\nSaving merged data to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_pairs, f, indent=2, ensure_ascii=False)

    # Also save JSONL version
    jsonl_path = str(output_path).replace('.json', '.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')
    print(f"Also saved JSONL to: {jsonl_path}")

    # Save Alpaca format (for training)
    alpaca_path = str(output_path).replace('.json', '_alpaca.json')
    alpaca_data = []
    for pair in all_pairs:
        alpaca_data.append({
            "instruction": pair["instruction"],
            "input": pair.get("input", ""),
            "output": pair["output"]
        })
    with open(alpaca_path, 'w', encoding='utf-8') as f:
        json.dump(alpaca_data, f, indent=2, ensure_ascii=False)
    print(f"Saved Alpaca format to: {alpaca_path}")

    # Save statistics
    stats_path = str(output_path).replace('.json', '_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_path}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Merge all Elson TB2 training data")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/final_training_data.json",
                        help="Output merged JSON file")
    parser.add_argument("--no-deduplicate", action="store_true",
                        help="Disable deduplication")
    parser.add_argument("--balance", action="store_true",
                        help="Balance domain distribution")
    parser.add_argument("--max-per-domain", type=int, default=5000,
                        help="Maximum pairs per domain when balancing")
    parser.add_argument("--sources", nargs="+",
                        help="Additional source files (format: name:path)")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    # Default sources
    sources = {
        "training_data_final": str(project_root / "backend/training_data/training_data_final.json"),
        "consolidated": str(project_root / "backend/training_data/consolidated_training_data.json"),
        "strategic_qa": str(project_root / "backend/training_data/strategic_qa_complete.json"),
        "augmented": str(project_root / "backend/training_data/augmented_training_data.json"),
        "synthetic": str(project_root / "backend/training_data/synthetic_qa_pairs.json"),
    }

    # Add additional sources from command line
    if args.sources:
        for source_spec in args.sources:
            if ':' in source_spec:
                name, path = source_spec.split(':', 1)
                sources[name] = path

    # Print sources
    print("Sources to merge:")
    for name, path in sources.items():
        exists = "✓" if Path(path).exists() else "✗"
        print(f"  [{exists}] {name}: {path}")

    # Merge
    output_path = project_root / args.output
    stats = merge_training_data(
        sources=sources,
        output_path=str(output_path),
        deduplicate=not args.no_deduplicate,
        balance_domains=args.balance,
        max_per_domain=args.max_per_domain if args.balance else None
    )

    # Print summary
    print("\n" + "=" * 60)
    print("MERGE SUMMARY")
    print("=" * 60)
    print(f"Total pairs: {stats['total_pairs']}")
    print(f"Unique pairs: {stats['unique_pairs']}")
    print(f"Categories: {stats['num_categories']}")
    print(f"Avg instruction length: {stats.get('avg_instruction_length', 0)}")
    print(f"Avg output length: {stats.get('avg_output_length', 0)}")
    print("\nSource contributions:")
    for source, count in stats['sources_loaded'].items():
        print(f"  {source}: {count}")
    print("\nTop categories:")
    for cat, count in list(stats['category_distribution'].items())[:10]:
        print(f"  {cat}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
