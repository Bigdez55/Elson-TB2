#!/usr/bin/env python3
"""
Elson TB2 - Evaluation Benchmark Runner

Runs the 100-question evaluation benchmark against the deployed model
and produces accuracy scores and detailed reports.

Usage:
    python scripts/run_evaluation_benchmark.py [--api-url URL] [--output results.json]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


@dataclass
class TestResult:
    """Result of a single test case."""
    id: int
    category: str
    question: str
    expected_keywords: List[str]
    difficulty: str
    response: str
    keywords_found: List[str]
    keywords_missing: List[str]
    score: float
    latency_ms: float
    passed: bool


@dataclass
class BenchmarkReport:
    """Overall benchmark report."""
    timestamp: str
    model_url: str
    total_tests: int
    tests_passed: int
    overall_score: float
    avg_latency_ms: float
    category_scores: Dict[str, Dict[str, float]]
    difficulty_scores: Dict[str, Dict[str, float]]
    results: List[TestResult]


def load_benchmark(benchmark_path: str) -> Dict:
    """Load the evaluation benchmark file."""
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def query_model(api_url: str, question: str, timeout: int = 60) -> Tuple[str, float]:
    """Query the model API and return response with latency."""
    start_time = time.time()

    # Try OpenAI-compatible API format (vLLM)
    payload = {
        "model": "elson-finance-trading-14b",
        "messages": [
            {"role": "system", "content": "You are Elson, an AI financial advisor."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 1024,
        "temperature": 0.1
    }

    try:
        response = requests.post(
            f"{api_url}/v1/chat/completions",
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        latency_ms = (time.time() - start_time) * 1000
        data = response.json()

        # Extract response text
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"], latency_ms

        return str(data), latency_ms

    except requests.exceptions.Timeout:
        return "[TIMEOUT]", timeout * 1000
    except requests.exceptions.ConnectionError:
        return "[CONNECTION_ERROR]", 0
    except Exception as e:
        return f"[ERROR: {str(e)}]", 0


def score_response(response: str, expected_keywords: List[str]) -> Tuple[List[str], List[str], float]:
    """Score a response based on keyword matching."""
    response_lower = response.lower()

    found = []
    missing = []

    for keyword in expected_keywords:
        # Normalize keyword for matching
        keyword_lower = keyword.lower()
        # Handle variations (e.g., "$23,000" might appear as "23000" or "23,000")
        keyword_pattern = keyword_lower.replace(",", ",?").replace("$", "\\$?")

        if re.search(keyword_pattern, response_lower):
            found.append(keyword)
        else:
            missing.append(keyword)

    if len(expected_keywords) > 0:
        score = len(found) / len(expected_keywords)
    else:
        score = 1.0

    return found, missing, score


def run_benchmark(
    api_url: str,
    benchmark_data: Dict,
    verbose: bool = True
) -> BenchmarkReport:
    """Run the full benchmark suite."""
    test_cases = benchmark_data.get("test_cases", [])
    results: List[TestResult] = []

    print(f"\nRunning {len(test_cases)} test cases...")
    print("-" * 60)

    total_latency = 0
    category_stats: Dict[str, Dict[str, float]] = {}
    difficulty_stats: Dict[str, Dict[str, float]] = {}

    for i, test in enumerate(test_cases):
        if verbose:
            print(f"[{i+1}/{len(test_cases)}] {test['category']}: {test['question'][:50]}...")

        # Query the model
        response, latency_ms = query_model(api_url, test["question"])
        total_latency += latency_ms

        # Score the response
        found, missing, score = score_response(response, test["expected_keywords"])
        passed = score >= 0.5  # Pass if at least 50% of keywords found

        result = TestResult(
            id=test["id"],
            category=test["category"],
            question=test["question"],
            expected_keywords=test["expected_keywords"],
            difficulty=test["difficulty"],
            response=response[:500] if len(response) > 500 else response,
            keywords_found=found,
            keywords_missing=missing,
            score=score,
            latency_ms=latency_ms,
            passed=passed
        )
        results.append(result)

        # Update category stats
        cat = test["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "score_sum": 0}
        category_stats[cat]["total"] += 1
        category_stats[cat]["passed"] += 1 if passed else 0
        category_stats[cat]["score_sum"] += score

        # Update difficulty stats
        diff = test["difficulty"]
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {"total": 0, "passed": 0, "score_sum": 0}
        difficulty_stats[diff]["total"] += 1
        difficulty_stats[diff]["passed"] += 1 if passed else 0
        difficulty_stats[diff]["score_sum"] += score

        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"  -> {status} (score: {score:.2f}, latency: {latency_ms:.0f}ms)")

    # Calculate final statistics
    tests_passed = sum(1 for r in results if r.passed)
    overall_score = sum(r.score for r in results) / len(results) if results else 0

    # Format category scores
    cat_scores = {}
    for cat, stats in category_stats.items():
        cat_scores[cat] = {
            "accuracy": stats["passed"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_score": stats["score_sum"] / stats["total"] if stats["total"] > 0 else 0,
            "total": stats["total"],
            "passed": stats["passed"]
        }

    # Format difficulty scores
    diff_scores = {}
    for diff, stats in difficulty_stats.items():
        diff_scores[diff] = {
            "accuracy": stats["passed"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_score": stats["score_sum"] / stats["total"] if stats["total"] > 0 else 0,
            "total": stats["total"],
            "passed": stats["passed"]
        }

    return BenchmarkReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_url=api_url,
        total_tests=len(results),
        tests_passed=tests_passed,
        overall_score=overall_score,
        avg_latency_ms=total_latency / len(results) if results else 0,
        category_scores=cat_scores,
        difficulty_scores=diff_scores,
        results=results
    )


def print_report(report: BenchmarkReport):
    """Print a formatted benchmark report."""
    print("\n" + "=" * 60)
    print("ELSON TB2 BENCHMARK REPORT")
    print("=" * 60)

    print(f"\nTimestamp: {report.timestamp}")
    print(f"Model URL: {report.model_url}")

    print(f"\n--- OVERALL RESULTS ---")
    print(f"Total Tests:    {report.total_tests}")
    print(f"Tests Passed:   {report.tests_passed} ({report.tests_passed/report.total_tests*100:.1f}%)")
    print(f"Overall Score:  {report.overall_score:.2%}")
    print(f"Avg Latency:    {report.avg_latency_ms:.0f}ms")

    print(f"\n--- CATEGORY BREAKDOWN ---")
    for cat, stats in sorted(report.category_scores.items()):
        print(f"  {cat:20} {stats['passed']}/{stats['total']} ({stats['accuracy']:.0%}) avg={stats['avg_score']:.2f}")

    print(f"\n--- DIFFICULTY BREAKDOWN ---")
    for diff, stats in sorted(report.difficulty_scores.items()):
        print(f"  {diff:10} {stats['passed']}/{stats['total']} ({stats['accuracy']:.0%}) avg={stats['avg_score']:.2f}")

    # Show failed tests
    failed = [r for r in report.results if not r.passed]
    if failed:
        print(f"\n--- FAILED TESTS ({len(failed)}) ---")
        for r in failed[:10]:  # Show first 10
            print(f"\n  #{r.id} [{r.category}] {r.difficulty}")
            print(f"  Q: {r.question[:60]}...")
            print(f"  Missing: {', '.join(r.keywords_missing)}")

    print("\n" + "=" * 60)


def save_report(report: BenchmarkReport, output_path: str):
    """Save the benchmark report to JSON."""
    # Convert dataclasses to dicts
    data = {
        "timestamp": report.timestamp,
        "model_url": report.model_url,
        "summary": {
            "total_tests": report.total_tests,
            "tests_passed": report.tests_passed,
            "overall_score": report.overall_score,
            "avg_latency_ms": report.avg_latency_ms
        },
        "category_scores": report.category_scores,
        "difficulty_scores": report.difficulty_scores,
        "results": [asdict(r) for r in report.results]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"\nReport saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run Elson TB2 Evaluation Benchmark")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="vLLM API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--benchmark",
        default=None,
        help="Path to benchmark JSON file"
    )
    parser.add_argument(
        "--output",
        default="benchmark_results.json",
        help="Output file for results"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode: don't actually query the model"
    )

    args = parser.parse_args()

    # Find benchmark file
    if args.benchmark:
        benchmark_path = args.benchmark
    else:
        base_path = Path(__file__).parent.parent
        benchmark_path = base_path / "backend" / "training_data" / "evaluation_benchmark.json"

    if not os.path.exists(benchmark_path):
        print(f"Error: Benchmark file not found: {benchmark_path}")
        return 1

    print("=" * 60)
    print("ELSON TB2 - EVALUATION BENCHMARK RUNNER")
    print("=" * 60)

    # Load benchmark
    print(f"\nLoading benchmark: {benchmark_path}")
    benchmark_data = load_benchmark(str(benchmark_path))
    print(f"  Loaded {len(benchmark_data.get('test_cases', []))} test cases")

    if args.dry_run:
        print("\n[DRY RUN MODE - Not querying model]")
        print("Would test against:", args.api_url)
        return 0

    # Run benchmark
    print(f"\nConnecting to model: {args.api_url}")

    try:
        report = run_benchmark(
            api_url=args.api_url,
            benchmark_data=benchmark_data,
            verbose=not args.quiet
        )

        # Print and save report
        print_report(report)
        save_report(report, args.output)

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
