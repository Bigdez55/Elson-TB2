#!/usr/bin/env python3
"""
Elson TB2 - Book Ingestion Pipeline
Processes book content from the Elson FAN folder to generate Q&A pairs.

Supports:
1. Markdown files (.md)
2. Text files (.txt)
3. Word documents (.docx)
4. PDF files (.pdf) - requires pdfplumber

Target: Extract 50+ Q&A pairs per book/document
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import Counter

# Try to import optional dependencies
try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# 62-domain keywords for classification
DOMAIN_KEYWORDS = {
    "federal_income_tax": ["irs", "income tax", "1040", "deduction", "taxable income", "irc"],
    "state_local_tax": ["salt", "state tax", "property tax", "sales tax"],
    "international_tax": ["foreign tax", "transfer pricing", "fatca", "tax treaty", "pfic"],
    "estate_gift_tax": ["estate tax", "gift tax", "unified credit", "marital deduction"],
    "corporate_tax": ["corporate tax", "c corporation", "subchapter c", "consolidated"],
    "estate_planning": ["estate plan", "will", "trust", "beneficiary", "probate"],
    "trust_administration": ["trustee", "fiduciary", "trust accounting", "distribution"],
    "life_insurance": ["life insurance", "death benefit", "cash value", "premium"],
    "health_insurance": ["health insurance", "medicare", "medicaid", "aca"],
    "commercial_banking": ["commercial bank", "lending", "credit", "treasury"],
    "equities": ["stock", "equity", "shares", "dividend", "earnings"],
    "fixed_income": ["bond", "yield", "coupon", "maturity", "duration"],
    "derivatives": ["option", "future", "swap", "derivative", "strike"],
    "portfolio_construction": ["portfolio", "diversification", "allocation", "sharpe"],
    "risk_management": ["risk", "var", "volatility", "hedge", "exposure"],
    "quantitative_finance": ["quantitative", "stochastic", "model", "simulation"],
    "algorithmic_trading": ["algorithm", "trading", "backtest", "systematic"],
    "hft": ["high frequency", "latency", "market making", "colocation"],
    "securities_regulation": ["sec", "finra", "compliance", "regulation", "filing"],
    "aml_kyc": ["aml", "kyc", "money laundering", "suspicious activity"],
    "financial_planning": ["financial plan", "budget", "goals", "cash flow"],
    "retirement_planning": ["retirement", "401k", "ira", "pension", "rmd"],
    "family_office": ["family office", "governance", "wealth management"]
}

# Q&A generation templates based on content type
DEFINITION_TEMPLATES = [
    ("What is {term}?", "{definition}"),
    ("Define {term} in financial terms.", "{definition}"),
    ("Explain the concept of {term}.", "{definition}"),
]

PROCEDURE_TEMPLATES = [
    ("How do you {action}?", "{steps}"),
    ("What is the process for {action}?", "{steps}"),
    ("Describe the steps to {action}.", "{steps}"),
]

COMPARISON_TEMPLATES = [
    ("What is the difference between {item1} and {item2}?", "{comparison}"),
    ("Compare and contrast {item1} with {item2}.", "{comparison}"),
]

CALCULATION_TEMPLATES = [
    ("How do you calculate {metric}?", "{formula}"),
    ("What is the formula for {metric}?", "{formula}"),
]

EXAMPLE_TEMPLATES = [
    ("Provide an example of {concept}.", "{example}"),
    ("Give a practical example of {concept}.", "{example}"),
]


def generate_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()[:12]


def classify_content(text: str) -> str:
    """Classify content into a domain."""
    text_lower = text.lower()
    domain_scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            domain_scores[domain] = score

    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return "financial_planning"


def extract_definitions(text: str) -> List[Tuple[str, str]]:
    """Extract term definitions from text."""
    definitions = []

    # Pattern: Term - definition or Term: definition
    patterns = [
        r'(?:^|\n)([A-Z][a-zA-Z\s]+)[\s]*[-:–][\s]*([^.]+\.)',
        r'(?:^|\n)\*\*([^*]+)\*\*[\s]*[-:–]?[\s]*([^.]+\.)',
        r'"([^"]+)"[\s]+(?:is|means|refers to)[\s]+([^.]+\.)',
        r'([A-Z][a-zA-Z\s]+)[\s]+is[\s]+(?:defined as|known as)[\s]+([^.]+\.)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for term, definition in matches:
            term = term.strip()
            definition = definition.strip()
            if 3 < len(term) < 50 and len(definition) > 20:
                definitions.append((term, definition))

    return definitions[:50]  # Limit to prevent explosion


def extract_numbered_lists(text: str) -> List[Tuple[str, str]]:
    """Extract numbered procedures/steps from text."""
    procedures = []

    # Find sections with numbered items
    sections = re.split(r'\n(?=(?:Steps|Process|Procedure|How to|To \w+):)', text, flags=re.IGNORECASE)

    for section in sections:
        # Extract the header
        header_match = re.match(r'^([^\n:]+):', section)
        if not header_match:
            continue

        header = header_match.group(1).strip()

        # Extract numbered items
        items = re.findall(r'\d+[.)]\s*([^\n]+)', section)
        if len(items) >= 2:
            steps_text = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items[:10]))
            procedures.append((header, steps_text))

    return procedures


def extract_bullet_points(text: str) -> List[Tuple[str, str]]:
    """Extract bullet point content with headers."""
    results = []

    # Split by headers
    sections = re.split(r'\n(?=#{1,4}\s+)', text)

    for section in sections:
        # Extract header
        header_match = re.match(r'^#{1,4}\s+(.+)', section)
        if not header_match:
            continue

        header = header_match.group(1).strip()

        # Extract bullet points
        bullets = re.findall(r'[-*•]\s+([^\n]+)', section)
        if len(bullets) >= 2:
            content = "\n".join(f"- {b}" for b in bullets[:10])
            results.append((header, content))

    return results


def extract_tables(text: str) -> List[Dict[str, Any]]:
    """Extract markdown tables from text."""
    tables = []

    # Find markdown tables
    table_pattern = r'\|(.+\|)+\n\|[-:\s|]+\|\n(\|.+\|[\n]?)+'
    matches = re.finditer(table_pattern, text)

    for match in matches:
        table_text = match.group(0)
        rows = [row.strip() for row in table_text.split('\n') if row.strip() and not row.startswith('|---')]

        if len(rows) >= 2:
            headers = [h.strip() for h in rows[0].split('|') if h.strip()]
            data_rows = []
            for row in rows[1:]:
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if len(cells) == len(headers):
                    data_rows.append(dict(zip(headers, cells)))

            if data_rows:
                tables.append({
                    "headers": headers,
                    "rows": data_rows
                })

    return tables


def extract_code_examples(text: str) -> List[Tuple[str, str]]:
    """Extract code blocks with context."""
    examples = []

    # Find code blocks with preceding context
    pattern = r'([^\n]+)\n+```(?:\w+)?\n([^`]+)```'
    matches = re.finditer(pattern, text)

    for match in matches:
        context = match.group(1).strip()
        code = match.group(2).strip()
        if len(context) > 10 and len(code) > 20:
            examples.append((context, code))

    return examples


def generate_qa_from_definitions(definitions: List[Tuple[str, str]], source: str, domain: str) -> List[Dict[str, Any]]:
    """Generate Q&A pairs from definitions."""
    pairs = []

    for term, definition in definitions:
        for q_template, a_template in DEFINITION_TEMPLATES[:2]:  # Use 2 templates per definition
            question = q_template.format(term=term)
            answer = a_template.format(definition=definition)

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": domain,
                "source": f"book_ingestion_{source}",
                "extraction_type": "definition",
                "hash": generate_hash(question + answer)
            })

    return pairs


def generate_qa_from_procedures(procedures: List[Tuple[str, str]], source: str, domain: str) -> List[Dict[str, Any]]:
    """Generate Q&A pairs from procedures."""
    pairs = []

    for header, steps in procedures:
        # Clean the header for use in question
        action = header.lower().replace("steps to", "").replace("how to", "").replace("process for", "").strip()

        for q_template, a_template in PROCEDURE_TEMPLATES[:2]:
            question = q_template.format(action=action)
            answer = a_template.format(steps=steps)

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": domain,
                "source": f"book_ingestion_{source}",
                "extraction_type": "procedure",
                "hash": generate_hash(question + answer)
            })

    return pairs


def generate_qa_from_sections(sections: List[Tuple[str, str]], source: str, domain: str) -> List[Dict[str, Any]]:
    """Generate Q&A pairs from content sections."""
    pairs = []

    for header, content in sections:
        # Generate explanation question
        question = f"Explain {header}."
        answer = f"**{header}**\n\n{content}"

        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "category": domain,
            "source": f"book_ingestion_{source}",
            "extraction_type": "section",
            "hash": generate_hash(question + answer)
        })

        # Generate "what" question
        question2 = f"What are the key points about {header.lower()}?"
        pairs.append({
            "instruction": question2,
            "input": "",
            "output": answer,
            "category": domain,
            "source": f"book_ingestion_{source}",
            "extraction_type": "section",
            "hash": generate_hash(question2 + answer)
        })

    return pairs


def generate_qa_from_tables(tables: List[Dict[str, Any]], source: str, domain: str) -> List[Dict[str, Any]]:
    """Generate Q&A pairs from tables."""
    pairs = []

    for table in tables:
        headers = table["headers"]
        rows = table["rows"]

        if len(rows) < 2:
            continue

        # Generate comparison questions from rows
        if len(headers) >= 2:
            first_col = headers[0]
            for row in rows[:5]:  # Limit to 5 rows
                item = row.get(first_col, "")
                if not item:
                    continue

                # Generate "what is" question
                details = ", ".join(f"{k}: {v}" for k, v in row.items() if k != first_col and v)
                if details:
                    question = f"What are the characteristics of {item}?"
                    answer = f"**{item}**\n\n{details}"

                    pairs.append({
                        "instruction": question,
                        "input": "",
                        "output": answer,
                        "category": domain,
                        "source": f"book_ingestion_{source}",
                        "extraction_type": "table",
                        "hash": generate_hash(question + answer)
                    })

    return pairs


def read_markdown_file(file_path: Path) -> str:
    """Read a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def read_text_file(file_path: Path) -> str:
    """Read a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def read_docx_file(file_path: Path) -> str:
    """Read a Word document."""
    if not HAS_DOCX:
        print(f"  Skipping {file_path}: python-docx not installed")
        return ""

    try:
        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def read_pdf_file(file_path: Path) -> str:
    """Read a PDF file."""
    if not HAS_PDF:
        print(f"  Skipping {file_path}: pdfplumber not installed")
        return ""

    try:
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:100]:  # Limit to first 100 pages
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def process_document(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single document and extract Q&A pairs."""
    suffix = file_path.suffix.lower()
    source_name = file_path.stem[:30]  # Truncate long names

    # Read content based on file type
    if suffix == '.md':
        content = read_markdown_file(file_path)
    elif suffix == '.txt':
        content = read_text_file(file_path)
    elif suffix == '.docx':
        content = read_docx_file(file_path)
    elif suffix == '.pdf':
        content = read_pdf_file(file_path)
    else:
        return []

    if not content or len(content) < 100:
        return []

    # Classify the content
    domain = classify_content(content)

    # Extract different content types
    definitions = extract_definitions(content)
    procedures = extract_numbered_lists(content)
    sections = extract_bullet_points(content)
    tables = extract_tables(content)

    # Generate Q&A pairs
    all_pairs = []
    all_pairs.extend(generate_qa_from_definitions(definitions, source_name, domain))
    all_pairs.extend(generate_qa_from_procedures(procedures, source_name, domain))
    all_pairs.extend(generate_qa_from_sections(sections, source_name, domain))
    all_pairs.extend(generate_qa_from_tables(tables, source_name, domain))

    return all_pairs


