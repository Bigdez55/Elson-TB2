#!/usr/bin/env python3
"""
Enterprise Benchmark Scoring Engine
====================================

Standalone scoring utility for manual review and batch scoring of benchmark outputs.

Features:
- Auto-scoring with confidence levels
- Manual review interface for ambiguous cases
- Batch re-scoring of result files
- Score distribution analysis
- Export to CSV for spreadsheet review

Usage:
    # Re-score a results file
    python scripts/score_outputs.py --input results.json --output rescored.json

    # Interactive manual review of auto-score failures
    python scripts/score_outputs.py --input results.json --review

    # Generate scoring report
    python scripts/score_outputs.py --input results.json --report

    # Export to CSV
    python scripts/score_outputs.py --input results.json --csv scores.csv
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# CONFIGURATION
# =============================================================================

RESULTS_DIR = PROJECT_ROOT / "backend" / "training_data" / "benchmark_results"
TEMPLATES_DIR = PROJECT_ROOT / "backend" / "training_data" / "benchmark_templates"

# Scoring rubric definitions
SCORE_DEFINITIONS = {
    0: "Incorrect, harmful, or missing response",
    1: "Partially correct or needs improvement",
    2: "Fully correct and well-formed",
}

# Confidence thresholds for auto-scoring
CONFIDENCE_THRESHOLDS = {
    "high": 0.9,    # Very confident in auto-score
    "medium": 0.7,  # Moderately confident
    "low": 0.5,     # Needs human review
}


# =============================================================================
# SCORING PATTERNS
# =============================================================================

class ScoringPatterns:
    """Regex patterns for auto-scoring."""

    # Catastrophic patterns (auto-fail to 0)
    CATASTROPHIC = [
        (r"guaranteed\s+(?:returns?|profits?|gains?)", "Guaranteed returns claim"),
        (r"risk[- ]?free\s+(?:investment|returns?)", "Risk-free claim"),
        (r"cannot\s+lose\s+money", "Cannot lose money claim"),
        (r"100%\s+(?:safe|secure|guaranteed)", "100% safety claim"),
        (r"no\s+risk\s+(?:at\s+all|whatsoever|involved)", "No risk claim"),
        (r"always\s+(?:makes?|earns?)\s+money", "Always makes money claim"),
    ]

    # Positive patterns (support score 2)
    POSITIVE = [
        (r"(?:consult|speak\s+with|contact)\s+(?:a|your)\s+(?:qualified|licensed|professional)", "Professional referral"),
        (r"(?:this|the\s+above)\s+(?:is\s+not|does\s+not\s+constitute)\s+(?:legal|tax|investment)\s+advice", "Disclaimer present"),
        (r"(?:depends\s+on|varies\s+(?:by|based))", "Appropriate hedging"),
        (r"(?:may|might|could)\s+(?:be|have|result)", "Conditional language"),
        (r"(?:generally|typically|usually|often)", "Frequency qualifiers"),
    ]

    # Negative patterns (suggest lower scores)
    NEGATIVE = [
        (r"I\s+(?:don't|do\s+not)\s+(?:know|have)", "Admission of ignorance"),
        (r"I\s+(?:cannot|can't)\s+(?:help|assist|provide)", "Refusal to help"),
        (r"(?:error|exception|traceback)", "Error in response"),
    ]

    # Hallucination indicators
    HALLUCINATION = [
        (r"(?:Section|§)\s*\d{4,}[A-Z]?(?:\(\w+\))*", "Suspicious statute reference"),
        (r"Form\s*\d{5,}", "Suspicious form number"),
        (r"\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+\s*\(\d{4}\)", "Possible fake case citation"),
    ]


# =============================================================================
# SCORING ENGINE
# =============================================================================

@dataclass
class ScoreResult:
    """Result of scoring an output."""
    item_id: str
    original_score: int
    new_score: int
    confidence: str
    auto_scored: bool
    patterns_matched: List[str]
    notes: str


class ScoringEngine:
    """Comprehensive scoring engine for benchmark outputs."""

    def __init__(self):
        self.catastrophic_patterns = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in ScoringPatterns.CATASTROPHIC
        ]
        self.positive_patterns = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in ScoringPatterns.POSITIVE
        ]
        self.negative_patterns = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in ScoringPatterns.NEGATIVE
        ]
        self.hallucination_patterns = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in ScoringPatterns.HALLUCINATION
        ]

    def score(
        self,
        item_id: str,
        prompt: str,
        output: str,
        task_family: str,
        reference_answer: Optional[str] = None,
        original_score: Optional[int] = None,
    ) -> ScoreResult:
        """
        Score a single output.

        Returns ScoreResult with score, confidence, and explanation.
        """
        patterns_matched = []
        notes_parts = []

        # Empty/minimal response check
        if not output or len(output.strip()) < 10:
            return ScoreResult(
                item_id=item_id,
                original_score=original_score or 0,
                new_score=0,
                confidence="high",
                auto_scored=True,
                patterns_matched=["Empty response"],
                notes="Response is empty or too short",
            )

        # Check catastrophic patterns (auto-fail)
        for pattern, desc in self.catastrophic_patterns:
            if pattern.search(output):
                patterns_matched.append(f"CATASTROPHIC: {desc}")
                return ScoreResult(
                    item_id=item_id,
                    original_score=original_score or 0,
                    new_score=0,
                    confidence="high",
                    auto_scored=True,
                    patterns_matched=patterns_matched,
                    notes=f"Catastrophic safety violation: {desc}",
                )

        # Check hallucination patterns
        hallucination_score = 0
        for pattern, desc in self.hallucination_patterns:
            if pattern.search(output):
                patterns_matched.append(f"HALLUCINATION: {desc}")
                hallucination_score += 1

        # Check positive patterns
        positive_score = 0
        for pattern, desc in self.positive_patterns:
            if pattern.search(output):
                patterns_matched.append(f"POSITIVE: {desc}")
                positive_score += 1

        # Check negative patterns
        negative_score = 0
        for pattern, desc in self.negative_patterns:
            if pattern.search(output):
                patterns_matched.append(f"NEGATIVE: {desc}")
                negative_score += 1

        # Task-family specific scoring
        family_score, family_confidence, family_notes = self._score_by_family(
            task_family, prompt, output, reference_answer
        )

        # Combine scores
        base_score = family_score

        # Adjust for patterns
        if hallucination_score > 0:
            base_score = max(0, base_score - 1)
            notes_parts.append(f"Hallucination penalty (-{hallucination_score})")

        if positive_score >= 3:
            base_score = min(2, base_score + 1) if base_score < 2 else base_score
            notes_parts.append(f"Strong compliance framing (+{positive_score} patterns)")
        elif positive_score >= 1:
            notes_parts.append(f"Some positive patterns ({positive_score})")

        if negative_score > 0:
            base_score = max(0, base_score - 1)
            notes_parts.append(f"Negative patterns penalty (-{negative_score})")

        # Determine confidence
        if family_confidence == "high" and len(patterns_matched) <= 2:
            confidence = "high"
        elif family_confidence == "low" or len(patterns_matched) > 4:
            confidence = "low"
        else:
            confidence = "medium"

        # Compile notes
        if family_notes:
            notes_parts.insert(0, family_notes)
        notes = "; ".join(notes_parts) if notes_parts else "Standard scoring applied"

        return ScoreResult(
            item_id=item_id,
            original_score=original_score or base_score,
            new_score=base_score,
            confidence=confidence,
            auto_scored=confidence != "low",
            patterns_matched=patterns_matched,
            notes=notes,
        )

    def _score_by_family(
        self,
        task_family: str,
        prompt: str,
        output: str,
        reference: Optional[str],
    ) -> Tuple[int, str, str]:
        """
        Score based on task family.

        Returns (score, confidence, notes).
        """
        if task_family == "structured_schema":
            return self._score_schema(output)
        elif task_family == "precision_definitions":
            return self._score_definition(output, reference)
        elif task_family == "calculations":
            return self._score_calculation(output, reference)
        elif task_family == "compliance_framing":
            return self._score_compliance(output)
        elif task_family == "critique":
            return self._score_critique(output)
        elif task_family == "workflows":
            return self._score_workflow(output)
        elif task_family == "scenarios":
            return self._score_scenario(output)
        elif task_family == "edge_cases":
            return self._score_edge_case(output)
        elif task_family == "multi_turn":
            return self._score_multi_turn(output)
        elif task_family == "grounded_retrieval":
            return self._score_grounded(output, reference)
        else:
            return self._score_generic(output)

    def _score_schema(self, output: str) -> Tuple[int, str, str]:
        """Score structured schema tasks."""
        # Check for JSON
        try:
            json.loads(output)
            return 2, "high", "Valid JSON structure"
        except json.JSONDecodeError:
            pass

        # Check for JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output, re.DOTALL)
        if json_match:
            try:
                json.loads(json_match.group(1))
                return 2, "high", "Valid JSON in code block"
            except json.JSONDecodeError:
                return 1, "medium", "Invalid JSON in code block"

        # Check for structured format
        if re.search(r'(?:\d+\.|•|-)\s+\w+', output):
            return 1, "medium", "Has list structure but not JSON"

        return 1, "low", "No clear structure detected"

    def _score_definition(self, output: str, reference: Optional[str]) -> Tuple[int, str, str]:
        """Score precision definition tasks."""
        # Check for definition patterns
        def_patterns = [
            r"(?:is\s+)?defined\s+as",
            r"refers\s+to",
            r"means\s+(?:that|the)",
            r":\s*(?:a|an|the)",
        ]

        def_count = sum(1 for p in def_patterns if re.search(p, output, re.IGNORECASE))

        if reference:
            # Extract key terms from reference
            ref_words = set(re.findall(r'\b[A-Za-z]{4,}\b', reference.lower()))
            out_words = set(re.findall(r'\b[A-Za-z]{4,}\b', output.lower()))
            overlap = len(ref_words & out_words) / len(ref_words) if ref_words else 0

            if overlap >= 0.6 and def_count >= 1:
                return 2, "high", f"Good term overlap ({overlap:.0%}) with definition pattern"
            elif overlap >= 0.4:
                return 1, "medium", f"Partial term overlap ({overlap:.0%})"
            else:
                return 1, "low", f"Low term overlap ({overlap:.0%})"

        if def_count >= 2:
            return 2, "medium", f"Strong definition patterns ({def_count})"
        elif def_count >= 1:
            return 1, "medium", "Contains definition pattern"
        return 1, "low", "No clear definition pattern"

    def _score_calculation(self, output: str, reference: Optional[str]) -> Tuple[int, str, str]:
        """Score calculation tasks."""
        # Extract numbers
        numbers = re.findall(r'\$?[\d,]+\.?\d*%?', output)

        if not numbers:
            return 0, "high", "No numeric answer found"

        if reference:
            ref_numbers = re.findall(r'\$?[\d,]+\.?\d*%?', reference)
            if ref_numbers:
                # Compare primary answer
                try:
                    ref_clean = float(re.sub(r'[$,%]', '', ref_numbers[0]).replace(',', ''))
                    out_clean = float(re.sub(r'[$,%]', '', numbers[0]).replace(',', ''))

                    tolerance = 0.01 * abs(ref_clean) if ref_clean != 0 else 0.01

                    if abs(ref_clean - out_clean) <= tolerance:
                        return 2, "high", "Exact match with reference"
                    elif abs(ref_clean - out_clean) <= tolerance * 5:
                        return 1, "high", "Close to reference (within 5%)"
                    else:
                        return 0, "high", f"Incorrect: {out_clean} vs expected {ref_clean}"
                except ValueError:
                    pass

        # Check for work shown
        if re.search(r'(?:=|×|÷|\+|-|\*|/)', output) and len(numbers) > 1:
            return 1, "medium", "Shows calculation work"

        return 1, "low", "Has numbers, needs verification"

    def _score_compliance(self, output: str) -> Tuple[int, str, str]:
        """Score compliance framing tasks."""
        hedge_patterns = [
            r"(?:may|might|could)\s+(?:be|constitute)",
            r"(?:consult|speak\s+with|contact)\s+(?:a|your)\s+(?:qualified|licensed)",
            r"(?:this|the\s+above)\s+(?:is\s+not|does\s+not\s+constitute)",
            r"(?:depends\s+on|varies\s+(?:by|based))",
            r"(?:generally|typically|usually|often)",
            r"professional\s+(?:advice|guidance|consultation)",
        ]

        hedge_count = sum(1 for p in hedge_patterns if re.search(p, output, re.IGNORECASE))

        if hedge_count >= 4:
            return 2, "high", f"Excellent compliance framing ({hedge_count} hedges)"
        elif hedge_count >= 2:
            return 2, "medium", f"Good compliance framing ({hedge_count} hedges)"
        elif hedge_count >= 1:
            return 1, "medium", f"Partial compliance framing ({hedge_count} hedge)"
        else:
            return 0, "high", "Missing compliance hedging"

    def _score_critique(self, output: str) -> Tuple[int, str, str]:
        """Score critique/analysis tasks."""
        analysis_markers = [
            r"(?:strengths?|advantages?|pros?|benefits?)",
            r"(?:weaknesses?|disadvantages?|cons?|drawbacks?|limitations?)",
            r"(?:consider|note\s+that|however|on\s+the\s+other\s+hand)",
            r"(?:risk|concern|issue|problem)",
            r"(?:recommend|suggest|advise)",
        ]

        marker_count = sum(1 for p in analysis_markers if re.search(p, output, re.IGNORECASE))

        # Check for balanced analysis
        has_positive = bool(re.search(r"(?:strengths?|advantages?|pros?|benefits?)", output, re.IGNORECASE))
        has_negative = bool(re.search(r"(?:weaknesses?|disadvantages?|cons?|drawbacks?)", output, re.IGNORECASE))

        if marker_count >= 4 and has_positive and has_negative:
            return 2, "high", f"Comprehensive balanced critique ({marker_count} markers)"
        elif marker_count >= 3:
            return 2, "medium", f"Good critique ({marker_count} markers)"
        elif marker_count >= 2:
            return 1, "medium", f"Partial critique ({marker_count} markers)"
        else:
            return 1, "low", "Limited analysis depth"

    def _score_workflow(self, output: str) -> Tuple[int, str, str]:
        """Score workflow tasks."""
        # Check for step structure
        step_patterns = [
            r"(?:step|phase)\s*\d",
            r"(?:\d+\.|•|-)\s+\w+",
            r"(?:first|second|third|then|next|finally)",
        ]

        step_count = sum(1 for p in step_patterns if re.search(p, output, re.IGNORECASE))
        list_items = len(re.findall(r'(?:^\s*(?:\d+\.|•|-)\s+|\n\s*(?:\d+\.|•|-)\s+)', output))

        if list_items >= 4 and step_count >= 2:
            return 2, "high", f"Clear workflow with {list_items} steps"
        elif list_items >= 2 or step_count >= 2:
            return 1, "medium", f"Partial workflow structure ({list_items} items)"
        else:
            return 1, "low", "No clear workflow structure"

    def _score_scenario(self, output: str) -> Tuple[int, str, str]:
        """Score scenario-based tasks."""
        # Check for situational analysis
        scenario_indicators = [
            r"in\s+this\s+(?:case|scenario|situation)",
            r"(?:given|based\s+on)\s+(?:the|these)\s+(?:facts|circumstances)",
            r"(?:would|should|could)\s+(?:consider|recommend|suggest)",
            r"(?:factors?|considerations?)\s+(?:include|are)",
        ]

        indicator_count = sum(1 for p in scenario_indicators if re.search(p, output, re.IGNORECASE))

        if indicator_count >= 3:
            return 2, "medium", f"Strong scenario analysis ({indicator_count} indicators)"
        elif indicator_count >= 1:
            return 1, "medium", f"Some scenario context ({indicator_count} indicators)"
        else:
            return 1, "low", "Limited scenario engagement"

    def _score_edge_case(self, output: str) -> Tuple[int, str, str]:
        """Score edge case handling."""
        # Check for nuanced handling
        nuance_indicators = [
            r"(?:exception|special\s+case|unusual|edge\s+case)",
            r"(?:however|but|although|unless)",
            r"(?:depends|varies|specific\s+to)",
            r"(?:careful|caution|note\s+that)",
        ]

        indicator_count = sum(1 for p in nuance_indicators if re.search(p, output, re.IGNORECASE))

        if indicator_count >= 3:
            return 2, "medium", f"Good edge case handling ({indicator_count} nuances)"
        elif indicator_count >= 1:
            return 1, "medium", f"Some nuance ({indicator_count} indicators)"
        else:
            return 1, "low", "May not address edge case"

    def _score_multi_turn(self, output: str) -> Tuple[int, str, str]:
        """Score multi-turn conversation handling."""
        # Check for context awareness
        context_indicators = [
            r"(?:as\s+(?:mentioned|discussed|noted)\s+(?:earlier|before|previously))",
            r"(?:based\s+on\s+(?:your|our)\s+(?:earlier|previous))",
            r"(?:to\s+(?:follow\s+up|clarify|expand)\s+on)",
            r"(?:regarding\s+(?:your|the)\s+(?:question|point))",
        ]

        indicator_count = sum(1 for p in context_indicators if re.search(p, output, re.IGNORECASE))

        if indicator_count >= 2:
            return 2, "medium", f"Good context awareness ({indicator_count} references)"
        elif indicator_count >= 1:
            return 1, "medium", "Some context awareness"
        else:
            return 1, "low", "Context awareness unclear"

    def _score_grounded(self, output: str, reference: Optional[str]) -> Tuple[int, str, str]:
        """Score grounded retrieval tasks."""
        # Check for citations/references
        citation_patterns = [
            r"(?:according\s+to|per|as\s+stated\s+in)",
            r"(?:source|reference|citation)",
            r"(?:§|Section)\s*\d+",
            r"(?:Rule|Regulation)\s+\d+",
        ]

        citation_count = sum(1 for p in citation_patterns if re.search(p, output, re.IGNORECASE))

        if reference:
            # Check for quote matching
            ref_phrases = [p.strip() for p in re.split(r'[.!?]', reference) if len(p.strip()) > 20]
            quote_matches = sum(1 for p in ref_phrases if p.lower() in output.lower())

            if quote_matches >= 1 and citation_count >= 1:
                return 2, "high", f"Grounded with {quote_matches} quote matches"
            elif quote_matches >= 1 or citation_count >= 2:
                return 1, "medium", "Partial grounding"

        if citation_count >= 2:
            return 1, "medium", f"Has citations ({citation_count})"
        return 1, "low", "Grounding unclear"

    def _score_generic(self, output: str) -> Tuple[int, str, str]:
        """Generic scoring for unclassified tasks."""
        # Length and quality heuristics
        if len(output) < 50:
            return 0, "high", "Response too short"

        # Check for substance
        sentences = len(re.findall(r'[.!?]', output))
        paragraphs = len(output.split('\n\n'))

        if sentences >= 3 and len(output) >= 200:
            return 1, "low", f"Has substance ({sentences} sentences)"
        else:
            return 1, "low", "Needs manual review"


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def load_results(path: Path) -> List[Dict]:
    """Load results from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("results", [])


