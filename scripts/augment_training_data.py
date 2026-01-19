#!/usr/bin/env python3
"""
Elson TB2 - Training Data Augmentation Pipeline
Scales training data from 950 pairs to 5,000+ using multiple augmentation techniques.

Techniques:
1. Paraphrasing (3x multiplier) - Synonym replacement, style swaps
2. Difficulty Scaling (3x multiplier) - Beginner/Intermediate/Advanced/Expert
3. Scenario Injection (2x multiplier) - Real-world context
4. Format Variation (2x multiplier) - Multi-turn, follow-up chains
5. Domain Cross-Referencing (2x multiplier) - Combined domain scenarios
"""

import json
import hashlib
import random
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Domain taxonomy for cross-referencing
DOMAINS = {
    "tax": ["federal_income_tax", "state_local_tax", "international_tax", "estate_gift_tax", "corporate_tax", "tax_controversy"],
    "estate": ["estate_planning", "trust_administration", "probate", "charitable_planning", "gst_planning"],
    "insurance": ["life_insurance", "health_insurance", "property_insurance", "casualty_insurance", "reinsurance", "annuities", "ltc", "actuarial"],
    "banking": ["commercial_banking", "consumer_lending", "mortgage_finance", "credit_risk", "treasury_management"],
    "securities": ["equities", "fixed_income", "derivatives", "commodities", "forex", "alternatives", "private_equity", "venture_capital", "hedge_funds", "crypto"],
    "portfolio": ["portfolio_construction", "risk_management", "asset_allocation", "performance_attribution", "factor_investing"],
    "quantitative": ["quantitative_finance", "algorithmic_trading", "hft", "market_microstructure", "trade_execution"],
    "corporate": ["mergers_acquisitions", "business_valuation", "restructuring", "capital_markets"],
    "regulatory": ["securities_regulation", "banking_regulation", "insurance_regulation", "aml_kyc", "erisa", "data_privacy"],
    "operations": ["prime_brokerage", "custodial", "fund_administration", "fintech"],
    "planning": ["financial_planning", "retirement_planning", "college_planning", "family_office"]
}

# Difficulty level templates
DIFFICULTY_TEMPLATES = {
    "beginner": {
        "prefix": ["What is ", "Can you explain ", "In simple terms, what is ", "What does ", "Help me understand "],
        "suffix": [" in basic terms?", " for someone new to finance?", " simply?", "?", " in plain language?"]
    },
    "intermediate": {
        "prefix": ["Explain the details of ", "What are the key aspects of ", "Describe ", "How does ", "What factors influence "],
        "suffix": ["?", " and its implications?", " with examples?", " in practice?", " from a technical perspective?"]
    },
    "advanced": {
        "prefix": ["Analyze the regulatory implications of ", "What are the edge cases in ", "Discuss the nuances of ", "How do professionals handle ", "What are the advanced considerations for "],
        "suffix": [" under current regulations?", " in complex scenarios?", " for high-net-worth clients?", " in institutional settings?", " with multiple jurisdictions?"]
    },
    "expert": {
        "prefix": ["From an institutional perspective, how would you structure ", "What are the cutting-edge approaches to ", "Discuss the interplay between ", "How do quantitative methods apply to ", "What are the systemic risks associated with "],
        "suffix": [" for a family office with $500M+ AUM?", " in the context of regulatory arbitrage?", " when dealing with cross-border complexities?", " using modern portfolio theory?", " in stressed market conditions?"]
    }
}

# Scenario injection templates
SCENARIO_TEMPLATES = [
    "A client aged {age} with {net_worth} in assets asks: {question}",
    "Consider a {client_type} who needs to know: {question}",
    "In the context of {scenario}, {question}",
    "A {profession} is advising a client who wants to understand: {question}",
    "During a {situation}, the question arises: {question}",
    "For a {family_situation}, explain: {question}",
    "When dealing with {asset_type}, {question}",
    "In a {market_condition} environment, {question}"
]