def ingest_books(
    input_dir: str,
    output_path: str,
    extensions: List[str] = ['.md', '.txt', '.docx', '.pdf']
) -> Dict[str, Any]:
    """
    Ingest all book/document content from a directory.

    Args:
        input_dir: Directory containing documents
        output_path: Output JSON file path
        extensions: File extensions to process

    Returns:
        Ingestion statistics
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    print(f"Ingesting documents from: {input_dir}")
    print(f"Looking for extensions: {extensions}")

    # Find all matching files
    all_files = []
    for ext in extensions:
        all_files.extend(input_dir.rglob(f"*{ext}"))

    print(f"Found {len(all_files)} files to process")

    all_pairs = []
    seen_hashes = set()
    file_stats = {}
    domain_counts = Counter()

    for i, file_path in enumerate(all_files):
        print(f"  [{i + 1}/{len(all_files)}] Processing: {file_path.name}")

        pairs = process_document(file_path)

        # Deduplicate
        new_pairs = []
        for pair in pairs:
            if pair["hash"] not in seen_hashes:
                new_pairs.append(pair)
                seen_hashes.add(pair["hash"])
                domain_counts[pair["category"]] += 1

        all_pairs.extend(new_pairs)
        file_stats[file_path.name] = len(new_pairs)

        if new_pairs:
            print(f"    Extracted {len(new_pairs)} Q&A pairs")

    print(f"\nTotal unique Q&A pairs: {len(all_pairs)}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_pairs, f, indent=2, ensure_ascii=False)
    print(f"Saved to: {output_path}")

    # Also save JSONL
    jsonl_path = str(output_path).replace('.json', '.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')

    # Calculate statistics
    stats = {
        "timestamp": datetime.now().isoformat(),
        "input_directory": str(input_dir),
        "files_processed": len(all_files),
        "total_pairs": len(all_pairs),
        "pairs_per_file": {k: v for k, v in sorted(file_stats.items(), key=lambda x: -x[1])[:20]},
        "domain_distribution": dict(domain_counts.most_common()),
        "extraction_types": dict(Counter(p.get("extraction_type", "unknown") for p in all_pairs))
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

    parser = argparse.ArgumentParser(description="Ingest books and documents for Elson TB2 training")
    parser.add_argument("--input-dir", "-i",
                        default="Elson FAN",
                        help="Input directory containing documents")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/book_qa_pairs.json",
                        help="Output JSON file")
    parser.add_argument("--extensions", nargs="+",
                        default=[".md", ".txt"],
                        help="File extensions to process")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    input_dir = project_root / args.input_dir
    output_path = project_root / args.output

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return

    stats = ingest_books(
        str(input_dir),
        str(output_path),
        extensions=args.extensions
    )

    # Print summary
    print("\n" + "=" * 60)
    print("BOOK INGESTION SUMMARY")
    print("=" * 60)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Total Q&A pairs: {stats['total_pairs']}")
    print(f"Avg pairs/file: {stats['total_pairs'] / max(stats['files_processed'], 1):.1f}")
    print("\nTop files by pairs:")
    for fname, count in list(stats['pairs_per_file'].items())[:5]:
        print(f"  {fname}: {count}")
    print("\nDomain distribution:")
    for domain, count in list(stats['domain_distribution'].items())[:10]:
        print(f"  {domain}: {count}")
    print("\nExtraction types:")
    for ext_type, count in stats['extraction_types'].items():
        print(f"  {ext_type}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
