#!/usr/bin/env python3
"""
Sentiment Analysis Benchmark Runner

Compares FinGPT financial sentiment analysis against DistilBERT baseline
on standard financial NLP benchmarks.

Usage:
    python scripts/benchmark_sentiment.py                    # Full benchmark
    python scripts/benchmark_sentiment.py --quick            # Quick test (no FinGPT)
    python scripts/benchmark_sentiment.py --save-report      # Save markdown report
    python scripts/benchmark_sentiment.py --output results/  # Custom output directory
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are available."""
    missing = []

    try:
        import torch
        logger.info(f"PyTorch: {torch.__version__}")
        logger.info(f"CUDA Available: {torch.cuda.is_available()}")
    except ImportError:
        missing.append("torch")

    try:
        import transformers
        logger.info(f"Transformers: {transformers.__version__}")
    except ImportError:
        missing.append("transformers")

    try:
        import numpy
        import pandas
    except ImportError:
        missing.append("numpy pandas")

    if missing:
        logger.error(f"Missing dependencies: {missing}")
        logger.error("Install with: pip install " + " ".join(missing))
        return False

    return True


def run_benchmark(
    include_fingpt: bool = True,
    output_dir: str = None,
    save_report: bool = True,
    save_json: bool = True
):
    """
    Run the full sentiment analysis benchmark.

    Args:
        include_fingpt: Include FinGPT in benchmark (requires model download)
        output_dir: Directory to save results
        save_report: Save markdown report
        save_json: Save JSON results
    """
    from app.trading_engine.ml_models.ai_model_engine.sentiment_benchmark import (
        SentimentBenchmark
    )

    # Set up output directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "benchmark_results"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("\n" + "="*70)
    print("ELSON Financial Sentiment Analysis Benchmark")
    print("="*70)
    print(f"\nOutput directory: {output_dir}")
    print(f"Include FinGPT: {include_fingpt}")
    print()

    # Initialize benchmark
    benchmark = SentimentBenchmark(use_gpu=True)

    # Run benchmark
    print("Running benchmark...")
    results = benchmark.run_full_benchmark(include_fingpt=include_fingpt)

    if not results:
        logger.error("No benchmark results generated")
        return

    # Generate report
    print("\nGenerating report...")
    report = benchmark.generate_report(results)

    # Print report to console
    print("\n" + "="*70)
    print(report)
    print("="*70 + "\n")

    # Save report
    if save_report:
        report_path = output_dir / f"sentiment_benchmark_report_{timestamp}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"Report saved to: {report_path}")

    # Save JSON results
    if save_json:
        json_path = output_dir / f"sentiment_benchmark_results_{timestamp}.json"
        benchmark.save_results(str(json_path))
        print(f"JSON results saved to: {json_path}")

    # Print summary
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)

    # Group by model
    by_model = {}
    for r in results:
        if r.model_name not in by_model:
            by_model[r.model_name] = []
        by_model[r.model_name].append(r)

    for model_name, model_results in by_model.items():
        avg_accuracy = sum(r.accuracy for r in model_results) / len(model_results)
        avg_f1 = sum(r.f1_score for r in model_results) / len(model_results)
        total_time = sum(r.inference_time_ms for r in model_results)

        print(f"\n{model_name}:")
        print(f"  Average Accuracy: {avg_accuracy:.2%}")
        print(f"  Average F1 Score: {avg_f1:.4f}")
        print(f"  Total Inference Time: {total_time:.2f}ms")

    print("\n" + "="*70)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark FinGPT vs DistilBERT for financial sentiment analysis"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick benchmark (DistilBERT only, skip FinGPT)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for results"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        default=True,
        help="Save markdown report (default: True)"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Don't save markdown report"
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Don't save JSON results"
    )

    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Run benchmark
    try:
        run_benchmark(
            include_fingpt=not args.quick,
            output_dir=args.output,
            save_report=not args.no_report,
            save_json=not args.no_json
        )
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