SCENARIO_VARIABLES = {
    "age": ["35", "45", "55", "65", "75", "retiring soon", "recently widowed"],
    "net_worth": ["$500K", "$1M", "$5M", "$10M", "$50M", "$100M+"],
    "client_type": ["high-net-worth individual", "business owner", "corporate executive", "professional athlete", "tech entrepreneur", "physician", "attorney", "retired executive"],
    "scenario": ["estate planning", "retirement transition", "business succession", "divorce proceedings", "inheritance receipt", "IPO liquidity event", "charitable giving planning"],
    "profession": ["CFP", "CPA", "estate attorney", "wealth advisor", "trust officer", "family office CIO"],
    "situation": ["annual review meeting", "life event consultation", "tax planning session", "investment committee meeting"],
    "family_situation": ["married couple with children", "blended family", "single parent", "multi-generational family", "family with special needs dependents"],
    "asset_type": ["concentrated stock position", "real estate portfolio", "private business", "retirement accounts", "trust assets", "inherited IRA"],
    "market_condition": ["volatile", "bull market", "bear market", "high inflation", "rising interest rate", "recessionary"]
}

# Paraphrase patterns
PARAPHRASE_PATTERNS = [
    (r"What is", ["Define", "Explain", "Describe", "What does", "Tell me about"]),
    (r"How do", ["What is the process for", "Explain how to", "What are the steps to", "Describe how to"]),
    (r"What are the", ["List the", "Identify the", "Name the", "Enumerate the"]),
    (r"Why is", ["What makes", "Explain why", "What is the reason"]),
    (r"When should", ["At what point should", "Under what circumstances should", "In what situations should"]),
    (r"Can you", ["Please", "Would you", "Could you"]),
    (r"benefits", ["advantages", "pros", "upsides", "positive aspects"]),
    (r"risks", ["dangers", "downsides", "potential issues", "concerns"]),
    (r"important", ["crucial", "essential", "critical", "vital"]),
    (r"strategies", ["approaches", "methods", "techniques", "tactics"])
]

# Format variation templates
FORMAT_TEMPLATES = {
    "multi_turn": [
        {"instruction": "First, explain the basics of {topic}.", "followup": "Now, how does this apply to {context}?"},
        {"instruction": "What is {topic}?", "followup": "And what are the key considerations for implementation?"},
        {"instruction": "Define {topic}.", "followup": "What are common mistakes to avoid?"}
    ],
    "problem_solving": [
        "A client has the following situation: {scenario}. What should they consider regarding {topic}?",
        "Given {constraints}, how would you approach {topic}?",
        "If a client wants to {goal}, what steps should they take regarding {topic}?"
    ],
    "comparison": [
        "Compare and contrast {topic_a} versus {topic_b} in the context of {context}.",
        "What are the differences between {topic_a} and {topic_b}?",
        "When would you recommend {topic_a} over {topic_b}?"
    ]
}


def generate_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def paraphrase_question(question: str) -> List[str]:
    """Generate paraphrased versions of a question."""
    paraphrases = [question]  # Include original

    for pattern, replacements in PARAPHRASE_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            for replacement in replacements:
                paraphrased = re.sub(pattern, replacement, question, flags=re.IGNORECASE)
                if paraphrased != question and paraphrased not in paraphrases:
                    paraphrases.append(paraphrased)

    # Style variations
    if not question.endswith("?"):
        paraphrases.append(question + "?")

    # Formal/informal variations
    formal_markers = ["please", "kindly", "would you"]
    if not any(marker in question.lower() for marker in formal_markers):
        paraphrases.append("Please explain: " + question)

    return paraphrases[:4]  # Limit to 4 variations


