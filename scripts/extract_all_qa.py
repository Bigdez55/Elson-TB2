#!/usr/bin/env python3
"""
Elson TB2 - Extract Q&A Pairs from All Strategic Documents
Parses markdown, text, and other documents to extract question-answer pairs.

Target documents:
- Building AGI_ASI Investment System.md
- Comprehensive Trading Knowledge Compilation.md
- EXHAUSTIVE EXPANSION PACK.txt
- INSTITUTIONAL-SCALE RESEARCH SOURCES.txt
- BLACKROCK & VANGUARD RIVALRY MASTER PLAN.txt
- LLM FINE-TUNING & RAG IMPLEMENTATION ROADMAP.txt
- FINANCIAL PROJECTIONS & INVESTOR PRESENTATION.txt
- ENTERPRISE API ARCHITECTURE & MICROSERVICES SPECIFICATION.txt
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Domain classification keywords
DOMAIN_KEYWORDS = {
    "high_frequency_trading": ["fpga", "latency", "nanosecond", "market making", "hft", "colocation", "kernel bypass"],
    "quantitative_finance": ["stochastic", "volatility", "pricing model", "black-scholes", "monte carlo", "heston", "rough volatility"],
    "algorithmic_trading": ["vwap", "twap", "execution algorithm", "almgren", "chriss", "market impact", "slippage"],
    "data_engineering": ["kdb+", "time-series", "tickerplant", "data lake", "streaming", "real-time"],
    "portfolio_management": ["asset allocation", "risk parity", "modern portfolio", "sharpe ratio", "optimization"],
    "risk_management": ["var", "value at risk", "stress test", "risk metrics", "exposure", "hedging"],
    "derivatives": ["options", "futures", "swaps", "greeks", "delta", "gamma", "vega", "exotic"],
    "market_microstructure": ["order book", "bid-ask", "liquidity", "price discovery", "market maker"],
    "compliance": ["regulatory", "sec", "finra", "aml", "kyc", "fiduciary", "compliance"],
    "tax": ["tax", "irs", "deduction", "estate tax", "gift tax", "capital gains"],
    "estate_planning": ["trust", "estate", "probate", "beneficiary", "inheritance", "will"],
    "retirement_planning": ["401k", "ira", "pension", "social security", "retirement", "rmd"],
    "insurance": ["insurance", "policy", "premium", "underwriting", "actuarial", "annuity"],
    "banking": ["bank", "lending", "credit", "mortgage", "loan", "deposit"],
    "investment_strategy": ["value investing", "growth", "momentum", "factor", "alpha", "beta"],
    "private_equity": ["private equity", "lbo", "buyout", "venture capital", "fund"],
    "ai_ml": ["machine learning", "deep learning", "neural network", "llm", "transformer", "nlp"],
    "infrastructure": ["aladdin", "charles river", "murex", "bloomberg", "platform", "architecture"],
    "general_finance": []  # Default category
}


def classify_domain(text: str) -> str:
    """Classify text into a domain based on keywords."""
    text_lower = text.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if not keywords:
            continue
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[domain] = score

    if scores:
        return max(scores, key=scores.get)
    return "general_finance"


def generate_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def extract_from_headers(content: str) -> List[Dict[str, Any]]:
    """Extract Q&A pairs from markdown headers and their content."""
    pairs = []

    # Match headers (##, ###, ####) and their content
    header_pattern = r'^(#{2,4})\s+(.+?)$'
    lines = content.split('\n')

    current_header = None
    current_content = []
    _current_level = 0  # noqa: F841 - kept for potential future use

    for line in lines:
        header_match = re.match(header_pattern, line)
        if header_match:
            # Save previous section if exists
            if current_header and current_content:
                content_text = '\n'.join(current_content).strip()
                if len(content_text) > 100:  # Minimum content length
                    # Create Q&A from header
                    question = f"What is {current_header}?"
                    if "how" in current_header.lower():
                        question = current_header + "?"
                    elif current_header.lower().startswith("the "):
                        question = f"Explain {current_header.lower()}."

                    pairs.append({
                        "instruction": question,
                        "input": "",
                        "output": content_text[:2000],  # Limit length
                        "category": classify_domain(current_header + " " + content_text),
                        "source": "header_extraction",
                        "original_header": current_header
                    })

            _current_level = len(header_match.group(1))  # noqa: F841 - kept for potential future use
            current_header = header_match.group(2).strip()
            current_content = []
        else:
            if current_header:
                current_content.append(line)

    # Don't forget the last section
    if current_header and current_content:
        content_text = '\n'.join(current_content).strip()
        if len(content_text) > 100:
            question = f"What is {current_header}?"
            pairs.append({
                "instruction": question,
                "input": "",
                "output": content_text[:2000],
                "category": classify_domain(current_header + " " + content_text),
                "source": "header_extraction",
                "original_header": current_header
            })

    return pairs


def extract_definitions(content: str) -> List[Dict[str, Any]]:
    """Extract definition-style Q&A pairs."""
    pairs = []

    # Pattern: Term: Definition or **Term**: Definition
    definition_patterns = [
        r'\*\*([^*]+)\*\*[:\s]+([^*\n]{50,500})',
        r'^([A-Z][a-zA-Z\s]+):\s+([^\n]{50,500})',
        r'-\s+\*\*([^*]+)\*\*[:\s]*([^\n]{30,500})'
    ]

    for pattern in definition_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            term = match.group(1).strip()
            definition = match.group(2).strip()

            if len(term) > 3 and len(definition) > 50:
                pairs.append({
                    "instruction": f"What is {term}?",
                    "input": "",
                    "output": definition,
                    "category": classify_domain(term + " " + definition),
                    "source": "definition_extraction"
                })

    return pairs


def extract_lists(content: str) -> List[Dict[str, Any]]:
    """Extract Q&A from numbered or bulleted lists with context."""
    pairs = []

    # Find sections with lists
    list_section_pattern = r'(?:^|\n)(#{2,4}[^\n]+)\n((?:(?:\d+\.|[-*])[^\n]+\n?)+)'
    matches = re.finditer(list_section_pattern, content)

    for match in matches:
        header = match.group(1).replace('#', '').strip()
        list_content = match.group(2).strip()

        if len(list_content) > 100:
            # Create a "what are the..." question
            question = f"What are the key points about {header.lower()}?"

            pairs.append({
                "instruction": question,
                "input": "",
                "output": list_content,
                "category": classify_domain(header + " " + list_content),
                "source": "list_extraction",
                "original_header": header
            })

    return pairs


def extract_code_blocks(content: str) -> List[Dict[str, Any]]:
    """Extract Q&A from code blocks with surrounding context."""
    pairs = []

    # Pattern for code blocks with context
    code_pattern = r'(?:^|\n)([^\n`]+)\n```(\w*)\n([\s\S]+?)```'
    matches = re.finditer(code_pattern, content)

    for match in matches:
        context = match.group(1).strip()
        language = match.group(2) or "code"
        code = match.group(3).strip()

        if len(code) > 20 and len(context) > 10:
            question = f"How do you implement {context.lower().rstrip(':').rstrip('.')}?"
            answer = f"Here's an example in {language}:\n\n```{language}\n{code}\n```"

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": classify_domain(context + " " + code),
                "source": "code_extraction",
                "language": language
            })

    return pairs


def extract_comparisons(content: str) -> List[Dict[str, Any]]:
    """Extract comparison-style content (vs, versus, compared to)."""
    pairs = []

    comparison_patterns = [
        r'([A-Za-z\s]+)\s+(?:vs\.?|versus|compared to)\s+([A-Za-z\s]+)[:\s]+([^\n]{50,500})',
        r'\*\*([^*]+)\s+(?:vs\.?|versus)\s+([^*]+)\*\*[:\s]*([^\n]{30,500})'
    ]

    for pattern in comparison_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            item_a = match.group(1).strip()
            item_b = match.group(2).strip()
            comparison = match.group(3).strip()

            if len(comparison) > 50:
                question = f"What is the difference between {item_a} and {item_b}?"
                pairs.append({
                    "instruction": question,
                    "input": "",
                    "output": comparison,
                    "category": classify_domain(item_a + " " + item_b + " " + comparison),
                    "source": "comparison_extraction"
                })

    return pairs


def extract_from_tables(content: str) -> List[Dict[str, Any]]:
    """Extract Q&A from markdown tables."""
    pairs = []

    # Find tables (rows with |)
    table_pattern = r'(?:^|\n)(#{2,4}[^\n]*)\n\n?\|([^\n]+)\|\n\|[-:\s|]+\|\n((?:\|[^\n]+\|\n?)+)'
    matches = re.finditer(table_pattern, content)

    for match in matches:
        header = match.group(1).replace('#', '').strip()
        columns = match.group(2)
        rows = match.group(3)

        table_content = f"| {columns} |\n|{'|'.join(['---' for _ in columns.split('|')])}|\n{rows}"

        question = f"What does the {header.lower()} table show?"
        pairs.append({
            "instruction": question,
            "input": "",
            "output": f"Here is the {header} information:\n\n{table_content}",
            "category": classify_domain(header + " " + table_content),
            "source": "table_extraction",
            "original_header": header
        })

    return pairs


def create_predefined_qa(doc_name: str, content: str) -> List[Dict[str, Any]]:
    """Create predefined high-quality Q&A pairs for specific documents."""
    pairs = []

    if "AGI_ASI" in doc_name or "Building" in doc_name:
        # Add specific Q&A for the AGI/ASI document
        predefined = [
            {
                "instruction": "What is FPGA acceleration in high-frequency trading?",
                "output": "FPGA (Field-Programmable Gate Array) acceleration implements trading logic directly in hardware, achieving message parsing latency of 20-30 nanoseconds. This is critical for HFT market making where deterministic, sub-microsecond execution is required. FPGAs handle FIX protocol parsing, order validation, and risk checks in a pipelined architecture.",
                "category": "high_frequency_trading"
            },
            {
                "instruction": "Explain kernel bypass networking for trading systems.",
                "output": "Kernel bypass networking eliminates OS overhead by allowing applications to directly access network hardware. Technologies like Solarflare ef_vi, OpenOnload, and DPDK bypass the kernel TCP/IP stack, reducing latency from microseconds to nanoseconds. This is essential for HFT systems where every nanosecond matters.",
                "category": "high_frequency_trading"
            },
            {
                "instruction": "What is kdb+ and why is it dominant in finance?",
                "output": "kdb+ is a column-oriented, in-memory time-series database using the q programming language. It dominates finance because: 1) Handles billions of rows in milliseconds, 2) Purpose-built for tick data and time-series analysis, 3) Integrated analytics language, 4) Used by major banks, hedge funds, and exchanges for real-time and historical market data.",
                "category": "data_engineering"
            },
            {
                "instruction": "What is Rough Volatility and why is it important?",
                "output": "Rough Volatility (RFSV) is a volatility modeling approach discovered by Gatheral, Bayer, and Friz showing that volatility exhibits roughness with Hurst parameter H ≈ 0.1, much rougher than Brownian motion. This explains the power-law behavior of the ATM volatility skew and provides better pricing for short-dated options than traditional Heston or local volatility models.",
                "category": "quantitative_finance"
            },
            {
                "instruction": "Explain Deep Hedging and how it differs from traditional hedging.",
                "output": "Deep Hedging, introduced by Buehler et al. (2018), uses neural networks to learn optimal hedging strategies directly from data, rather than relying on model-based Greeks. Unlike traditional delta hedging, it can: 1) Account for transaction costs, 2) Handle illiquid markets, 3) Optimize for specific risk measures, 4) Learn from market data without assuming a pricing model.",
                "category": "quantitative_finance"
            },
            {
                "instruction": "What is the Almgren-Chriss model for optimal execution?",
                "output": "The Almgren-Chriss model (2000) solves the optimal execution problem: how to liquidate a large position while minimizing market impact and timing risk. It balances permanent impact (proportional to trade rate), temporary impact (immediate price pressure), and volatility risk. The solution is a deterministic trading trajectory that minimizes expected cost plus variance penalty.",
                "category": "algorithmic_trading"
            }
        ]

        for qa in predefined:
            qa["source"] = "predefined_agi_asi"
            qa["input"] = ""
            pairs.append(qa)

    elif "Trading Knowledge" in doc_name or "Comprehensive" in doc_name:
        predefined = [
            {
                "instruction": "What are the major asset classes in financial markets?",
                "output": "Major asset classes include: 1) Equities (stocks, ETFs), 2) Fixed Income (government bonds, corporate bonds, MBS), 3) Cash and Money Markets, 4) Commodities (energy, metals, agriculture), 5) Real Estate (REITs, direct property), 6) Alternatives (private equity, hedge funds, infrastructure), 7) Derivatives (options, futures, swaps), 8) Digital Assets (cryptocurrencies, tokens).",
                "category": "investment_strategy"
            },
            {
                "instruction": "Explain the trade lifecycle from order to settlement.",
                "output": "The trade lifecycle: 1) Order Initiation - client places order, 2) Order Routing - sent to exchange/dark pool, 3) Order Matching - execution at best price, 4) Trade Confirmation - details sent to parties, 5) Clearing - CCP becomes counterparty, nets positions, 6) Settlement - securities and cash exchange (T+1 for US equities), 7) Reconciliation - positions matched with custodian.",
                "category": "market_microstructure"
            },
            {
                "instruction": "What is Statistical Arbitrage and how does it work?",
                "output": "Statistical Arbitrage (Stat Arb) exploits mean-reverting relationships between securities using quantitative models. Key components: 1) Universe selection (liquid stocks), 2) Factor/signal generation (momentum, value, etc.), 3) Portfolio construction (long-short, sector-neutral), 4) Risk management (factor exposure limits), 5) Execution (minimize market impact). Returns from capturing mispricings as prices revert to equilibrium.",
                "category": "quantitative_finance"
            },
            {
                "instruction": "What is the Kelly Criterion and why use fractional Kelly?",
                "output": "The Kelly Criterion (f* = μ/σ²) determines the optimal fraction of capital to bet to maximize geometric growth rate. It's derived from information theory. Practitioners use fractional Kelly (typically half-Kelly) because: 1) Estimation error in μ and σ, 2) Reduces drawdowns significantly, 3) Path dependency of wealth, 4) Psychological tolerance for volatility. Half-Kelly achieves 75% of growth with much lower variance.",
                "category": "risk_management"
            }
        ]

        for qa in predefined:
            qa["source"] = "predefined_trading_knowledge"
            qa["input"] = ""
            pairs.append(qa)

    return pairs


def extract_from_document(file_path: Path) -> List[Dict[str, Any]]:
    """Extract all Q&A pairs from a single document."""
    print(f"  Processing: {file_path.name}")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"    Error reading file: {e}")
        return []

    all_pairs = []

    # Apply all extraction methods
    all_pairs.extend(extract_from_headers(content))
    all_pairs.extend(extract_definitions(content))
    all_pairs.extend(extract_lists(content))
    all_pairs.extend(extract_code_blocks(content))
    all_pairs.extend(extract_comparisons(content))
    all_pairs.extend(extract_from_tables(content))
    all_pairs.extend(create_predefined_qa(file_path.name, content))

    # Add source file to all pairs
    for pair in all_pairs:
        pair["source_file"] = file_path.name
        pair["hash"] = generate_hash(pair.get("instruction", "") + pair.get("output", ""))

    print(f"    Extracted {len(all_pairs)} pairs")
    return all_pairs


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract Q&A pairs from Elson FAN documents")
    parser.add_argument("--input-dir", "-i",
                        default="Elson FAN",
                        help="Input directory containing strategic documents")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/strategic_qa_complete.json",
                        help="Output JSON file")
    parser.add_argument("--extensions", "-e", nargs="+",
                        default=[".md", ".txt"],
                        help="File extensions to process")

    args = parser.parse_args()

    # Resolve paths
    project_root = Path(__file__).parent.parent
    input_dir = project_root / args.input_dir
    output_path = project_root / args.output

    print(f"Extracting Q&A from documents in: {input_dir}")
    print(f"Looking for extensions: {args.extensions}")

    # Find all matching files
    all_files = []
    for ext in args.extensions:
        all_files.extend(input_dir.glob(f"*{ext}"))
        all_files.extend(input_dir.glob(f"**/*{ext}"))

    all_files = list(set(all_files))  # Remove duplicates
    print(f"Found {len(all_files)} files to process")

    # Extract from all files
    all_pairs = []
    seen_hashes = set()

    for file_path in all_files:
        pairs = extract_from_document(file_path)
        for pair in pairs:
            pair_hash = pair.get("hash", generate_hash(str(pair)))
            if pair_hash not in seen_hashes:
                all_pairs.append(pair)
                seen_hashes.add(pair_hash)

    print(f"\nTotal unique Q&A pairs extracted: {len(all_pairs)}")

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
    print(f"Also saved JSONL to: {jsonl_path}")

    # Print category distribution
    categories = {}
    for pair in all_pairs:
        cat = pair.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Save statistics
    stats = {
        "timestamp": datetime.now().isoformat(),
        "files_processed": len(all_files),
        "total_pairs": len(all_pairs),
        "category_distribution": categories,
        "source_files": [f.name for f in all_files]
    }

    stats_path = str(output_path).replace('.json', '_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_path}")


if __name__ == "__main__":
    main()
