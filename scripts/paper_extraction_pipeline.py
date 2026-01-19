#!/usr/bin/env python3
"""
Elson TB2 - Academic Paper Extraction Pipeline
Extracts Q&A pairs from academic paper references and citations in the codebase.

Sources:
1. Citations in strategic documents (Building AGI_ASI, Trading Knowledge, etc.)
2. arXiv references
3. Journal article references
4. Book chapter references

Target: 20+ Q&A pairs per cited paper
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

# Academic paper templates by type
PAPER_TEMPLATES = {
    "methodology": [
        ("What is the main contribution of {title}?", "{contribution}"),
        ("Describe the methodology in {title}.", "{methodology}"),
        ("What problem does {title} address?", "{problem}"),
        ("What are the key findings of {title}?", "{findings}"),
    ],
    "application": [
        ("How can {title} be applied in practice?", "{application}"),
        ("What are the practical implications of {title}?", "{implications}"),
        ("How does {title} improve upon existing methods?", "{improvement}"),
    ],
    "theory": [
        ("What is the theoretical framework of {title}?", "{framework}"),
        ("Explain the mathematical foundation of {title}.", "{math}"),
        ("What assumptions does {title} make?", "{assumptions}"),
    ]
}

# Known seminal papers with detailed Q&A
SEMINAL_PAPERS = {
    "volatility_is_rough": {
        "title": "Volatility is Rough",
        "authors": "Gatheral, Jaisson, Rosenbaum",
        "year": "2018",
        "journal": "Quantitative Finance",
        "domain": "quantitative_finance",
        "qa_pairs": [
            {
                "instruction": "What is the main finding of 'Volatility is Rough' by Gatheral et al.?",
                "output": "The paper demonstrates that log-volatility behaves as fractional Brownian motion with Hurst parameter H ≈ 0.1, much smaller than 0.5. This 'rough' behavior explains many empirical properties of volatility including the term structure of implied volatility, volatility persistence, and the leverage effect. The rough volatility framework provides a more accurate model than traditional stochastic volatility models."
            },
            {
                "instruction": "What is the Hurst parameter in rough volatility models?",
                "output": "The Hurst parameter H characterizes the roughness of paths in fractional Brownian motion. In rough volatility models, H ≈ 0.1, indicating very rough (irregular) paths. When H = 0.5, we have standard Brownian motion. H < 0.5 indicates rougher-than-Brownian paths with antipersistent increments. The low Hurst parameter in volatility explains why realized volatility exhibits such erratic short-term behavior while still showing long-range dependence."
            },
            {
                "instruction": "How does rough volatility improve option pricing?",
                "output": "Rough volatility models better capture the term structure of at-the-money implied volatility skew. Traditional models like Heston struggle to jointly fit short-term and long-term skews. Rough models naturally produce the power-law decay of ATM skew observed in markets. They also provide a unified framework for pricing both vanilla and exotic options with consistent volatility dynamics across all maturities."
            },
            {
                "instruction": "What is fractional Brownian motion in the context of volatility modeling?",
                "output": "Fractional Brownian motion (fBm) is a generalization of Brownian motion characterized by the Hurst parameter H. Unlike standard Brownian motion where increments are independent, fBm increments are correlated. For H < 0.5 (rough regime), past positive increments make future negative increments more likely, creating rough, irregular paths. In volatility modeling, log-volatility is modeled as fBm with H ≈ 0.1, explaining the fractal-like behavior of volatility time series."
            }
        ]
    },
    "deep_hedging": {
        "title": "Deep Hedging",
        "authors": "Buehler, Gonon, Teichmann, Wood",
        "year": "2019",
        "journal": "Quantitative Finance",
        "domain": "derivatives",
        "qa_pairs": [
            {
                "instruction": "What is Deep Hedging and how does it differ from traditional hedging?",
                "output": "Deep Hedging uses neural networks to learn optimal hedging strategies directly from data, without assuming a specific model for the underlying dynamics. Unlike traditional delta hedging which relies on Black-Scholes assumptions, Deep Hedging can incorporate transaction costs, market frictions, and learn non-linear hedging strategies. The neural network optimizes a risk measure (like CVaR) over the P&L distribution of the hedged portfolio."
            },
            {
                "instruction": "How does Deep Hedging handle transaction costs?",
                "output": "Deep Hedging explicitly incorporates transaction costs into the optimization objective. The neural network learns to balance the trade-off between hedging accuracy and trading costs. This leads to more realistic hedging strategies that trade less frequently than delta hedging would suggest. The model can handle both proportional and fixed transaction costs, as well as bid-ask spreads and market impact."
            },
            {
                "instruction": "What risk measures are used in Deep Hedging?",
                "output": "Deep Hedging typically uses Conditional Value at Risk (CVaR) as the risk measure, which focuses on the tail of the P&L distribution. Unlike variance-based measures, CVaR directly addresses extreme losses. The neural network is trained to minimize CVaR of the hedged portfolio's P&L. Other convex risk measures can also be used, including Expected Shortfall and spectral risk measures."
            },
            {
                "instruction": "Explain the neural network architecture in Deep Hedging.",
                "output": "Deep Hedging uses a recurrent neural network (often LSTM) that takes market observables (prices, volatility, time to expiry) as input and outputs the optimal hedge ratio at each time step. The network is trained on simulated paths using stochastic gradient descent. The architecture allows the strategy to adapt based on the full history of observations, not just current state, enabling path-dependent hedging decisions."
            }
        ]
    },
    "almgren_chriss": {
        "title": "Optimal Execution of Portfolio Transactions",
        "authors": "Almgren, Chriss",
        "year": "2000",
        "journal": "Journal of Risk",
        "domain": "trade_execution",
        "qa_pairs": [
            {
                "instruction": "What is the Almgren-Chriss model for optimal execution?",
                "output": "The Almgren-Chriss model provides a framework for optimal trade execution that balances market impact costs against timing risk. It models temporary impact (instantaneous price impact that decays) and permanent impact (lasting price change from trading). The optimal strategy is a deterministic trade schedule that minimizes a risk-adjusted cost function combining expected cost and execution risk (variance of cost)."
            },
            {
                "instruction": "What is the difference between temporary and permanent market impact?",
                "output": "Temporary impact is the immediate price displacement caused by trading that decays over time as the order book refills. It's typically modeled as proportional to trade rate. Permanent impact is the lasting price change that persists after trading, reflecting information incorporated into prices. In Almgren-Chriss, temporary impact is linear in trade rate and permanent impact is linear in trade size."
            },
            {
                "instruction": "What is implementation shortfall in trade execution?",
                "output": "Implementation shortfall is the difference between the actual execution price and a benchmark price (typically the decision price when the trade was initiated). It captures all costs of execution including market impact, timing costs, and opportunity costs. The Almgren-Chriss framework minimizes expected implementation shortfall subject to a risk constraint on the variance of the shortfall."
            },
            {
                "instruction": "How does risk aversion affect the optimal execution strategy?",
                "output": "Higher risk aversion leads to more aggressive front-loading of trades to reduce exposure to price volatility, accepting higher impact costs for lower timing risk. Lower risk aversion allows for more patient execution over longer horizons, accepting higher timing risk for lower impact costs. The optimal trajectory interpolates between TWAP (minimum impact) and immediate execution (minimum timing risk) based on the risk aversion parameter."
            }
        ]
    },
    "avellaneda_stoikov": {
        "title": "High-frequency trading in a limit order book",
        "authors": "Avellaneda, Stoikov",
        "year": "2008",
        "journal": "Quantitative Finance",
        "domain": "hft",
        "qa_pairs": [
            {
                "instruction": "What is the Avellaneda-Stoikov market making model?",
                "output": "The Avellaneda-Stoikov model provides an optimal strategy for market makers in limit order book markets. It determines optimal bid and ask quotes based on inventory position, time horizon, and risk aversion. The model balances earning the bid-ask spread against inventory risk. Optimal quotes are skewed based on inventory: a long inventory leads to lower ask prices to encourage selling."
            },
            {
                "instruction": "How does inventory affect market maker quotes in the Avellaneda-Stoikov model?",
                "output": "Inventory creates risk for market makers who prefer to stay inventory-neutral. The model adjusts quotes asymmetrically based on inventory: when long, the market maker widens the bid and tightens the ask to encourage selling and discourage buying. The adjustment is linear in inventory and proportional to risk aversion and time remaining. This inventory-based skewing is known as 'leaning' the quotes."
            },
            {
                "instruction": "What is the indifference price in market making?",
                "output": "The indifference price is the mid-price at which the market maker is indifferent between holding inventory and being flat. It differs from the market mid-price based on the market maker's inventory and risk preferences. In Avellaneda-Stoikov, the indifference price is the mid-price minus (risk_aversion × variance × inventory × time_remaining). The bid and ask are then set symmetrically around this indifference price with a spread determined by fill probability."
            }
        ]
    },
    "double_ml": {
        "title": "Double/Debiased Machine Learning",
        "authors": "Chernozhukov, Chetverikov, Demirer, et al.",
        "year": "2018",
        "journal": "Econometrics Journal",
        "domain": "quantitative_finance",
        "qa_pairs": [
            {
                "instruction": "What is Double Machine Learning (DML)?",
                "output": "Double Machine Learning is a method for estimating causal parameters when using machine learning for nuisance parameter estimation. It combines two key ideas: (1) orthogonalization - constructing moment conditions that are insensitive to small errors in nuisance estimates, and (2) cross-fitting - using sample splitting to avoid overfitting bias. DML allows valid inference on treatment effects even when using complex ML methods for high-dimensional controls."
            },
            {
                "instruction": "Why is cross-fitting important in Double Machine Learning?",
                "output": "Cross-fitting addresses the bias that arises when the same data is used to estimate nuisance functions and the target parameter. The sample is split into K folds; nuisance functions are estimated on K-1 folds and predictions are made on the held-out fold. This prevents the nuisance estimator from 'overfitting' to the data used for final estimation. Cross-fitting ensures root-n consistency and valid inference even with slow-converging ML methods."
            },
            {
                "instruction": "How does DML differ from traditional regression adjustment?",
                "output": "Traditional regression adjustment with many controls can suffer from regularization bias - shrinkage in ML methods biases the treatment effect estimate. DML solves this by 'partialing out' the effect of controls from both treatment and outcome using ML, then regressing residuals. This orthogonalization makes the treatment effect estimate robust to first-stage ML errors, allowing the use of any ML method (LASSO, random forest, neural nets) without affecting inference."
            }
        ]
    },
    "mean_field_games": {
        "title": "Mean Field Games",
        "authors": "Lasry, Lions",
        "year": "2007",
        "journal": "Japanese Journal of Mathematics",
        "domain": "quantitative_finance",
        "qa_pairs": [
            {
                "instruction": "What are Mean Field Games and how do they apply to finance?",
                "output": "Mean Field Games (MFG) model strategic interactions among a large number of rational agents. Each agent optimizes against the aggregate distribution of all agents, and the equilibrium distribution is self-consistent. In finance, MFG applies to optimal execution (traders impact the same price), systemic risk (banks' actions affect each other), and market microstructure. The theory reduces complex multi-agent problems to tractable partial differential equations."
            },
            {
                "instruction": "How do Mean Field Games model optimal execution with many traders?",
                "output": "In MFG execution models, many traders simultaneously execute orders and affect the same price through aggregate market impact. Each trader optimizes against the expected price path, which depends on all traders' strategies. The Nash equilibrium strategy has each trader accounting for how their trading interacts with the aggregate. This leads to different optimal strategies than single-agent models - trading is less aggressive because everyone trades together."
            }
        ]
    }
}

# Additional paper references to extract from documents
PAPER_PATTERNS = [
    # arXiv pattern
    r'arXiv[:\s]+(\d{4}\.\d{4,5})',
    # DOI pattern
    r'doi[:\s]+([^\s]+)',
    # Standard citation
    r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?)\s*\((\d{4})\)',
    # Journal reference
    r'"([^"]+)"\s*,\s*([^,]+),\s*(\d{4})',
]


def generate_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()[:12]


def extract_paper_references(text: str) -> List[Dict[str, Any]]:
    """Extract paper references from text."""
    references = []
    seen = set()

    # Extract arXiv IDs
    arxiv_matches = re.findall(r'arXiv[:\s]+(\d{4}\.\d{4,5})', text, re.IGNORECASE)
    for arxiv_id in arxiv_matches:
        if arxiv_id not in seen:
            references.append({
                "type": "arxiv",
                "id": arxiv_id,
                "title": f"arXiv:{arxiv_id}"
            })
            seen.add(arxiv_id)

    # Extract author-year citations
    citation_matches = re.findall(
        r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?)\s*\((\d{4})\)',
        text
    )
    for author, year in citation_matches:
        key = f"{author}_{year}"
        if key not in seen:
            references.append({
                "type": "citation",
                "author": author,
                "year": year,
                "title": f"{author} ({year})"
            })
            seen.add(key)

    return references


def extract_paper_context(text: str, paper_title: str) -> str:
    """Extract context around a paper reference."""
    # Find sentences mentioning the paper
    sentences = re.split(r'[.!?]+', text)
    relevant = []

    for sent in sentences:
        if paper_title.lower() in sent.lower() or any(
            word.lower() in sent.lower()
            for word in paper_title.split()[:3]
        ):
            relevant.append(sent.strip())

    return " ".join(relevant[:3])


def generate_qa_from_context(paper: Dict[str, Any], context: str, domain: str) -> List[Dict[str, Any]]:
    """Generate Q&A pairs from paper context."""
    pairs = []
    title = paper.get("title", "")
    authors = paper.get("author", paper.get("authors", ""))
    year = paper.get("year", "")

    if not context or len(context) < 50:
        return pairs

    # Generate basic Q&A
    qa_templates = [
        (
            f"What is the contribution of {title}?",
            f"The paper '{title}' by {authors} ({year}) contributes to the field by: {context}"
        ),
        (
            f"Summarize the findings of {title}.",
            f"'{title}' ({year}): {context}"
        ),
    ]

    for question, answer in qa_templates:
        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "category": domain,
            "source": "paper_extraction",
            "paper_title": title,
            "hash": generate_hash(question + answer)
        })

    return pairs


def generate_domain_paper_qa(domain: str) -> List[Dict[str, Any]]:
    """Generate Q&A pairs about papers in a domain."""
    pairs = []

    domain_papers = {
        "quantitative_finance": [
            ("Stochastic Calculus for Finance", "Steven Shreve", "textbook"),
            ("Options, Futures, and Other Derivatives", "John Hull", "textbook"),
            ("The Volatility Surface", "Jim Gatheral", "textbook"),
            ("Advances in Financial Machine Learning", "Marcos Lopez de Prado", "book"),
        ],
        "hft": [
            ("Flash Boys", "Michael Lewis", "book"),
            ("Algorithmic and High-Frequency Trading", "Cartea, Jaimungal, Penalva", "textbook"),
            ("Market Microstructure Theory", "Maureen O'Hara", "textbook"),
            ("Trading and Exchanges", "Larry Harris", "textbook"),
        ],
        "derivatives": [
            ("Dynamic Hedging", "Nassim Taleb", "book"),
            ("Volatility Trading", "Euan Sinclair", "book"),
            ("Option Volatility and Pricing", "Sheldon Natenberg", "book"),
        ],
        "risk_management": [
            ("Value at Risk", "Philippe Jorion", "textbook"),
            ("Against the Gods", "Peter Bernstein", "book"),
            ("The Misbehavior of Markets", "Benoit Mandelbrot", "book"),
        ],
        "portfolio_construction": [
            ("Investments", "Bodie, Kane, Marcus", "textbook"),
            ("A Random Walk Down Wall Street", "Burton Malkiel", "book"),
            ("The Intelligent Investor", "Benjamin Graham", "book"),
        ]
    }

    papers = domain_papers.get(domain, [])
    for title, author, book_type in papers:
        pairs.append({
            "instruction": f"What is '{title}' by {author} about?",
            "input": "",
            "output": f"'{title}' by {author} is a foundational {book_type} in {domain.replace('_', ' ')}. It covers key concepts and provides essential knowledge for practitioners in the field. This work is widely referenced in academic and professional contexts.",
            "category": domain,
            "source": "paper_extraction",
            "paper_title": title,
            "hash": generate_hash(f"{title}_{author}")
        })

        pairs.append({
            "instruction": f"Why should I read '{title}'?",
            "input": "",
            "output": f"'{title}' by {author} is considered essential reading for professionals in {domain.replace('_', ' ')}. It provides comprehensive coverage of fundamental concepts and advanced techniques. The book is frequently cited in academic literature and used in professional training programs.",
            "category": domain,
            "source": "paper_extraction",
            "paper_title": title,
            "hash": generate_hash(f"why_{title}")
        })

    return pairs


def extract_papers_from_documents(
    input_dir: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Extract Q&A pairs from academic paper references in documents.

    Args:
        input_dir: Directory containing documents with paper references
        output_path: Output JSON file path

    Returns:
        Extraction statistics
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    print(f"Extracting paper references from: {input_dir}")

    all_pairs = []
    seen_hashes = set()
    paper_counts = Counter()
    domain_counts = Counter()

    # First, add seminal paper Q&A pairs
    print("\n1. Adding seminal paper Q&A pairs...")
    for paper_key, paper_data in SEMINAL_PAPERS.items():
        for qa in paper_data["qa_pairs"]:
            pair = {
                "instruction": qa["instruction"],
                "input": "",
                "output": qa["output"],
                "category": paper_data["domain"],
                "source": "paper_extraction_seminal",
                "paper_title": paper_data["title"],
                "authors": paper_data["authors"],
                "year": paper_data["year"],
                "hash": generate_hash(qa["instruction"] + qa["output"])
            }
            if pair["hash"] not in seen_hashes:
                all_pairs.append(pair)
                seen_hashes.add(pair["hash"])
                paper_counts[paper_data["title"]] += 1
                domain_counts[paper_data["domain"]] += 1

    print(f"   Added {len(all_pairs)} seminal paper Q&A pairs")

    # Add domain-specific paper Q&A
    print("\n2. Adding domain-specific paper Q&A...")
    domains = ["quantitative_finance", "hft", "derivatives", "risk_management", "portfolio_construction"]
    for domain in domains:
        domain_pairs = generate_domain_paper_qa(domain)
        for pair in domain_pairs:
            if pair["hash"] not in seen_hashes:
                all_pairs.append(pair)
                seen_hashes.add(pair["hash"])
                domain_counts[domain] += 1

    print(f"   Total pairs after domain papers: {len(all_pairs)}")

    # Process documents in the input directory
    print("\n3. Extracting from documents...")
    extensions = ['.md', '.txt']
    files = []
    for ext in extensions:
        files.extend(input_dir.rglob(f"*{ext}"))

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract paper references
            references = extract_paper_references(content)

            for ref in references:
                # Try to get context around the reference
                context = extract_paper_context(content, ref.get("title", ""))

                # Determine domain from content
                domain = "quantitative_finance"  # Default
                for d in domain_counts.keys():
                    if d in content.lower():
                        domain = d
                        break

                # Generate Q&A from context
                pairs = generate_qa_from_context(ref, context, domain)
                for pair in pairs:
                    if pair["hash"] not in seen_hashes:
                        all_pairs.append(pair)
                        seen_hashes.add(pair["hash"])
                        domain_counts[domain] += 1

        except Exception as e:
            print(f"   Error processing {file_path.name}: {e}")

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
        "total_pairs": len(all_pairs),
        "seminal_papers": len(SEMINAL_PAPERS),
        "domain_distribution": dict(domain_counts.most_common()),
        "top_papers": dict(paper_counts.most_common(10)),
        "sources": dict(Counter(p.get("source", "unknown") for p in all_pairs))
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

    parser = argparse.ArgumentParser(description="Extract Q&A from academic papers for Elson TB2")
    parser.add_argument("--input-dir", "-i",
                        default="Elson FAN",
                        help="Input directory containing documents with paper references")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/paper_qa_pairs.json",
                        help="Output JSON file")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    input_dir = project_root / args.input_dir
    output_path = project_root / args.output

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return

    stats = extract_papers_from_documents(
        str(input_dir),
        str(output_path)
    )

    # Print summary
    print("\n" + "=" * 60)
    print("PAPER EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total Q&A pairs: {stats['total_pairs']}")
    print(f"Seminal papers: {stats['seminal_papers']}")
    print("\nDomain distribution:")
    for domain, count in list(stats['domain_distribution'].items())[:10]:
        print(f"  {domain}: {count}")
    print("\nSources:")
    for source, count in stats['sources'].items():
        print(f"  {source}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
