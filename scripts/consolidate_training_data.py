#!/usr/bin/env python3
"""
Elson TB2 - Training Data Consolidation Script (v2)

Consolidates ALL training data sources into a unified dataset for DoRA fine-tuning:

Existing Data:
- final_training_data.json (23,493 Q&A pairs)
- classified_training_data.json (classified by domain)

New Tool-First Training Data (Phases 1-3):
- tool_use_training_data.json (2,500 tool-use examples)
- insurance_training_data.json (10,000 insurance workflow examples)
- accounting_training_data.json (5,000 accounting/budgeting examples)

Outputs:
- consolidated_all.json (combined Q&A for fine-tuning)
- consolidated_all.jsonl (for streaming/incremental training)
- consolidated_all_alpaca.json (Alpaca format for compatibility)
- consolidated_all_stats.json (data quality metrics)

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


def categorize_example(record: Dict) -> str:
    """Categorize example by domain based on content."""
    # Check explicit category/domain
    if 'category' in record and record['category']:
        return record['category']
    if 'domain' in record and record['domain']:
        return record['domain']

    # Infer from content
    instruction = record.get('instruction', '').lower()
    output = record.get('output', '').lower()

    # Tool-use patterns
    if 'tool_call' in record or 'get_quote' in output or 'get_ratios' in output:
        return 'tool_use'

    # Insurance patterns
    insurance_terms = ['insurance', 'policy', 'premium', 'annuity', 'beneficiary',
                      'underwriting', 'claims', 'coverage', 'deductible']
    if any(term in instruction or term in output for term in insurance_terms):
        return 'insurance'

    # Accounting patterns
    accounting_terms = ['budget', 'ledger', 'bookkeeping', 'gnucash', 'reconcil',
                       'accounts payable', 'accounts receivable', 'cash flow']
    if any(term in instruction or term in output for term in accounting_terms):
        return 'accounting'

    # Tax patterns
    tax_terms = ['tax', 'irs', 'deduction', '401k', 'ira', 'capital gains']
    if any(term in instruction or term in output for term in tax_terms):
        return 'tax_education'

    # Portfolio/investment patterns
    portfolio_terms = ['portfolio', 'asset allocation', 'diversif', 'rebalance',
                      'sharpe ratio', 'beta', 'alpha']
    if any(term in instruction or term in output for term in portfolio_terms):
        return 'portfolio_management'

    # Market analysis patterns
    market_terms = ['stock', 'market', 'trading', 'technical analysis', 'fundamental']
    if any(term in instruction or term in output for term in market_terms):
        return 'market_analysis'

    return 'general_finance'


def to_alpaca_format(record: Dict) -> Dict:
    """Convert to Alpaca format for compatibility."""
    return {
        "instruction": record.get('instruction', ''),
        "input": record.get('input', ''),
        "output": record.get('output', ''),
    }


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent
    training_path = base_path / "backend" / "training_data"
    fan_path = base_path / "Elson FAN"

    print("=" * 60)
    print("Elson TB2 - Training Data Consolidation v2")
    print("Tool-First Architecture - Complete Dataset")
    print("=" * 60)

    all_records: List[Dict] = []
    source_counts = defaultdict(int)

    # =========================================================================
    # EXISTING TRAINING DATA
    # =========================================================================

    # Load final training data (largest existing source)
    print("\n[EXISTING] Loading final_training_data.json...")
    final_data = load_json(str(training_path / "final_training_data.json"))
    for record in final_data:
        normalized = normalize_qa(record, 'final_training_data')
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(final_data):,} records")
    source_counts['final_training_data'] = len(final_data)

    # Load strategic Q&A pairs
    print("\n[EXISTING] Loading strategic_qa_pairs.json...")
    strategic_data = load_json(str(training_path / "strategic_qa_pairs.json"))
    for record in strategic_data:
        normalized = normalize_qa(record, record.get('source', 'strategic_docs'))
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(strategic_data):,} records")
    source_counts['strategic_qa_pairs'] = len(strategic_data)

    # Load expansion pack (if exists)
    print("\n[EXISTING] Loading expansion_pack_v4.jsonl...")
    expansion_data = load_jsonl(str(fan_path / "expansion_pack_v4.jsonl"))
    resource_qa_count = 0
    for record in expansion_data:
        qa = create_resource_qa(record)
        if qa:
            all_records.append(qa)
            resource_qa_count += 1
    print(f"   Loaded: {len(expansion_data):,} records -> {resource_qa_count:,} Q&A pairs")
    source_counts['expansion_pack'] = resource_qa_count

    # =========================================================================
    # NEW TOOL-FIRST TRAINING DATA (Phases 1-3)
    # =========================================================================

    # Load tool-use training data (Phase 1c)
    print("\n[NEW] Loading tool_use_training_data.json (Phase 1c)...")
    tool_use_data = load_json(str(training_path / "tool_use_training_data.json"))
    for record in tool_use_data:
        normalized = normalize_qa(record, 'tool_use_training')
        normalized['category'] = 'tool_use'
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(tool_use_data):,} tool-use examples")
    source_counts['tool_use_training'] = len(tool_use_data)

    # Load insurance training data (Phase 2)
    print("\n[NEW] Loading insurance_training_data.json (Phase 2)...")
    insurance_data = load_json(str(training_path / "insurance_training_data.json"))
    for record in insurance_data:
        normalized = normalize_qa(record, 'insurance_training')
        normalized['category'] = 'insurance'
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(insurance_data):,} insurance examples")
    source_counts['insurance_training'] = len(insurance_data)

    # Load accounting training data (Phase 3)
    print("\n[NEW] Loading accounting_training_data.json (Phase 3)...")
    accounting_data = load_json(str(training_path / "accounting_training_data.json"))
    for record in accounting_data:
        normalized = normalize_qa(record, 'accounting_training')
        normalized['category'] = 'accounting'
        if normalized['output']:
            all_records.append(normalized)
    print(f"   Loaded: {len(accounting_data):,} accounting examples")
    source_counts['accounting_training'] = len(accounting_data)

    # =========================================================================
    # PROCESS AND DEDUPLICATE
    # =========================================================================

    # Deduplicate
    print("\n[PROCESSING] Deduplicating...")
    before_dedup = len(all_records)
    all_records = deduplicate(all_records)
    print(f"   Before: {before_dedup:,} -> After: {len(all_records):,} (removed {before_dedup - len(all_records):,} duplicates)")

    # Filter out empty/invalid records
    print("\n[PROCESSING] Filtering invalid records...")
    valid_records = [r for r in all_records if r.get('instruction') and r.get('output')]
    print(f"   Valid records: {len(valid_records):,}")

    # Categorize examples
    print("\n[PROCESSING] Categorizing examples...")
    for record in valid_records:
        if not record.get('category') or record['category'] == 'general':
            record['category'] = categorize_example(record)

    # Analyze quality
    print("\n[PROCESSING] Analyzing data quality...")
    stats = analyze_quality(valid_records)

    # =========================================================================
    # SAVE OUTPUTS
    # =========================================================================

    # Save consolidated data (new format)
    output_json = training_path / "consolidated_all.json"
    output_jsonl = training_path / "consolidated_all.jsonl"
    output_alpaca = training_path / "consolidated_all_alpaca.json"
    output_stats = training_path / "consolidated_all_stats.json"

    print(f"\n[SAVING] Saving outputs...")

    # JSON format
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)
    print(f"   Saved: {output_json}")

    # JSONL format
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for record in valid_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"   Saved: {output_jsonl}")

    # Alpaca format
    alpaca_records = [to_alpaca_format(r) for r in valid_records]
    with open(output_alpaca, 'w', encoding='utf-8') as f:
        json.dump(alpaca_records, f, indent=2, ensure_ascii=False)
    print(f"   Saved: {output_alpaca}")

    # Statistics (enhanced)
    stats['source_counts'] = dict(source_counts)
    stats['new_training_total'] = (
        source_counts.get('tool_use_training', 0) +
        source_counts.get('insurance_training', 0) +
        source_counts.get('accounting_training', 0)
    )
    with open(output_stats, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"   Saved: {output_stats}")

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print("\n" + "=" * 60)
    print("CONSOLIDATION SUMMARY")
    print("=" * 60)
    print(f"\nTotal Q&A pairs: {stats['total_records']:,}")
    print(f"Avg output length: {stats['avg_output_length']:.0f} chars")

    print("\nBy Source:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / stats['total_records'] if stats['total_records'] > 0 else 0
        print(f"  {source}: {count:,} ({pct:.1f}%)")

    print("\nBy Category (top 10):")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1])[:10]:
        pct = 100 * count / stats['total_records'] if stats['total_records'] > 0 else 0
        print(f"  {cat}: {count:,} ({pct:.1f}%)")

    print("\nQuality Metrics:")
    print(f"  Empty outputs: {stats['empty_outputs']:,}")
    print(f"  Short outputs (<50 chars): {stats['short_outputs']:,}")
    print(f"  Long outputs (>2000 chars): {stats['long_outputs']:,}")

    # New training data summary
    new_total = stats.get('new_training_total', 0)
    print(f"\n" + "=" * 60)
    print(f"TOOL-FIRST TRAINING DATA (NEW)")
    print(f"=" * 60)
    print(f"  Tool-use examples:   {source_counts.get('tool_use_training', 0):,}")
    print(f"  Insurance examples:  {source_counts.get('insurance_training', 0):,}")
    print(f"  Accounting examples: {source_counts.get('accounting_training', 0):,}")
    print(f"  --------------------------------")
    print(f"  NEW TOTAL:           {new_total:,}")

    print(f"\n" + "=" * 60)
    print(f"READY FOR DoRA FINE-TUNING")
    print(f"=" * 60)
    print(f"  Total training examples: {stats['total_records']:,}")
    print(f"  Output file: {output_jsonl}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