def scale_difficulty(qa_pair: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate difficulty-scaled versions of a Q&A pair."""
    scaled_pairs = []
    original_question = qa_pair.get("instruction", "")
    original_answer = qa_pair.get("output", "")
    category = qa_pair.get("category", "general_finance")

    # Extract the core topic from the question
    topic = original_question.replace("What is ", "").replace("?", "").strip()

    for difficulty, templates in DIFFICULTY_TEMPLATES.items():
        prefix = random.choice(templates["prefix"])
        suffix = random.choice(templates["suffix"])

        new_question = f"{prefix}{topic}{suffix}"

        # Adjust answer based on difficulty
        if difficulty == "beginner":
            # Simplify answer - take first few sentences
            sentences = original_answer.split(". ")
            new_answer = ". ".join(sentences[:3]) + "." if len(sentences) > 3 else original_answer
        elif difficulty == "expert":
            # Add complexity note
            new_answer = original_answer + "\n\nFor institutional applications, additional considerations include regulatory compliance, fiduciary duties, and systematic risk management frameworks."
        else:
            new_answer = original_answer

        scaled_pairs.append({
            "instruction": new_question,
            "input": qa_pair.get("input", ""),
            "output": new_answer,
            "category": category,
            "difficulty": difficulty,
            "source": "augmented_difficulty",
            "original_hash": generate_hash(original_question)
        })

    return scaled_pairs


def inject_scenario(qa_pair: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Inject real-world scenarios into Q&A pairs."""
    scenario_pairs = []
    original_question = qa_pair.get("instruction", "")
    original_answer = qa_pair.get("output", "")
    category = qa_pair.get("category", "general_finance")

    for _ in range(2):  # Generate 2 scenario variations
        template = random.choice(SCENARIO_TEMPLATES)

        # Fill in scenario variables
        scenario_question = template.format(
            question=original_question,
            age=random.choice(SCENARIO_VARIABLES["age"]),
            net_worth=random.choice(SCENARIO_VARIABLES["net_worth"]),
            client_type=random.choice(SCENARIO_VARIABLES["client_type"]),
            scenario=random.choice(SCENARIO_VARIABLES["scenario"]),
            profession=random.choice(SCENARIO_VARIABLES["profession"]),
            situation=random.choice(SCENARIO_VARIABLES["situation"]),
            family_situation=random.choice(SCENARIO_VARIABLES["family_situation"]),
            asset_type=random.choice(SCENARIO_VARIABLES["asset_type"]),
            market_condition=random.choice(SCENARIO_VARIABLES["market_condition"])
        )

        # Contextualize the answer
        scenario_answer = f"In this specific situation:\n\n{original_answer}\n\nAdditional considerations for this client profile may include their specific risk tolerance, time horizon, and overall financial goals."

        scenario_pairs.append({
            "instruction": scenario_question,
            "input": qa_pair.get("input", ""),
            "output": scenario_answer,
            "category": category,
            "source": "augmented_scenario",
            "original_hash": generate_hash(original_question)
        })

    return scenario_pairs


def create_format_variations(qa_pair: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create format variations (multi-turn, problem-solving, comparison)."""
    variations = []
    original_question = qa_pair.get("instruction", "")
    original_answer = qa_pair.get("output", "")
    category = qa_pair.get("category", "general_finance")

    # Extract topic for template filling
    topic = original_question.replace("What is ", "").replace("How do ", "").replace("?", "").strip()

    # Problem-solving format
    problem_template = random.choice(FORMAT_TEMPLATES["problem_solving"])
    problem_question = problem_template.format(
        topic=topic,
        scenario=random.choice(SCENARIO_VARIABLES["scenario"]),
        constraints="limited liquidity and tax efficiency requirements",
        goal="optimize their financial position"
    )

    variations.append({
        "instruction": problem_question,
        "input": "",
        "output": f"To address this situation effectively:\n\n{original_answer}\n\nKey steps include: 1) Assess current position, 2) Identify constraints and goals, 3) Develop actionable recommendations, 4) Monitor and adjust as needed.",
        "category": category,
        "source": "augmented_format",
        "format_type": "problem_solving",
        "original_hash": generate_hash(original_question)
    })

    return variations


def cross_reference_domains(qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create cross-domain Q&A pairs by combining related topics."""
    cross_ref_pairs = []

    # Group pairs by category
    by_category = {}
    for pair in qa_pairs:
        cat = pair.get("category", "general")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(pair)

    # Create cross-domain combinations
    cross_domain_templates = [
        "How does {topic_a} interact with {topic_b} in financial planning?",
        "What are the considerations when combining {topic_a} with {topic_b}?",
        "Explain the relationship between {topic_a} and {topic_b} for wealth management.",
        "When should a client consider both {topic_a} and {topic_b} together?"
    ]

    categories = list(by_category.keys())
    for i, cat_a in enumerate(categories):
        for cat_b in categories[i + 1:]:
            if by_category[cat_a] and by_category[cat_b]:
                pair_a = random.choice(by_category[cat_a])
                pair_b = random.choice(by_category[cat_b])

                topic_a = pair_a.get("instruction", "").replace("What is ", "").replace("?", "").strip()[:50]
                topic_b = pair_b.get("instruction", "").replace("What is ", "").replace("?", "").strip()[:50]

                template = random.choice(cross_domain_templates)
                question = template.format(topic_a=topic_a, topic_b=topic_b)

                answer = f"The intersection of {cat_a} and {cat_b} considerations:\n\n"
                answer += f"**{cat_a.replace('_', ' ').title()}:**\n{pair_a.get('output', '')[:500]}...\n\n"
                answer += f"**{cat_b.replace('_', ' ').title()}:**\n{pair_b.get('output', '')[:500]}...\n\n"
                answer += "When planning, these areas should be coordinated to ensure a comprehensive strategy."

                cross_ref_pairs.append({
                    "instruction": question,
                    "input": "",
                    "output": answer,
                    "category": f"{cat_a}_{cat_b}_crossref",
                    "source": "augmented_crossref",
                    "original_categories": [cat_a, cat_b]
                })

    return cross_ref_pairs[:100]  # Limit cross-references


def augment_dataset(input_path: str, output_path: str, target_multiplier: float = 5.5) -> Dict[str, Any]:
    """
    Main augmentation pipeline.

    Args:
        input_path: Path to input training data JSON
        output_path: Path to output augmented data JSON
        target_multiplier: Target multiplier for dataset size (default 5.5x)

    Returns:
        Statistics about the augmentation
    """
    print(f"Loading training data from {input_path}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    original_count = len(original_data)
    print(f"Loaded {original_count} original Q&A pairs")

    augmented_data = []
    seen_hashes = set()

    # Include original data
    for pair in original_data:
        pair_hash = generate_hash(pair.get("instruction", "") + pair.get("output", ""))
        if pair_hash not in seen_hashes:
            augmented_data.append(pair)
            seen_hashes.add(pair_hash)

    print("Applying augmentation techniques...")

    # 1. Paraphrasing (select subset for efficiency)
    print("  - Paraphrasing questions...")
    paraphrase_count = 0
    for pair in random.sample(original_data, min(len(original_data), 500)):
        paraphrases = paraphrase_question(pair.get("instruction", ""))
        for para in paraphrases[1:]:  # Skip original
            new_pair = pair.copy()
            new_pair["instruction"] = para
            new_pair["source"] = "augmented_paraphrase"
            pair_hash = generate_hash(para + new_pair.get("output", ""))
            if pair_hash not in seen_hashes:
                augmented_data.append(new_pair)
                seen_hashes.add(pair_hash)
                paraphrase_count += 1
    print(f"    Added {paraphrase_count} paraphrased pairs")

    # 2. Difficulty scaling
    print("  - Scaling difficulty levels...")
    difficulty_count = 0
    for pair in random.sample(original_data, min(len(original_data), 400)):
        scaled = scale_difficulty(pair)
        for sp in scaled:
            pair_hash = generate_hash(sp.get("instruction", "") + sp.get("output", ""))
            if pair_hash not in seen_hashes:
                augmented_data.append(sp)
                seen_hashes.add(pair_hash)
                difficulty_count += 1
    print(f"    Added {difficulty_count} difficulty-scaled pairs")

    # 3. Scenario injection
    print("  - Injecting scenarios...")
    scenario_count = 0
    for pair in random.sample(original_data, min(len(original_data), 400)):
        scenarios = inject_scenario(pair)
        for sp in scenarios:
            pair_hash = generate_hash(sp.get("instruction", "") + sp.get("output", ""))
            if pair_hash not in seen_hashes:
                augmented_data.append(sp)
                seen_hashes.add(pair_hash)
                scenario_count += 1
    print(f"    Added {scenario_count} scenario-injected pairs")

    # 4. Format variations
    print("  - Creating format variations...")
    format_count = 0
    for pair in random.sample(original_data, min(len(original_data), 300)):
        variations = create_format_variations(pair)
        for v in variations:
            pair_hash = generate_hash(v.get("instruction", "") + v.get("output", ""))
            if pair_hash not in seen_hashes:
                augmented_data.append(v)
                seen_hashes.add(pair_hash)
                format_count += 1
    print(f"    Added {format_count} format variation pairs")

    # 5. Cross-domain references
    print("  - Creating cross-domain references...")
    cross_refs = cross_reference_domains(original_data)
    cross_count = 0
    for cr in cross_refs:
        pair_hash = generate_hash(cr.get("instruction", "") + cr.get("output", ""))
        if pair_hash not in seen_hashes:
            augmented_data.append(cr)
            seen_hashes.add(pair_hash)
            cross_count += 1
    print(f"    Added {cross_count} cross-domain pairs")

    # Final statistics
    final_count = len(augmented_data)
    actual_multiplier = final_count / original_count

    print("\nAugmentation complete!")
    print(f"  Original pairs: {original_count}")
    print(f"  Augmented pairs: {final_count}")
    print(f"  Multiplier achieved: {actual_multiplier:.2f}x")

    # Save augmented data
    print(f"\nSaving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(augmented_data, f, indent=2, ensure_ascii=False)

    # Also save JSONL version
    jsonl_path = output_path.replace('.json', '.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for pair in augmented_data:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')
    print(f"Also saved JSONL version to {jsonl_path}")

    # Generate statistics report
    stats = {
        "timestamp": datetime.now().isoformat(),
        "original_count": original_count,
        "augmented_count": final_count,
        "multiplier": actual_multiplier,
        "techniques_applied": {
            "paraphrasing": paraphrase_count,
            "difficulty_scaling": difficulty_count,
            "scenario_injection": scenario_count,
            "format_variation": format_count,
            "cross_domain": cross_count
        },
        "category_distribution": {}
    }

    # Count by category
    for pair in augmented_data:
        cat = pair.get("category", "unknown")
        stats["category_distribution"][cat] = stats["category_distribution"].get(cat, 0) + 1

    stats_path = output_path.replace('.json', '_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to {stats_path}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Augment training data for Elson TB2")
    parser.add_argument("--input", "-i",
                        default="backend/training_data/consolidated_training_data.json",
                        help="Input training data JSON file")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/augmented_training_data.json",
                        help="Output augmented data JSON file")
    parser.add_argument("--multiplier", "-m", type=float, default=5.5,
                        help="Target multiplier for dataset size")

    args = parser.parse_args()

    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / args.input
    output_path = project_root / args.output

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stats = augment_dataset(str(input_path), str(output_path), args.multiplier)

    print("\n" + "=" * 50)
    print("AUGMENTATION SUMMARY")
    print("=" * 50)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Original: {stats['original_count']} pairs")
    print(f"Final:    {stats['augmented_count']} pairs")
    print(f"Multiplier: {stats['multiplier']:.2f}x")
    print("=" * 50)


if __name__ == "__main__":
    main()
