#!/usr/bin/env python3
"""
Elson TB2 - Training Data Consolidation Script

Consolidates all training data sources into a unified dataset for fine-tuning:
- training_data_final.json (643 Q&A pairs)
- strategic_qa_pairs.json (205+ pairs from strategic docs)
- expansion_pack_v4.jsonl (140+ resource records)
- master_training_resources_categorized.csv (929 categorized URLs)

Outputs:
- consolidated_training_data.json (combined Q&A for fine-tuning)
- consolidated_training_data.jsonl (for streaming/incremental training)
- training_statistics.json (data quality metrics)

Usage:
    python scripts/consolidate_training_data.py
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import hashlib


def load_json(path: str) -> List[Dict]:
    """Load a JSON file."""
    if not os.path.exists(path):
        print(f"  Warning: File not found: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            # Handle benchmark format with metadata
            return data.get('test_cases', data.get('data', [data]))
        return data


def load_jsonl(path: str) -> List[Dict]:
    """Load a JSONL file."""
    if not os.path.exists(path):
        print(f"  Warning: File not found: {path}")
        return []
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def load_csv(path: str) -> List[Dict]:
    """Load a CSV file."""
    if not os.path.exists(path):
        print(f"  Warning: File not found: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def normalize_qa(record: Dict, source: str) -> Dict:
    """Normalize a Q&A record to standard format."""
    # Handle different field names
    instruction = record.get('instruction', record.get('question', record.get('input', '')))
    context = record.get('input', record.get('context', ''))
    output = record.get('output', record.get('answer', record.get('response', '')))
    category = record.get('category', 'general')

    return {
        'instruction': instruction.strip(),
        'input': context.strip(),
        'output': output.strip(),
        'category': category,
        'source': source,
        'hash': hashlib.md5(f"{instruction}{output}".encode()).hexdigest()[:12]
    }


def create_resource_qa(record: Dict) -> Dict:
    """Create a Q&A pair from a resource record."""
    title = record.get('title', '')
    domain = record.get('domain', 'General')
    subdomain = record.get('subdomain', '')
    url = record.get('url', '')
    notes = record.get('notes', '')
    organization = record.get('organization', '')

    if not title or not url:
        return None

    instruction = f"What is {title}?"

    output_parts = [f"**{title}**"]
    if organization:
        output_parts.append(f"\nProvided by: {organization}")
    if domain and subdomain:
        output_parts.append(f"\nCategory: {domain} - {subdomain}")
    if notes:
        output_parts.append(f"\n{notes}")
    output_parts.append(f"\n\nSource: {url}")

    return {
        'instruction': instruction,
        'input': '',
        'output': '\n'.join(output_parts),
        'category': domain.lower().replace(' ', '_') if domain else 'general',
        'source': 'resource_catalog',
        'hash': hashlib.md5(url.encode()).hexdigest()[:12]
    }


def deduplicate(records: List[Dict]) -> List[Dict]:
    """Remove duplicates based on hash."""
    seen: Set[str] = set()
    unique = []
    for record in records:
        h = record.get('hash', '')
        if h and h not in seen:
            seen.add(h)
            unique.append(record)
        elif not h:
            unique.append(record)
    return unique


def analyze_quality(records: List[Dict]) -> Dict:
    """Analyze data quality metrics."""
    stats = {
        'total_records': len(records),
        'by_source': defaultdict(int),
        'by_category': defaultdict(int),
        'avg_output_length': 0,
        'empty_outputs': 0,
        'short_outputs': 0,
        'long_outputs': 0
    }

    total_length = 0
    for record in records:
        stats['by_source'][record.get('source', 'unknown')] += 1
        stats['by_category'][record.get('category', 'unknown')] += 1

        output_len = len(record.get('output', ''))
        total_length += output_len

        if output_len == 0:
            stats['empty_outputs'] += 1
        elif output_len < 50:
            stats['short_outputs'] += 1
        elif output_len > 2000:
            stats['long_outputs'] += 1

    stats['avg_output_length'] = total_length / len(records) if records else 0
    stats['by_source'] = dict(stats['by_source'])
    stats['by_category'] = dict(stats['by_category'])

    return stats


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent
    training_path = base_path / "backend" / "training_data"
    fan_path = base_path / "Elson FAN"

    print("=" * 60)
    print("Elson TB2 - Training Data Consolidation")
    print("=" * 60)

    all_records: List[Dict] = []

    # Load existing training data
    print("\n1. Loading training_data_final.json...")
    final_data = load_json(str(training_path / "training_data_final.json"))
    for record in final_data:
        normalized = normalize_qa(record, 'training_data_final')
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(final_data)} records")

    # Load strategic Q&A pairs
    print("\n2. Loading strategic_qa_pairs.json...")
    strategic_data = load_json(str(training_path / "strategic_qa_pairs.json"))
    for record in strategic_data:
        normalized = normalize_qa(record, record.get('source', 'strategic_docs'))
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(strategic_data)} records")

    # Load expansion pack
    print("\n3. Loading expansion_pack_v4.jsonl...")
    expansion_data = load_jsonl(str(fan_path / "expansion_pack_v4.jsonl"))
    resource_qa_count = 0
    for record in expansion_data:
        qa = create_resource_qa(record)
        if qa:
            all_records.append(qa)
            resource_qa_count += 1
    print(f"   Loaded: {len(expansion_data)} records -> {resource_qa_count} Q&A pairs")

    # Load categorized resources (create Q&A pairs from high-value resources)
    print("\n4. Loading master_training_resources_categorized.csv...")
    categorized_data = load_csv(str(fan_path / "master_training_resources_categorized.csv"))
    resource_count = 0
    for record in categorized_data:
        # Only create Q&A for primary authority resources
        if record.get('authority_tier', '') == 'primary':
            qa = create_resource_qa(record)
            if qa:
                all_records.append(qa)
                resource_count += 1
    print(f"   Loaded: {len(categorized_data)} records -> {resource_count} primary resource Q&A pairs")

    # Deduplicate
    print("\n5. Deduplicating...")
    before_dedup = len(all_records)
    all_records = deduplicate(all_records)
    print(f"   Before: {before_dedup} -> After: {len(all_records)} (removed {before_dedup - len(all_records)} duplicates)")

    # Filter out empty/invalid records
    print("\n6. Filtering invalid records...")
    valid_records = [r for r in all_records if r.get('instruction') and r.get('output')]
    print(f"   Valid records: {len(valid_records)}")

    # Analyze quality
    print("\n7. Analyzing data quality...")
    stats = analyze_quality(valid_records)

    # Save consolidated data
    output_json = training_path / "consolidated_training_data.json"
    output_jsonl = training_path / "consolidated_training_data.jsonl"
    output_stats = training_path / "training_statistics.json"

    print(f"\n8. Saving outputs...")

    # JSON format
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)
    print(f"   Saved: {output_json}")

    # JSONL format
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for record in valid_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"   Saved: {output_jsonl}")

    # Statistics
    with open(output_stats, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"   Saved: {output_stats}")

    # Print summary
    print("\n" + "=" * 60)
    print("CONSOLIDATION SUMMARY")
    print("=" * 60)
    print(f"\nTotal Q&A pairs: {stats['total_records']}")
    print(f"Avg output length: {stats['avg_output_length']:.0f} chars")

    print("\nBy Source:")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")

    print("\nBy Category (top 10):")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {count}")

    print("\nQuality Metrics:")
    print(f"  Empty outputs: {stats['empty_outputs']}")
    print(f"  Short outputs (<50 chars): {stats['short_outputs']}")
    print(f"  Long outputs (>2000 chars): {stats['long_outputs']}")

    # Training data target
    current = stats['total_records']
    target = 1200
    gap = max(0, target - current)

    print(f"\n" + "=" * 60)
    print(f"TRAINING DATA STATUS")
    print(f"=" * 60)
    print(f"  Current: {current} Q&A pairs")
    print(f"  Target:  {target} Q&A pairs")
    print(f"  Gap:     {gap} pairs needed")

    if current >= target:
        print(f"\n  ✓ Training data target ACHIEVED!")
    else:
        print(f"\n  ⚠ Need {gap} more Q&A pairs to reach target.")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