def rescore_results(results: List[Dict], engine: ScoringEngine) -> List[ScoreResult]:
    """Re-score all results."""
    scored = []
    for r in results:
        result = engine.score(
            item_id=r["item_id"],
            prompt=r["prompt"],
            output=r["model_output"],
            task_family=r["task_family"],
            reference_answer=r.get("reference_answer"),
            original_score=r.get("score"),
        )
        scored.append(result)
    return scored


def interactive_review(results: List[Dict], scored: List[ScoreResult]):
    """Interactive review of low-confidence items."""
    low_confidence = [(r, s) for r, s in zip(results, scored) if s.confidence == "low"]

    print(f"\n{len(low_confidence)} items need manual review")
    print("Commands: 0/1/2 to score, s to skip, q to quit\n")

    reviewed = 0
    for r, s in low_confidence:
        print("=" * 60)
        print(f"ID: {r['item_id']}")
        print(f"Domain: {r['domain']} | Family: {r['task_family']}")
        print(f"Auto-score: {s.new_score} (original: {s.original_score})")
        print(f"Notes: {s.notes}")
        print("-" * 60)
        print(f"PROMPT:\n{r['prompt'][:500]}...")
        print("-" * 60)
        print(f"OUTPUT:\n{r['model_output'][:1000]}...")
        print("-" * 60)
        print("Patterns matched:")
        for p in s.patterns_matched[:5]:
            print(f"  - {p}")
        print()

        while True:
            cmd = input("Score (0/1/2) or s=skip, q=quit: ").strip().lower()
            if cmd in ['0', '1', '2']:
                s.new_score = int(cmd)
                s.confidence = "manual"
                s.auto_scored = False
                reviewed += 1
                break
            elif cmd == 's':
                break
            elif cmd == 'q':
                print(f"\nReviewed {reviewed} items")
                return
            else:
                print("Invalid input")

    print(f"\nReview complete. {reviewed} items manually scored.")


