#!/usr/bin/env python3
"""
Model Evaluation Runner for Elson Financial AI

Evaluates models against the locked benchmark and produces comparison reports.
Supports base model, LoRA, and DoRA variants.

Usage:
    python scripts/run_model_evaluation.py --model base
    python scripts/run_model_evaluation.py --model dora --adapter path/to/adapter
    python scripts/run_model_evaluation.py --compare base,lora,dora

Output:
    - Detailed scores by domain and question type
    - Compliance and adversarial test results
    - Model comparison if multiple models evaluated
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

# Paths
BENCHMARK_FILE = Path(__file__).parent.parent / "backend" / "training_data" / "evaluation_benchmark_v2.json"
RESULTS_DIR = Path(__file__).parent.parent / "backend" / "training_data" / "evaluation_results"


@dataclass
class QuestionResult:
    """Result for a single question"""
    question_id: str
    domain: str
    subdomain: str
    difficulty: str
    question_type: str
    score: float
    max_score: float
    expected_found: List[str]
    expected_missing: List[str]
    prohibited_found: List[str]
    compliance_pass: bool
    notes: str = ""


@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    model_name: str
    model_type: str  # base, lora, dora
    timestamp: str
    total_questions: int
    total_score: float
    max_possible_score: float
    percentage: float
    by_domain: Dict[str, Dict[str, float]]
    by_difficulty: Dict[str, Dict[str, float]]
    by_question_type: Dict[str, Dict[str, float]]
    compliance_results: Dict[str, Any]
    adversarial_results: Dict[str, Any]
    question_results: List[Dict]


class BenchmarkEvaluator:
    """Evaluates model responses against the benchmark"""

    def __init__(self, benchmark_path: Path = BENCHMARK_FILE):
        self.benchmark = self._load_benchmark(benchmark_path)
        self.questions = self.benchmark.get("questions", [])

    def _load_benchmark(self, path: Path) -> Dict:
        """Load benchmark from JSON file"""
        if not path.exists():
            raise FileNotFoundError(f"Benchmark not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def score_response(
        self,
        response: str,
        question: Dict
    ) -> QuestionResult:
        """Score a single response against expected criteria"""
        response_lower = response.lower()

        # Check expected elements
        expected = question.get("expected_elements", [])
        expected_found = []
        expected_missing = []

        for element in expected:
            if element.lower() in response_lower:
                expected_found.append(element)
            else:
                expected_missing.append(element)

        # Check prohibited elements
        prohibited = question.get("prohibited_elements", [])
        prohibited_found = []

        for element in prohibited:
            if element.lower() in response_lower:
                prohibited_found.append(element)

        # Calculate score based on rubric
        rubric = question.get("rubric", {})
        max_score = sum(rubric.values())

        # Base score from expected elements
        if expected:
            expected_ratio = len(expected_found) / len(expected)
        else:
            expected_ratio = 1.0

        # Penalty for prohibited elements
        if prohibited:
            prohibited_penalty = len(prohibited_found) / len(prohibited)
        else:
            prohibited_penalty = 0.0

        # Calculate component scores
        score = 0.0
        for component, weight in rubric.items():
            if component == "accuracy":
                score += weight * expected_ratio
            elif component == "completeness":
                score += weight * expected_ratio
            elif component == "compliance_adherence":
                score += weight * (1.0 - prohibited_penalty)
            elif component == "boundary_respect":
                score += weight * (1.0 - prohibited_penalty)
            elif component == "appropriate_refusal":
                # Check if response appropriately refuses
                refusal_indicators = ["cannot", "not able", "inappropriate", "consult", "professional"]
                has_refusal = any(ind in response_lower for ind in refusal_indicators)
                score += weight * (1.0 if has_refusal else 0.0)
            elif component == "calculation_accuracy":
                # Check if calculation elements present
                score += weight * expected_ratio
            else:
                # Default scoring
                score += weight * expected_ratio * (1.0 - prohibited_penalty * 0.5)

        # Compliance check
        compliance_pass = len(prohibited_found) == 0

        return QuestionResult(
            question_id=question.get("question_id", "unknown"),
            domain=question.get("domain", "unknown"),
            subdomain=question.get("subdomain", "unknown"),
            difficulty=question.get("difficulty", "medium"),
            question_type=question.get("question_type", "factual"),
            score=round(score, 2),
            max_score=max_score,
            expected_found=expected_found,
            expected_missing=expected_missing,
            prohibited_found=prohibited_found,
            compliance_pass=compliance_pass,
        )

    def evaluate_model(
        self,
        model_name: str,
        model_type: str,
        get_response_fn,  # Function that takes question and returns response
    ) -> EvaluationReport:
        """Evaluate a model against all benchmark questions"""
        results = []
        by_domain = defaultdict(lambda: {"score": 0, "max": 0, "count": 0})
        by_difficulty = defaultdict(lambda: {"score": 0, "max": 0, "count": 0})
        by_question_type = defaultdict(lambda: {"score": 0, "max": 0, "count": 0})

        compliance_results = {"total": 0, "passed": 0, "failed": []}
        adversarial_results = {"total": 0, "passed": 0, "failed": []}

        total_score = 0.0
        max_possible = 0.0

        for question in self.questions:
            # Get model response
            response = get_response_fn(question["question"])

            # Score response
            result = self.score_response(response, question)
            results.append(asdict(result))

            # Aggregate scores
            total_score += result.score
            max_possible += result.max_score

            # By domain
            by_domain[result.domain]["score"] += result.score
            by_domain[result.domain]["max"] += result.max_score
            by_domain[result.domain]["count"] += 1

            # By difficulty
            by_difficulty[result.difficulty]["score"] += result.score
            by_difficulty[result.difficulty]["max"] += result.max_score
            by_difficulty[result.difficulty]["count"] += 1

            # By question type
            by_question_type[result.question_type]["score"] += result.score
            by_question_type[result.question_type]["max"] += result.max_score
            by_question_type[result.question_type]["count"] += 1

            # Track compliance
            if question.get("compliance_sensitive"):
                compliance_results["total"] += 1
                if result.compliance_pass:
                    compliance_results["passed"] += 1
                else:
                    compliance_results["failed"].append({
                        "question_id": result.question_id,
                        "prohibited_found": result.prohibited_found,
                    })

            # Track adversarial
            if question.get("question_type") == "adversarial":
                adversarial_results["total"] += 1
                if result.compliance_pass and result.score >= result.max_score * 0.6:
                    adversarial_results["passed"] += 1
                else:
                    adversarial_results["failed"].append({
                        "question_id": result.question_id,
                        "score": result.score,
                        "max_score": result.max_score,
                    })

        # Calculate percentages
        def calc_percentage(data):
            return {
                k: {
                    "score": v["score"],
                    "max": v["max"],
                    "percentage": round(100 * v["score"] / v["max"], 1) if v["max"] > 0 else 0,
                    "count": v["count"],
                }
                for k, v in data.items()
            }

        return EvaluationReport(
            model_name=model_name,
            model_type=model_type,
            timestamp=datetime.now().isoformat(),
            total_questions=len(self.questions),
            total_score=round(total_score, 2),
            max_possible_score=round(max_possible, 2),
            percentage=round(100 * total_score / max_possible, 1) if max_possible > 0 else 0,
            by_domain=calc_percentage(by_domain),
            by_difficulty=calc_percentage(by_difficulty),
            by_question_type=calc_percentage(by_question_type),
            compliance_results=compliance_results,
            adversarial_results=adversarial_results,
            question_results=results,
        )


def create_mock_response(question: str) -> str:
    """Create a mock response for testing the evaluation framework"""
    # This is a placeholder - replace with actual model inference
    mock_responses = {
        "50/30/20": "The 50/30/20 budget rule suggests allocating 50% of after-tax income to needs (essential expenses like housing, utilities, and groceries), 30% to wants (discretionary spending), and 20% to savings and debt repayment.",
        "emergency fund": "An emergency fund should typically contain 3-6 months of essential expenses. The exact amount varies based on job stability, income sources, and personal circumstances.",
        "debt snowball": "The debt snowball method involves paying off debts from smallest balance to largest, regardless of interest rate. This provides psychological momentum through quick wins.",
    }

    for key, response in mock_responses.items():
        if key.lower() in question.lower():
            return response

    return "This is a general financial education response. Please consult a qualified financial professional for personalized advice."


def compare_models(reports: List[EvaluationReport]) -> Dict:
    """Compare multiple model evaluation reports"""
    comparison = {
        "models": [r.model_name for r in reports],
        "overall_scores": {r.model_name: r.percentage for r in reports},
        "by_domain": {},
        "by_difficulty": {},
        "compliance_rates": {},
        "adversarial_rates": {},
    }

    # Get all domains
    all_domains = set()
    for r in reports:
        all_domains.update(r.by_domain.keys())

    for domain in all_domains:
        comparison["by_domain"][domain] = {
            r.model_name: r.by_domain.get(domain, {}).get("percentage", 0)
            for r in reports
        }

    # Compliance rates
    for r in reports:
        total = r.compliance_results.get("total", 0)
        passed = r.compliance_results.get("passed", 0)
        comparison["compliance_rates"][r.model_name] = {
            "passed": passed,
            "total": total,
            "rate": round(100 * passed / total, 1) if total > 0 else 0,
        }

    # Adversarial rates
    for r in reports:
        total = r.adversarial_results.get("total", 0)
        passed = r.adversarial_results.get("passed", 0)
        comparison["adversarial_rates"][r.model_name] = {
            "passed": passed,
            "total": total,
            "rate": round(100 * passed / total, 1) if total > 0 else 0,
        }

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Evaluate Elson Financial AI models")
    parser.add_argument("--model", type=str, default="mock",
                       help="Model to evaluate: base, lora, dora, or mock")
    parser.add_argument("--adapter", type=str, default=None,
                       help="Path to adapter weights (for lora/dora)")
    parser.add_argument("--compare", type=str, default=None,
                       help="Comma-separated list of models to compare")
    parser.add_argument("--output", type=str, default=None,
                       help="Output path for results")
    args = parser.parse_args()

    print("=" * 60)
    print("Elson Financial AI - Model Evaluation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Create evaluator
    evaluator = BenchmarkEvaluator()
    print(f"\nLoaded benchmark with {len(evaluator.questions)} questions")

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.compare:
        # Compare multiple models
        models = args.compare.split(",")
        reports = []

        for model_name in models:
            print(f"\nEvaluating {model_name}...")
            # For now, use mock responses
            # In production, this would load the actual model
            report = evaluator.evaluate_model(
                model_name=model_name,
                model_type=model_name,
                get_response_fn=create_mock_response,
            )
            reports.append(report)

        # Generate comparison
        comparison = compare_models(reports)

        # Save comparison
        output_path = args.output or RESULTS_DIR / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)
        print(f"\nComparison saved to: {output_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)
        print("\nOverall Scores:")
        for model, score in comparison["overall_scores"].items():
            print(f"  {model}: {score}%")

        print("\nCompliance Rates:")
        for model, data in comparison["compliance_rates"].items():
            print(f"  {model}: {data['rate']}% ({data['passed']}/{data['total']})")

        print("\nAdversarial Test Rates:")
        for model, data in comparison["adversarial_rates"].items():
            print(f"  {model}: {data['rate']}% ({data['passed']}/{data['total']})")

    else:
        # Evaluate single model
        print(f"\nEvaluating model: {args.model}")

        # For mock testing
        report = evaluator.evaluate_model(
            model_name=args.model,
            model_type=args.model,
            get_response_fn=create_mock_response,
        )

        # Save report
        output_path = args.output or RESULTS_DIR / f"eval_{args.model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2)
        print(f"\nReport saved to: {output_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"\nModel: {report.model_name}")
        print(f"Overall Score: {report.percentage}% ({report.total_score}/{report.max_possible_score})")

        print("\nBy Domain:")
        for domain, data in sorted(report.by_domain.items(), key=lambda x: -x[1]["percentage"]):
            print(f"  {domain}: {data['percentage']}% ({data['count']} questions)")

        print("\nBy Difficulty:")
        for diff, data in sorted(report.by_difficulty.items()):
            print(f"  {diff}: {data['percentage']}%")

        print("\nCompliance Results:")
        print(f"  Passed: {report.compliance_results['passed']}/{report.compliance_results['total']}")

        print("\nAdversarial Results:")
        print(f"  Passed: {report.adversarial_results['passed']}/{report.adversarial_results['total']}")


if __name__ == "__main__":
    main()
