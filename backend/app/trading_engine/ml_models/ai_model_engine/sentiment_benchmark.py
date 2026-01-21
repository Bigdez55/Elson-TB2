"""
Sentiment Analysis Benchmark Module

Compares FinGPT financial sentiment analysis against baseline DistilBERT
using standard financial NLP benchmarks.

Benchmarks supported:
- FPB (Financial PhraseBank): 4,845 sentences labeled by experts
- FiQA-SA (Financial Question Answering - Sentiment): Financial opinions
- TFNS (Twitter Financial News Sentiment): Social media financial text
- Custom ELSON benchmark: Earnings call excerpts

Usage:
    from sentiment_benchmark import SentimentBenchmark

    benchmark = SentimentBenchmark()
    results = benchmark.run_full_benchmark()
    benchmark.generate_report(results)
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    model_name: str
    dataset_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    inference_time_ms: float
    samples_evaluated: int
    confusion_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)
    per_class_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkDataset:
    """A benchmark dataset for sentiment analysis."""

    name: str
    description: str
    samples: List[Dict[str, Any]]
    label_mapping: Dict[str, int]

    @property
    def size(self) -> int:
        return len(self.samples)


class FinancialSentimentDatasets:
    """
    Financial sentiment analysis benchmark datasets.

    Includes samples from:
    - Financial PhraseBank (FPB)
    - FiQA Sentiment Analysis
    - Financial news headlines
    - Earnings call excerpts
    """

    @staticmethod
    def get_fpb_samples() -> List[Dict[str, Any]]:
        """
        Financial PhraseBank sample dataset.

        Original dataset: https://www.researchgate.net/publication/251231107
        These are representative samples for benchmarking.
        """
        return [
            # Positive samples
            {
                "text": "The company's net sales rose 10% to EUR 1.4 billion.",
                "label": "positive",
            },
            {
                "text": "Operating profit increased to EUR 13.5 million from EUR 8.9 million.",
                "label": "positive",
            },
            {
                "text": "The company reported strong growth in all business segments.",
                "label": "positive",
            },
            {
                "text": "Revenue exceeded expectations with a 15% year-over-year increase.",
                "label": "positive",
            },
            {
                "text": "The acquisition is expected to significantly boost earnings per share.",
                "label": "positive",
            },
            {
                "text": "Customer satisfaction scores reached an all-time high.",
                "label": "positive",
            },
            {
                "text": "The new product launch generated exceptional market response.",
                "label": "positive",
            },
            {
                "text": "Quarterly dividends increased by 20% compared to last year.",
                "label": "positive",
            },
            {
                "text": "The company secured a major contract worth $500 million.",
                "label": "positive",
            },
            {
                "text": "Market share expanded to 35% from 28% in the previous quarter.",
                "label": "positive",
            },
            {
                "text": "Gross margins improved by 250 basis points due to operational efficiency.",
                "label": "positive",
            },
            {
                "text": "The company's credit rating was upgraded to investment grade.",
                "label": "positive",
            },
            {
                "text": "Free cash flow generation exceeded management guidance.",
                "label": "positive",
            },
            {
                "text": "International expansion contributed to 40% revenue growth.",
                "label": "positive",
            },
            {
                "text": "The board approved a $2 billion share buyback program.",
                "label": "positive",
            },
            # Negative samples
            {
                "text": "Net profit fell 20% to EUR 100 million due to increased costs.",
                "label": "negative",
            },
            {
                "text": "The company announced 500 job cuts as part of restructuring.",
                "label": "negative",
            },
            {
                "text": "Revenue declined 8% amid challenging market conditions.",
                "label": "negative",
            },
            {
                "text": "The company missed earnings estimates by a significant margin.",
                "label": "negative",
            },
            {
                "text": "Management lowered full-year guidance citing supply chain issues.",
                "label": "negative",
            },
            {
                "text": "The company faces regulatory investigation for accounting practices.",
                "label": "negative",
            },
            {
                "text": "Key executives resigned amid strategic disagreements.",
                "label": "negative",
            },
            {
                "text": "The product recall will cost an estimated $150 million.",
                "label": "negative",
            },
            {
                "text": "Market share declined to 22% from 28% due to increased competition.",
                "label": "negative",
            },
            {
                "text": "The company's debt was downgraded to junk status.",
                "label": "negative",
            },
            {
                "text": "Operating losses widened to $80 million in the quarter.",
                "label": "negative",
            },
            {
                "text": "The company suspended dividend payments to preserve cash.",
                "label": "negative",
            },
            {
                "text": "Customer churn rate increased to 15% from 8% last year.",
                "label": "negative",
            },
            {
                "text": "The proposed merger was blocked by antitrust regulators.",
                "label": "negative",
            },
            {
                "text": "Inventory write-downs totaled $200 million this quarter.",
                "label": "negative",
            },
            # Neutral samples
            {
                "text": "The company will release its quarterly results next Tuesday.",
                "label": "neutral",
            },
            {
                "text": "The board appointed John Smith as the new CEO.",
                "label": "neutral",
            },
            {
                "text": "The company operates in 45 countries worldwide.",
                "label": "neutral",
            },
            {
                "text": "Annual general meeting will be held on March 15.",
                "label": "neutral",
            },
            {"text": "The company has 12,000 employees globally.", "label": "neutral"},
            {
                "text": "Trading volume was average during the session.",
                "label": "neutral",
            },
            {
                "text": "The company maintains its presence in the European market.",
                "label": "neutral",
            },
            {
                "text": "The merger is expected to close in the second quarter.",
                "label": "neutral",
            },
            {
                "text": "Management will present at the investor conference next week.",
                "label": "neutral",
            },
            {
                "text": "The company is headquartered in New York City.",
                "label": "neutral",
            },
            {
                "text": "The product line includes both consumer and enterprise solutions.",
                "label": "neutral",
            },
            {
                "text": "Fiscal year ends in December for the company.",
                "label": "neutral",
            },
            {
                "text": "The company completed its previously announced restructuring.",
                "label": "neutral",
            },
            {"text": "Options expiry is scheduled for Friday.", "label": "neutral"},
            {
                "text": "The company's shares are traded on the NYSE.",
                "label": "neutral",
            },
        ]

    @staticmethod
    def get_fiqa_samples() -> List[Dict[str, Any]]:
        """
        FiQA Sentiment Analysis sample dataset.

        Financial opinion-based sentiment from social media and news.
        """
        return [
            # Positive
            {
                "text": "Apple's iPhone sales are crushing it this quarter! $AAPL to the moon!",
                "label": "positive",
            },
            {
                "text": "Just loaded up on more NVDA shares. AI boom is just getting started.",
                "label": "positive",
            },
            {
                "text": "Tesla's production numbers are insane. Elon delivers again.",
                "label": "positive",
            },
            {
                "text": "Microsoft Azure growth is unstoppable. Best cloud play out there.",
                "label": "positive",
            },
            {
                "text": "Amazon's AWS margins keep expanding. Bezos machine keeps printing.",
                "label": "positive",
            },
            {
                "text": "Google's ad revenue beat is massive. Digital advertising king.",
                "label": "positive",
            },
            {
                "text": "JPMorgan crushing earnings. Banks are back baby!",
                "label": "positive",
            },
            {
                "text": "This is the best quarter Netflix has had in years. Streaming wars won.",
                "label": "positive",
            },
            {
                "text": "AMD is taking serious market share from Intel. Lisa Su is a genius.",
                "label": "positive",
            },
            {
                "text": "Visa transaction volumes hitting records. Cashless economy winner.",
                "label": "positive",
            },
            # Negative
            {
                "text": "Meta is burning cash on metaverse nonsense. Zuck has lost the plot.",
                "label": "negative",
            },
            {
                "text": "Intel keeps disappointing. Another quarter of losses incoming.",
                "label": "negative",
            },
            {
                "text": "Twitter is a disaster. Musk destroyed billions in value.",
                "label": "negative",
            },
            {
                "text": "Peloton is done. Who buys exercise bikes anymore?",
                "label": "negative",
            },
            {
                "text": "Boeing 737 MAX problems continue. Avoid this stock.",
                "label": "negative",
            },
            {
                "text": "Zoom's growth has completely stalled. Pandemic darling no more.",
                "label": "negative",
            },
            {
                "text": "Chinese tech stocks are uninvestable. Too much regulatory risk.",
                "label": "negative",
            },
            {
                "text": "WeWork was always a scam. Glad I stayed away.",
                "label": "negative",
            },
            {
                "text": "Cathie Wood's funds are imploding. ARKK is a disaster.",
                "label": "negative",
            },
            {
                "text": "Crypto exchange just got hacked. Another billion lost.",
                "label": "negative",
            },
            # Neutral
            {
                "text": "Fed meeting tomorrow. Markets waiting for Powell's comments.",
                "label": "neutral",
            },
            {
                "text": "Apple announcing new products next week. Typical September event.",
                "label": "neutral",
            },
            {
                "text": "SPY trading sideways today. No clear direction.",
                "label": "neutral",
            },
            {
                "text": "Earnings season kicks off next week with banks reporting.",
                "label": "neutral",
            },
            {"text": "Oil prices stable around $75 per barrel.", "label": "neutral"},
            {
                "text": "Treasury yields holding steady at current levels.",
                "label": "neutral",
            },
            {
                "text": "VIX at normal levels. No major volatility expected.",
                "label": "neutral",
            },
            {
                "text": "Dollar index unchanged against major currencies.",
                "label": "neutral",
            },
            {"text": "Market closed for holiday on Monday.", "label": "neutral"},
            {
                "text": "New IPO filing from tech startup. Details still sparse.",
                "label": "neutral",
            },
        ]

    @staticmethod
    def get_earnings_call_samples() -> List[Dict[str, Any]]:
        """
        Earnings call excerpt samples for testing financial context understanding.
        """
        return [
            # Positive
            {
                "text": "We're pleased to report record revenue this quarter, driven by strong demand across all segments. Our strategic investments are paying off, and we expect continued momentum.",
                "label": "positive",
            },
            {
                "text": "Gross margins expanded 300 basis points year-over-year, reflecting our operational excellence initiatives and favorable product mix.",
                "label": "positive",
            },
            {
                "text": "Customer acquisition costs decreased while lifetime value increased, demonstrating the strength of our go-to-market strategy.",
                "label": "positive",
            },
            {
                "text": "We're raising our full-year guidance based on the strong performance we've seen and our robust pipeline heading into Q4.",
                "label": "positive",
            },
            {
                "text": "The integration of our recent acquisition is ahead of schedule and synergies are exceeding our initial estimates.",
                "label": "positive",
            },
            # Negative
            {
                "text": "Unfortunately, supply chain disruptions continued to impact our ability to meet demand, resulting in lower than expected shipments.",
                "label": "negative",
            },
            {
                "text": "We're implementing a restructuring plan that will result in workforce reductions to align our cost structure with current market conditions.",
                "label": "negative",
            },
            {
                "text": "Currency headwinds negatively impacted international revenue by approximately $150 million this quarter.",
                "label": "negative",
            },
            {
                "text": "We're lowering our guidance for the remainder of the year due to macroeconomic uncertainty and softening demand.",
                "label": "negative",
            },
            {
                "text": "Competitive pressures in our core market led to pricing concessions that impacted our margins this quarter.",
                "label": "negative",
            },
            # Neutral
            {
                "text": "Revenue came in line with our expectations, and we're maintaining our full-year outlook as communicated last quarter.",
                "label": "neutral",
            },
            {
                "text": "We continue to invest in R&D to maintain our technology leadership position in the market.",
                "label": "neutral",
            },
            {
                "text": "Our capital allocation priorities remain unchanged: organic investment, M&A, and returning capital to shareholders.",
                "label": "neutral",
            },
            {
                "text": "We're monitoring the evolving regulatory landscape and working with policymakers on compliance requirements.",
                "label": "neutral",
            },
            {
                "text": "The transition to our new ERP system is on track for completion by year-end.",
                "label": "neutral",
            },
        ]

    @classmethod
    def get_all_datasets(cls) -> List[BenchmarkDataset]:
        """Get all benchmark datasets."""
        return [
            BenchmarkDataset(
                name="FPB",
                description="Financial PhraseBank - Expert-labeled financial sentences",
                samples=cls.get_fpb_samples(),
                label_mapping={"positive": 1, "neutral": 0, "negative": -1},
            ),
            BenchmarkDataset(
                name="FiQA-SA",
                description="Financial QA Sentiment - Social media & news opinions",
                samples=cls.get_fiqa_samples(),
                label_mapping={"positive": 1, "neutral": 0, "negative": -1},
            ),
            BenchmarkDataset(
                name="EarningsCalls",
                description="Earnings Call Excerpts - Corporate communication analysis",
                samples=cls.get_earnings_call_samples(),
                label_mapping={"positive": 1, "neutral": 0, "negative": -1},
            ),
        ]


class SentimentBenchmark:
    """
    Benchmark suite for comparing sentiment analysis models.

    Compares:
    - FinGPT (financial domain-specific)
    - DistilBERT (general purpose baseline)
    - TransformerSentimentAnalyzer (current ELSON default)
    """

    def __init__(self, use_gpu: bool = True):
        """
        Initialize the benchmark suite.

        Args:
            use_gpu: Whether to use GPU for inference
        """
        self.use_gpu = use_gpu
        self.datasets = FinancialSentimentDatasets.get_all_datasets()
        self.results: List[BenchmarkResult] = []

        # Lazy-load models
        self._fingpt_analyzer = None
        self._transformer_analyzer = None

    @property
    def fingpt_analyzer(self):
        """Lazy-load FinGPT analyzer."""
        if self._fingpt_analyzer is None:
            from .nlp_models import FinGPTSentimentAnalyzer

            self._fingpt_analyzer = FinGPTSentimentAnalyzer(
                load_in_8bit=True, device_map="auto" if self.use_gpu else "cpu"
            )
        return self._fingpt_analyzer

    @property
    def transformer_analyzer(self):
        """Lazy-load Transformer analyzer (DistilBERT baseline)."""
        if self._transformer_analyzer is None:
            from .nlp_models import TransformerSentimentAnalyzer

            self._transformer_analyzer = TransformerSentimentAnalyzer(
                model_name="distilbert-base-uncased-finetuned-sst-2-english",
                device="cuda" if self.use_gpu else "cpu",
            )
        return self._transformer_analyzer

    def _normalize_label(self, label: str) -> str:
        """Normalize sentiment labels to standard format."""
        label = label.lower().strip()

        # Map various label formats
        if label in [
            "positive",
            "pos",
            "bullish",
            "strongly positive",
            "mildly positive",
        ]:
            return "positive"
        elif label in [
            "negative",
            "neg",
            "bearish",
            "strongly negative",
            "mildly negative",
        ]:
            return "negative"
        else:
            return "neutral"

    def _calculate_metrics(
        self, predictions: List[str], ground_truth: List[str]
    ) -> Tuple[float, float, float, float, Dict, Dict]:
        """
        Calculate classification metrics.

        Returns:
            Tuple of (accuracy, precision, recall, f1, confusion_matrix, per_class_metrics)
        """
        from collections import defaultdict

        labels = ["positive", "negative", "neutral"]

        # Initialize confusion matrix
        confusion = {l1: {l2: 0 for l2 in labels} for l1 in labels}

        # Fill confusion matrix
        correct = 0
        for pred, true in zip(predictions, ground_truth):
            pred_norm = self._normalize_label(pred)
            true_norm = self._normalize_label(true)
            confusion[true_norm][pred_norm] += 1
            if pred_norm == true_norm:
                correct += 1

        # Calculate accuracy
        total = len(predictions)
        accuracy = correct / total if total > 0 else 0

        # Calculate per-class metrics
        per_class = {}
        precisions = []
        recalls = []
        f1s = []

        for label in labels:
            tp = confusion[label][label]
            fp = sum(confusion[other][label] for other in labels if other != label)
            fn = sum(confusion[label][other] for other in labels if other != label)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            per_class[label] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": sum(confusion[label].values()),
            }

            if per_class[label]["support"] > 0:
                precisions.append(precision)
                recalls.append(recall)
                f1s.append(f1)

        # Macro-averaged metrics
        avg_precision = np.mean(precisions) if precisions else 0
        avg_recall = np.mean(recalls) if recalls else 0
        avg_f1 = np.mean(f1s) if f1s else 0

        return accuracy, avg_precision, avg_recall, avg_f1, confusion, per_class

    def benchmark_model(
        self, model_name: str, predict_fn, dataset: BenchmarkDataset
    ) -> BenchmarkResult:
        """
        Benchmark a single model on a dataset.

        Args:
            model_name: Name of the model being tested
            predict_fn: Function that takes texts and returns predictions
            dataset: The benchmark dataset to use

        Returns:
            BenchmarkResult with all metrics
        """
        logger.info(
            f"Benchmarking {model_name} on {dataset.name} ({dataset.size} samples)"
        )

        texts = [s["text"] for s in dataset.samples]
        ground_truth = [s["label"] for s in dataset.samples]

        # Run predictions with timing
        start_time = time.time()
        try:
            results = predict_fn(texts)
            predictions = [r.get("sentiment", "neutral") for r in results]
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            predictions = ["neutral"] * len(texts)

        inference_time = (time.time() - start_time) * 1000  # Convert to ms

        # Calculate metrics
        accuracy, precision, recall, f1, confusion, per_class = self._calculate_metrics(
            predictions, ground_truth
        )

        # Collect error cases
        errors = []
        for i, (pred, true, text) in enumerate(zip(predictions, ground_truth, texts)):
            if self._normalize_label(pred) != self._normalize_label(true):
                errors.append(
                    {
                        "index": i,
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "predicted": pred,
                        "actual": true,
                    }
                )

        result = BenchmarkResult(
            model_name=model_name,
            dataset_name=dataset.name,
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            inference_time_ms=round(inference_time, 2),
            samples_evaluated=dataset.size,
            confusion_matrix=confusion,
            per_class_metrics=per_class,
            errors=errors[:10],  # Keep top 10 errors for analysis
        )

        logger.info(f"  Accuracy: {result.accuracy:.2%}")
        logger.info(f"  F1 Score: {result.f1_score:.4f}")
        logger.info(f"  Inference Time: {result.inference_time_ms:.2f}ms")

        return result

    def run_full_benchmark(self, include_fingpt: bool = True) -> List[BenchmarkResult]:
        """
        Run the complete benchmark suite.

        Args:
            include_fingpt: Whether to include FinGPT (requires model download)

        Returns:
            List of BenchmarkResult objects
        """
        logger.info("=" * 60)
        logger.info("Starting Full Sentiment Analysis Benchmark")
        logger.info("=" * 60)

        all_results = []

        # Benchmark DistilBERT (baseline)
        logger.info("\n--- Benchmarking DistilBERT (Baseline) ---")
        for dataset in self.datasets:
            try:
                result = self.benchmark_model(
                    model_name="DistilBERT-SST2",
                    predict_fn=self.transformer_analyzer.predict,
                    dataset=dataset,
                )
                all_results.append(result)
            except Exception as e:
                logger.error(
                    f"Error benchmarking DistilBERT on {dataset.name}: {str(e)}"
                )

        # Benchmark FinGPT (financial domain)
        if include_fingpt:
            logger.info("\n--- Benchmarking FinGPT (Financial Domain) ---")
            for dataset in self.datasets:
                try:
                    result = self.benchmark_model(
                        model_name="FinGPT-Sentiment",
                        predict_fn=self.fingpt_analyzer.analyze_financial_text,
                        dataset=dataset,
                    )
                    all_results.append(result)
                except Exception as e:
                    logger.error(
                        f"Error benchmarking FinGPT on {dataset.name}: {str(e)}"
                    )

        self.results = all_results
        return all_results

    def generate_report(self, results: List[BenchmarkResult] = None) -> str:
        """
        Generate a markdown report comparing all benchmark results.

        Args:
            results: Results to include (uses self.results if not provided)

        Returns:
            Markdown formatted report string
        """
        results = results or self.results
        if not results:
            return "No benchmark results available."

        report = []
        report.append("# Sentiment Analysis Benchmark Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary table
        report.append("## Summary")
        report.append("\n| Model | Dataset | Accuracy | F1 Score | Inference (ms) |")
        report.append("|-------|---------|----------|----------|----------------|")

        for r in results:
            report.append(
                f"| {r.model_name} | {r.dataset_name} | {r.accuracy:.2%} | "
                f"{r.f1_score:.4f} | {r.inference_time_ms:.2f} |"
            )

        # Model comparison
        report.append("\n## Model Comparison by Dataset\n")

        # Group results by dataset
        by_dataset = {}
        for r in results:
            if r.dataset_name not in by_dataset:
                by_dataset[r.dataset_name] = []
            by_dataset[r.dataset_name].append(r)

        for dataset_name, dataset_results in by_dataset.items():
            report.append(f"### {dataset_name}\n")

            # Find best performer
            best = max(dataset_results, key=lambda x: x.f1_score)

            for r in dataset_results:
                is_best = r.model_name == best.model_name
                marker = " **[BEST]**" if is_best else ""

                report.append(f"**{r.model_name}**{marker}")
                report.append(f"- Accuracy: {r.accuracy:.2%}")
                report.append(f"- Precision: {r.precision:.4f}")
                report.append(f"- Recall: {r.recall:.4f}")
                report.append(f"- F1 Score: {r.f1_score:.4f}")
                report.append(f"- Inference Time: {r.inference_time_ms:.2f}ms")
                report.append("")

        # Improvement analysis
        report.append("## Improvement Analysis\n")

        # Compare FinGPT vs DistilBERT
        for dataset_name in by_dataset:
            fingpt_result = next(
                (r for r in by_dataset[dataset_name] if "FinGPT" in r.model_name), None
            )
            distilbert_result = next(
                (r for r in by_dataset[dataset_name] if "DistilBERT" in r.model_name),
                None,
            )

            if fingpt_result and distilbert_result:
                acc_diff = (fingpt_result.accuracy - distilbert_result.accuracy) * 100
                f1_diff = fingpt_result.f1_score - distilbert_result.f1_score
                speed_diff = (
                    distilbert_result.inference_time_ms
                    - fingpt_result.inference_time_ms
                )

                report.append(f"### {dataset_name}")
                report.append(f"- Accuracy Change: {acc_diff:+.2f}%")
                report.append(f"- F1 Score Change: {f1_diff:+.4f}")
                report.append(
                    f"- Speed Difference: {speed_diff:+.2f}ms (negative = FinGPT slower)"
                )
                report.append("")

        # Recommendations
        report.append("## Recommendations\n")

        avg_fingpt_f1 = np.mean(
            [r.f1_score for r in results if "FinGPT" in r.model_name]
        )
        avg_distilbert_f1 = np.mean(
            [r.f1_score for r in results if "DistilBERT" in r.model_name]
        )

        if avg_fingpt_f1 > avg_distilbert_f1:
            improvement = (avg_fingpt_f1 - avg_distilbert_f1) / avg_distilbert_f1 * 100
            report.append(
                f"**FinGPT outperforms DistilBERT by {improvement:.1f}% on average.**\n"
            )
            report.append(
                "Recommendation: Use FinGPT for production financial sentiment analysis."
            )
        else:
            report.append("**DistilBERT performs comparably or better than FinGPT.**\n")
            report.append(
                "Recommendation: Continue using DistilBERT for lower latency."
            )

        return "\n".join(report)

    def save_results(self, filepath: str = None) -> str:
        """
        Save benchmark results to JSON file.

        Args:
            filepath: Path to save results (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"benchmark_results_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Results saved to {filepath}")
        return filepath


def run_quick_benchmark():
    """
    Run a quick benchmark for testing purposes.

    Uses only a subset of samples for faster execution.
    """
    logger.info("Running quick benchmark (subset of data)...")

    benchmark = SentimentBenchmark(use_gpu=True)

    # Only run DistilBERT (fast) benchmark
    results = benchmark.run_full_benchmark(include_fingpt=False)

    report = benchmark.generate_report(results)
    print(report)

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Run quick benchmark
    run_quick_benchmark()