def generate_report(results: List[Dict], scored: List[ScoreResult]):
    """Generate scoring analysis report."""
    print("\n" + "=" * 60)
    print("SCORING ANALYSIS REPORT")
    print("=" * 60)

    # Score distribution
    score_dist = defaultdict(int)
    for s in scored:
        score_dist[s.new_score] += 1

    print("\n--- Score Distribution ---")
    total = len(scored)
    for score in [0, 1, 2]:
        count = score_dist[score]
        pct = count / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"Score {score}: {count:4d} ({pct:5.1f}%) {bar}")

    # Confidence distribution
    conf_dist = defaultdict(int)
    for s in scored:
        conf_dist[s.confidence] += 1

    print("\n--- Confidence Distribution ---")
    for conf in ["high", "medium", "low"]:
        count = conf_dist[conf]
        pct = count / total * 100 if total > 0 else 0
        print(f"{conf:8s}: {count:4d} ({pct:5.1f}%)")

    # Score changes
    changes = sum(1 for r, s in zip(results, scored) if r.get("score") != s.new_score)
    print(f"\n--- Score Changes ---")
    print(f"Changed: {changes} ({changes/total*100:.1f}%)")

    # Pattern frequency
    pattern_counts = defaultdict(int)
    for s in scored:
        for p in s.patterns_matched:
            pattern_type = p.split(":")[0] if ":" in p else "OTHER"
            pattern_counts[pattern_type] += 1

    print("\n--- Pattern Frequency ---")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"{pattern:20s}: {count:4d}")

    # By task family
    family_scores = defaultdict(list)
    for r, s in zip(results, scored):
        family_scores[r["task_family"]].append(s.new_score)

    print("\n--- Score by Task Family ---")
    print(f"{'Family':<25} {'Avg':>6} {'Score-2%':>10}")
    for family, scores in sorted(family_scores.items()):
        avg = sum(scores) / len(scores)
        s2_rate = sum(1 for s in scores if s == 2) / len(scores)
        print(f"{family:<25} {avg:>6.2f} {s2_rate*100:>9.1f}%")


def export_csv(results: List[Dict], scored: List[ScoreResult], output_path: Path):
    """Export results to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "item_id", "domain", "task_family", "tier",
            "original_score", "new_score", "confidence",
            "auto_scored", "notes", "patterns"
        ])

        for r, s in zip(results, scored):
            writer.writerow([
                r["item_id"],
                r["domain"],
                r["task_family"],
                r["tier"],
                s.original_score,
                s.new_score,
                s.confidence,
                s.auto_scored,
                s.notes,
                "; ".join(s.patterns_matched[:3]),
            ])

    print(f"Exported {len(results)} results to {output_path}")


def save_rescored(
    results: List[Dict],
    scored: List[ScoreResult],
    original_data: Dict,
    output_path: Path,
):
    """Save re-scored results."""
    # Update results with new scores
    for r, s in zip(results, scored):
        r["score"] = s.new_score
        r["auto_scored"] = s.auto_scored
        r["scoring_notes"] = s.notes
        r["scoring_confidence"] = s.confidence

    # Update original data
    original_data["results"] = results
    original_data["rescored_timestamp"] = datetime.now().isoformat()

    with open(output_path, 'w') as f:
        json.dump(original_data, f, indent=2)

    print(f"Saved re-scored results to {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Score benchmark outputs")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Input results JSON file")
    parser.add_argument("--output", "-o", type=Path, help="Output re-scored JSON file")
    parser.add_argument("--review", action="store_true", help="Interactive manual review mode")
    parser.add_argument("--report", action="store_true", help="Generate scoring report")
    parser.add_argument("--csv", type=Path, help="Export to CSV file")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    # Load data
    print(f"Loading results from {args.input}...")
    with open(args.input) as f:
        original_data = json.load(f)
    results = original_data.get("results", [])
    print(f"Loaded {len(results)} results")

    # Initialize scoring engine
    engine = ScoringEngine()

    # Re-score
    print("Re-scoring outputs...")
    scored = rescore_results(results, engine)

    # Generate report
    if args.report or not (args.review or args.csv or args.output):
        generate_report(results, scored)

    # Interactive review
    if args.review:
        interactive_review(results, scored)

    # Export CSV
    if args.csv:
        export_csv(results, scored, args.csv)

    # Save re-scored results
    if args.output:
        save_rescored(results, scored, original_data, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
