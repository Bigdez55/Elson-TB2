"""
Quantum Model Evaluation Script.
Tests and evaluates quantum models on real market data.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Add parent directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from Elson.services.market_data import MarketDataService

# Local imports
from Elson.trading_engine.ai_model_engine.quantum_models import (
    QuantumKernelClassifier,
    QuantumVariationalClassifier,
)
from Elson.trading_engine.backtesting.quantum_backtester import QuantumModelBacktester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("quantum_evaluation.log")],
)

logger = logging.getLogger(__name__)


async def run_evaluation(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    data_service: MarketDataService,
    output_dir: str = "evaluation_results",
    n_qubits: int = 4,
    include_classical_models: bool = True,
    volatility_regime_test: bool = True,
):
    """
    Run comprehensive evaluation of quantum models on specified symbols across different
    market volatility regimes to test robustness in varying market conditions.

    Args:
        symbols: List of stock symbols to evaluate
        start_date: Start date for data
        end_date: End date for data
        data_service: Market data service for fetching data
        output_dir: Directory to save results
        n_qubits: Number of qubits to use
        include_classical_models: Whether to include classical models in comparison
        volatility_regime_test: Whether to test across different volatility regimes
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create backtester
    backtester = QuantumModelBacktester(
        market_data_service=data_service, results_dir=output_dir
    )

    # Define standard feature columns
    feature_columns = [
        "Close",
        "Volume",
        "SMA_10",
        "SMA_30",
        "EMA_10",
        "ATR",
        "Volatility",
        "RSI",
        "Price_to_SMA10",
        "Price_to_SMA30",
    ]

    # Define classical models if needed
    classical_models = {}
    if include_classical_models:
        classical_models = {
            "RandomForest": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        RandomForestClassifier(
                            n_estimators=100, class_weight="balanced"
                        ),
                    ),
                ]
            ),
            "LogisticRegression": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(max_iter=1000, class_weight="balanced"),
                    ),
                ]
            ),
        }

    # Run evaluation for each symbol
    summary_results = {}

    # Define volatility regimes if required
    volatility_regimes = {}
    if volatility_regime_test:
        volatility_regimes = {
            "LOW": {"threshold_min": 0, "threshold_max": 15},
            "NORMAL": {"threshold_min": 15, "threshold_max": 25},
            "HIGH": {"threshold_min": 25, "threshold_max": 40},
            "EXTREME": {"threshold_min": 40, "threshold_max": 100},
        }

        logger.info(
            f"Testing across {len(volatility_regimes)} volatility regimes: {', '.join(volatility_regimes.keys())}"
        )

    for symbol in symbols:
        logger.info(f"Starting evaluation for {symbol}")

        # Define models to test
        models_to_test = [
            {
                "name": "QuantumKernel",
                "constructor": lambda: QuantumKernelClassifier(
                    n_qubits=n_qubits,
                    feature_map_reps=2,
                    backend_name="statevector_simulator",
                    feature_selection="pca",
                    regularization=1.0,
                    noise_mitigation=True,
                ),
                "params": {},
            },
            {
                "name": "QuantumVariational",
                "constructor": lambda: QuantumVariationalClassifier(
                    n_qubits=n_qubits,
                    feature_map_reps=2,
                    variational_form_reps=2,
                    backend_name="statevector_simulator",
                    shots=1024,
                    feature_selection="pca",
                    regularization_strength=0.01,
                    noise_mitigation=True,
                ),
                "params": {
                    "optimizer": "COBYLA",
                    "max_iter": 100,
                    "early_stopping": True,
                },
            },
            # Add hybrid model for better performance in high volatility
            {
                "name": "QuantumHybrid",
                "constructor": lambda: QuantumKernelClassifier(
                    n_qubits=n_qubits,
                    feature_map_reps=3,  # More expressive feature map
                    backend_name="statevector_simulator",
                    feature_selection="pca",
                    regularization=0.5,  # Different regularization
                    noise_mitigation=True,
                    hybrid_model=True,  # Enable hybrid classical-quantum processing
                    classical_optimizer="ADAM",
                ),
                "params": {
                    "learning_rate": 0.01,
                    "hybrid_weight": 0.7,  # Weight between classical and quantum components
                },
            },
        ]

        symbol_results = {}

        # Fetch market data
        try:
            # Fetch daily data for calculating volatility
            historical_data = await data_service.get_historical_data(
                symbol=symbol, start_date=start_date, end_date=end_date, interval="1d"
            )

            # Convert to DataFrame
            df = pd.DataFrame(historical_data)

            # Calculate volatility (20-day rolling standard deviation of returns)
            df["Return"] = df["Close"].pct_change()
            df["Volatility_20d"] = (
                df["Return"].rolling(window=20).std() * np.sqrt(252) * 100
            )  # Annualized

            # Drop NaN values
            df = df.dropna()

            if df.empty:
                logger.error(f"No valid data for {symbol}. Skipping.")
                continue

            # If volatility regime testing is enabled
            if volatility_regime_test:
                # Create separate DataFrames for each volatility regime
                regime_dfs = {}
                regime_periods = {}

                for regime_name, thresholds in volatility_regimes.items():
                    # Filter data by volatility thresholds
                    regime_df = df[
                        (df["Volatility_20d"] >= thresholds["threshold_min"])
                        & (df["Volatility_20d"] < thresholds["threshold_max"])
                    ]

                    if len(regime_df) >= 60:  # Minimum 60 days of data required
                        regime_dfs[regime_name] = regime_df

                        # Find continuous periods
                        regime_df["date_diff"] = (
                            regime_df.index.to_series().diff().dt.days
                        )
                        period_start = None
                        periods = []

                        for idx, row in regime_df.iterrows():
                            if period_start is None or row["date_diff"] > 1:
                                if (
                                    period_start is not None
                                    and (idx - period_start).days >= 30
                                ):
                                    periods.append((period_start, idx))
                                period_start = idx

                        # Add the last period if it's long enough
                        if (
                            period_start is not None
                            and (regime_df.index[-1] - period_start).days >= 30
                        ):
                            periods.append((period_start, regime_df.index[-1]))

                        regime_periods[regime_name] = periods

                        logger.info(
                            f"Found {len(regime_df)} days in {regime_name} volatility regime "
                            f"with {len(periods)} continuous periods of 30+ days"
                        )

                logger.info(
                    f"Testing {symbol} across {len(regime_dfs)} volatility regimes "
                    f"with enough data: {list(regime_dfs.keys())}"
                )

                # Create nested structure for results by regime
                symbol_results = {regime: {} for regime in regime_dfs.keys()}

            else:
                # Just use the whole dataset
                logger.info(f"Testing {symbol} on full dataset with {len(df)} days")
                regime_dfs = {"ALL": df}
                regime_periods = {"ALL": [(df.index[0], df.index[-1])]}
                symbol_results = {"ALL": {}}

        # Run backtest for each regime and model
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            continue

        for regime_name, regime_df in regime_dfs.items():
            periods = regime_periods[regime_name]

            # Skip if no valid periods
            if not periods:
                logger.warning(
                    f"No valid test periods for {symbol} in {regime_name} regime"
                )
                continue

            logger.info(
                f"Testing {symbol} in {regime_name} volatility regime with {len(regime_df)} data points"
            )

            # Run each model
            for model_config in models_to_test:
                try:
                    # Adapt model configuration based on volatility regime if hybrid models are used
                    model_constructor = model_config["constructor"]
                    model_params = model_config["params"].copy()

                    # Adjust hyperparameters for high volatility regimes if using QuantumHybrid
                    if model_config["name"] == "QuantumHybrid" and regime_name in [
                        "HIGH",
                        "EXTREME",
                    ]:
                        if "hybrid_weight" in model_params:
                            # Increase classical component weight in high volatility
                            model_params["hybrid_weight"] = 0.5

                        if "learning_rate" in model_params:
                            # Decrease learning rate in high volatility
                            model_params["learning_rate"] = 0.005

                    logger.info(
                        f"Testing {model_config['name']} on {symbol} in {regime_name} regime"
                    )

                    # For each continuous period in this regime, run a separate backtest
                    period_results = []
                    for period_start, period_end in periods:
                        logger.debug(
                            f"Testing period {period_start.date()} to {period_end.date()}"
                        )

                        # Run backtest for this specific period
                        result = await backtester.run_full_backtest(
                            symbol=symbol,
                            start_date=period_start,
                            end_date=period_end,
                            model_constructor=model_constructor,
                            feature_columns=feature_columns,
                            model_params=model_params,
                            use_walk_forward=True,
                            classical_benchmarks=classical_models,
                        )

                        period_results.append(result)

                    # Aggregate results across all periods
                    if period_results:
                        aggregated_result = {
                            "test_metrics": {
                                "accuracy": np.mean(
                                    [
                                        r["test_metrics"]["accuracy"]
                                        for r in period_results
                                    ]
                                ),
                                "precision": np.mean(
                                    [
                                        r["test_metrics"]["precision"]
                                        for r in period_results
                                    ]
                                ),
                                "recall": np.mean(
                                    [
                                        r["test_metrics"]["recall"]
                                        for r in period_results
                                    ]
                                ),
                                "f1": np.mean(
                                    [r["test_metrics"]["f1"] for r in period_results]
                                ),
                            },
                            "financial_impact": {
                                "total_return": np.mean(
                                    [
                                        r["financial_impact"]["total_return"]
                                        for r in period_results
                                    ]
                                ),
                                "sharpe_ratio": np.mean(
                                    [
                                        r["financial_impact"]["sharpe_ratio"]
                                        for r in period_results
                                    ]
                                ),
                                "max_drawdown": np.mean(
                                    [
                                        r["financial_impact"]["max_drawdown"]
                                        for r in period_results
                                    ]
                                ),
                                "win_rate": np.mean(
                                    [
                                        r["financial_impact"]["win_rate"]
                                        for r in period_results
                                    ]
                                ),
                            },
                            "volatility_regime": regime_name,
                            "sample_count": len(regime_df),
                            "period_count": len(periods),
                            "individual_periods": [
                                {
                                    "start_date": p_start.strftime("%Y-%m-%d"),
                                    "end_date": p_end.strftime("%Y-%m-%d"),
                                    "data_points": len(
                                        regime_df[
                                            (regime_df.index >= p_start)
                                            & (regime_df.index <= p_end)
                                        ]
                                    ),
                                    "win_rate": r["financial_impact"]["win_rate"],
                                    "total_return": r["financial_impact"][
                                        "total_return"
                                    ],
                                }
                                for (p_start, p_end), r in zip(periods, period_results)
                            ],
                        }

                        # Add benchmark comparison (average across periods)
                        if all("benchmark_comparison" in r for r in period_results):
                            # Get unique benchmark names
                            benchmark_names = set()
                            for r in period_results:
                                benchmark_names.update(r["benchmark_comparison"].keys())

                            # Calculate average metrics for each benchmark
                            benchmark_comparison = {}
                            for benchmark in benchmark_names:
                                # Only include benchmarks that appear in all periods
                                if all(
                                    benchmark in r["benchmark_comparison"]
                                    for r in period_results
                                ):
                                    benchmark_comparison[benchmark] = {
                                        "accuracy": np.mean(
                                            [
                                                r["benchmark_comparison"][benchmark][
                                                    "accuracy"
                                                ]
                                                for r in period_results
                                                if benchmark
                                                in r["benchmark_comparison"]
                                            ]
                                        ),
                                        "f1": np.mean(
                                            [
                                                r["benchmark_comparison"][benchmark][
                                                    "f1"
                                                ]
                                                for r in period_results
                                                if benchmark
                                                in r["benchmark_comparison"]
                                            ]
                                        ),
                                    }

                            aggregated_result["benchmark_comparison"] = (
                                benchmark_comparison
                            )

                        # Store results for this model in this regime
                        symbol_results[regime_name][
                            model_config["name"]
                        ] = aggregated_result

                        logger.info(
                            f"Completed testing {model_config['name']} on {symbol} in {regime_name} regime. "
                            f"Avg win rate: {aggregated_result['financial_impact']['win_rate']:.2f}, "
                            f"Avg return: {aggregated_result['financial_impact']['total_return']:.2f}%"
                        )
                    else:
                        logger.warning(
                            f"No periods were successfully evaluated for {symbol} with {model_config['name']} "
                            f"in {regime_name} regime"
                        )
                        symbol_results[regime_name][model_config["name"]] = {
                            "error": "No valid periods"
                        }

                except Exception as e:
                    logger.error(
                        f"Error testing {model_config['name']} on {symbol} in {regime_name} regime: {str(e)}"
                    )
                    symbol_results[regime_name][model_config["name"]] = {
                        "error": str(e)
                    }

        # Store results for this symbol
        summary_results[symbol] = symbol_results

        # Save partial results
        with open(os.path.join(output_dir, f"{symbol}_summary.json"), "w") as f:
            json.dump(symbol_results, f, indent=2)

    # Create overall summary
    overall_summary = await create_summary_report(summary_results, output_dir)

    return overall_summary


async def create_summary_report(
    results: Dict[str, Dict[str, Any]], output_dir: str
) -> Dict[str, Any]:
    """
    Create a summary report of all model evaluations across volatility regimes

    Args:
        results: Dictionary of results by symbol, regime, and model
        output_dir: Directory to save the report

    Returns:
        Summary metrics including performance by volatility regime
    """
    # Initialize summary structures
    summary = {"models": {}, "symbols": {}, "volatility_regimes": {}, "overall": {}}

    # Extract model names, symbol names, and regimes
    model_names = set()
    regimes = set()

    for symbol, symbol_results in results.items():
        for regime, regime_results in symbol_results.items():
            regimes.add(regime)
            for model_name in regime_results.keys():
                model_names.add(model_name)

    # Initialize regime summary data structure
    for regime in regimes:
        summary["volatility_regimes"][regime] = {
            "models": {},
            "sample_count": 0,
            "period_count": 0,
        }

    # Calculate average metrics by model
    for model_name in model_names:
        # Overall metrics across all regimes
        model_metrics = {
            "accuracy": [],
            "f1": [],
            "total_return": [],
            "sharpe_ratio": [],
            "max_drawdown": [],
            "win_rate": [],
        }

        # Metrics by regime
        regime_metrics = {
            regime: {
                "accuracy": [],
                "f1": [],
                "total_return": [],
                "sharpe_ratio": [],
                "max_drawdown": [],
                "win_rate": [],
                "sample_count": [],
                "period_count": [],
            }
            for regime in regimes
        }

        for symbol, symbol_results in results.items():
            for regime, regime_results in symbol_results.items():
                if (
                    model_name in regime_results
                    and "error" not in regime_results[model_name]
                ):
                    # Add test metrics to both overall and regime-specific
                    if "test_metrics" in regime_results[model_name]:
                        metrics = regime_results[model_name]["test_metrics"]
                        model_metrics["accuracy"].append(metrics["accuracy"])
                        model_metrics["f1"].append(metrics["f1"])

                        regime_metrics[regime]["accuracy"].append(metrics["accuracy"])
                        regime_metrics[regime]["f1"].append(metrics["f1"])

                    # Add financial metrics
                    if "financial_impact" in regime_results[model_name]:
                        impact = regime_results[model_name]["financial_impact"]
                        model_metrics["total_return"].append(impact["total_return"])
                        model_metrics["sharpe_ratio"].append(impact["sharpe_ratio"])
                        model_metrics["max_drawdown"].append(impact["max_drawdown"])
                        model_metrics["win_rate"].append(impact["win_rate"])

                        regime_metrics[regime]["total_return"].append(
                            impact["total_return"]
                        )
                        regime_metrics[regime]["sharpe_ratio"].append(
                            impact["sharpe_ratio"]
                        )
                        regime_metrics[regime]["max_drawdown"].append(
                            impact["max_drawdown"]
                        )
                        regime_metrics[regime]["win_rate"].append(impact["win_rate"])

                    # Add sample and period counts
                    if "sample_count" in regime_results[model_name]:
                        regime_metrics[regime]["sample_count"].append(
                            regime_results[model_name]["sample_count"]
                        )

                    if "period_count" in regime_results[model_name]:
                        regime_metrics[regime]["period_count"].append(
                            regime_results[model_name]["period_count"]
                        )

        # Calculate overall model averages
        summary["models"][model_name] = {
            "avg_accuracy": (
                np.mean(model_metrics["accuracy"])
                if model_metrics["accuracy"]
                else None
            ),
            "avg_f1": np.mean(model_metrics["f1"]) if model_metrics["f1"] else None,
            "avg_total_return": (
                np.mean(model_metrics["total_return"])
                if model_metrics["total_return"]
                else None
            ),
            "avg_sharpe_ratio": (
                np.mean(model_metrics["sharpe_ratio"])
                if model_metrics["sharpe_ratio"]
                else None
            ),
            "avg_max_drawdown": (
                np.mean(model_metrics["max_drawdown"])
                if model_metrics["max_drawdown"]
                else None
            ),
            "avg_win_rate": (
                np.mean(model_metrics["win_rate"])
                if model_metrics["win_rate"]
                else None
            ),
            "success_count": sum(1 for m in model_metrics["accuracy"] if m is not None),
            "by_regime": {},
        }

        # Calculate model performance by regime
        for regime in regimes:
            r_metrics = regime_metrics[regime]

            # Only add regime data if we have results
            if r_metrics["accuracy"]:
                summary["models"][model_name]["by_regime"][regime] = {
                    "avg_accuracy": np.mean(r_metrics["accuracy"]),
                    "avg_f1": np.mean(r_metrics["f1"]),
                    "avg_total_return": np.mean(r_metrics["total_return"]),
                    "avg_sharpe_ratio": np.mean(r_metrics["sharpe_ratio"]),
                    "avg_max_drawdown": np.mean(r_metrics["max_drawdown"]),
                    "avg_win_rate": np.mean(r_metrics["win_rate"]),
                    "sample_count": int(np.sum(r_metrics["sample_count"])),
                    "period_count": int(np.sum(r_metrics["period_count"])),
                    "success_count": len(r_metrics["accuracy"]),
                }

                # Update regime summary data
                summary["volatility_regimes"][regime]["sample_count"] += int(
                    np.sum(r_metrics["sample_count"])
                )
                summary["volatility_regimes"][regime]["period_count"] += int(
                    np.sum(r_metrics["period_count"])
                )

                # Add model performance to regime summary
                if model_name not in summary["volatility_regimes"][regime]["models"]:
                    summary["volatility_regimes"][regime]["models"][model_name] = {
                        "avg_win_rate": np.mean(r_metrics["win_rate"]),
                        "avg_return": np.mean(r_metrics["total_return"]),
                    }

    # Calculate comparison with classical models - overall and by regime
    classical_comparison = {}
    by_regime_comparison = {regime: {} for regime in regimes}

    for model_name in model_names:
        if "Quantum" in model_name:  # Only compare quantum models
            wins = 0
            losses = 0
            ties = 0
            total = 0

            # Track by regime
            regime_stats = {
                regime: {"wins": 0, "losses": 0, "ties": 0, "total": 0}
                for regime in regimes
            }

            for symbol, symbol_results in results.items():
                for regime, regime_results in symbol_results.items():
                    if (
                        model_name in regime_results
                        and "benchmark_comparison" in regime_results[model_name]
                    ):

                        benchmark = regime_results[model_name]["benchmark_comparison"]
                        quantum_acc = benchmark.get(model_name, {}).get("accuracy", 0)

                        for classical_model, metrics in benchmark.items():
                            if (
                                "Random" in classical_model
                                or "Logistic" in classical_model
                            ):
                                classical_acc = metrics.get("accuracy", 0)
                                total += 1
                                regime_stats[regime]["total"] += 1

                                if (
                                    quantum_acc > classical_acc + 0.02
                                ):  # 2% better is a win
                                    wins += 1
                                    regime_stats[regime]["wins"] += 1
                                elif (
                                    classical_acc > quantum_acc + 0.02
                                ):  # 2% worse is a loss
                                    losses += 1
                                    regime_stats[regime]["losses"] += 1
                                else:
                                    ties += 1
                                    regime_stats[regime]["ties"] += 1

            if total > 0:
                classical_comparison[model_name] = {
                    "wins": wins,
                    "losses": losses,
                    "ties": ties,
                    "win_rate": wins / total if total > 0 else 0,
                }

                # Add by-regime stats
                for regime, stats in regime_stats.items():
                    if stats["total"] > 0:
                        if model_name not in by_regime_comparison[regime]:
                            by_regime_comparison[regime][model_name] = {}

                        by_regime_comparison[regime][model_name] = {
                            "wins": stats["wins"],
                            "losses": stats["losses"],
                            "ties": stats["ties"],
                            "win_rate": (
                                stats["wins"] / stats["total"]
                                if stats["total"] > 0
                                else 0
                            ),
                        }

    summary["classical_comparison"] = classical_comparison
    summary["classical_comparison_by_regime"] = by_regime_comparison

    # Calculate volatility robustness - the consistency of win rates across regimes
    volatility_robustness = {}

    for model_name in model_names:
        # Collect win rates by regime
        win_rates = []
        for regime in regimes:
            if (
                regime in summary["volatility_regimes"]
                and model_name in summary["volatility_regimes"][regime]["models"]
            ):
                win_rate = summary["volatility_regimes"][regime]["models"][model_name][
                    "avg_win_rate"
                ]
                win_rates.append(win_rate)

        # Calculate volatility robustness (max difference in win rates)
        if len(win_rates) >= 2:
            robustness = max(win_rates) - min(win_rates)
            volatility_robustness[model_name] = {
                "max_win_rate": max(win_rates),
                "min_win_rate": min(win_rates),
                "performance_differential": robustness
                * 100,  # Convert to percentage points
                "is_robust": robustness
                <= 0.1,  # Less than 10 percentage points difference is considered robust
            }

    summary["volatility_robustness"] = volatility_robustness

    # Calculate best model overall and by regime
    best_model = None
    best_return = -float("inf")

    best_by_regime = {}

    # Overall best model
    for model_name, metrics in summary["models"].items():
        if (
            metrics["avg_total_return"] is not None
            and metrics["avg_total_return"] > best_return
        ):
            best_return = metrics["avg_total_return"]
            best_model = model_name

    summary["overall"]["best_model"] = best_model
    summary["overall"]["best_return"] = best_return

    # Best model by regime
    for regime in regimes:
        if regime in summary["volatility_regimes"]:
            regime_best_model = None
            regime_best_return = -float("inf")

            for model_name, metrics in summary["volatility_regimes"][regime][
                "models"
            ].items():
                if metrics["avg_return"] > regime_best_return:
                    regime_best_return = metrics["avg_return"]
                    regime_best_model = model_name

            if regime_best_model:
                best_by_regime[regime] = {
                    "model": regime_best_model,
                    "return": regime_best_return,
                    "win_rate": summary["volatility_regimes"][regime]["models"][
                        regime_best_model
                    ]["avg_win_rate"],
                }

    summary["overall"]["best_by_regime"] = best_by_regime

    # Save summary report
    with open(os.path.join(output_dir, "overall_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Create visualization
    create_comparison_charts(summary, output_dir)

    return summary


def create_comparison_charts(summary: Dict[str, Any], output_dir: str):
    """
    Create visualization charts comparing model performance across volatility regimes

    Args:
        summary: Summary metrics dictionary
        output_dir: Directory to save charts
    """
    # Create figure for model comparison
    plt.figure(figsize=(12, 8))

    # Extract model names and returns
    models = []
    returns = []
    accuracies = []

    for model_name, metrics in summary["models"].items():
        if metrics["avg_total_return"] is not None:
            models.append(model_name)
            returns.append(metrics["avg_total_return"])
            accuracies.append(
                metrics["avg_accuracy"] if metrics["avg_accuracy"] is not None else 0
            )

    # Plot returns comparison
    plt.subplot(2, 1, 1)
    bars = plt.bar(models, returns)

    # Color bars based on model type
    for i, model in enumerate(models):
        if "Quantum" in model:
            bars[i].set_color("blue")
        else:
            bars[i].set_color("green")

    plt.title("Average Return by Model")
    plt.ylabel("Return")
    plt.xticks(rotation=45)
    plt.grid(axis="y", alpha=0.3)

    # Plot accuracy comparison
    plt.subplot(2, 1, 2)
    bars = plt.bar(models, accuracies)

    # Color bars based on model type
    for i, model in enumerate(models):
        if "Quantum" in model:
            bars[i].set_color("blue")
        else:
            bars[i].set_color("green")

    plt.title("Average Accuracy by Model")
    plt.ylabel("Accuracy")
    plt.xticks(rotation=45)
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "model_comparison.png"), dpi=300)

    # Create win/loss chart for quantum vs classical
    if "classical_comparison" in summary:
        plt.figure(figsize=(10, 6))

        quantum_models = list(summary["classical_comparison"].keys())
        win_rates = [
            summary["classical_comparison"][m]["win_rate"] for m in quantum_models
        ]

        plt.bar(quantum_models, win_rates, color="purple")
        plt.title("Win Rate Against Classical Models")
        plt.ylabel("Win Rate")
        plt.ylim(0, 1)
        plt.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "quantum_vs_classical.png"), dpi=300)

    # Create volatility regime performance chart
    if "volatility_regimes" in summary and len(summary["volatility_regimes"]) > 1:
        # Get all volatility regimes and models
        regimes = sorted(list(summary["volatility_regimes"].keys()))
        quantum_models = [m for m in models if "Quantum" in m]

        if quantum_models and regimes:
            # Create figure with subplots for win rate and return by regime
            plt.figure(figsize=(14, 10))

            # Extract win rate data for each model by regime
            model_win_rates = {model: [] for model in quantum_models}
            model_returns = {model: [] for model in quantum_models}

            # Set up colors for models
            colors = [
                "blue",
                "green",
                "red",
                "orange",
                "purple",
                "brown",
                "pink",
                "gray",
            ]
            model_colors = {
                model: colors[i % len(colors)] for i, model in enumerate(quantum_models)
            }

            for regime in regimes:
                if regime in summary["volatility_regimes"]:
                    regime_models = summary["volatility_regimes"][regime]["models"]
                    for model in quantum_models:
                        if model in regime_models:
                            model_win_rates[model].append(
                                regime_models[model]["avg_win_rate"]
                            )
                            model_returns[model].append(
                                regime_models[model]["avg_return"]
                            )
                        else:
                            # No data for this model in this regime
                            model_win_rates[model].append(0)
                            model_returns[model].append(0)

            # Plot win rates
            plt.subplot(2, 1, 1)

            # Plot lines for each model
            for model in quantum_models:
                plt.plot(
                    regimes,
                    model_win_rates[model],
                    marker="o",
                    label=model,
                    color=model_colors[model],
                )

            plt.title("Win Rate by Volatility Regime")
            plt.ylabel("Win Rate")
            plt.ylim(0, 1)
            plt.grid(True, alpha=0.3)
            plt.legend()

            # Plot returns
            plt.subplot(2, 1, 2)

            # Plot lines for each model
            for model in quantum_models:
                plt.plot(
                    regimes,
                    model_returns[model],
                    marker="o",
                    label=model,
                    color=model_colors[model],
                )

            plt.title("Return by Volatility Regime")
            plt.ylabel("Return %")
            plt.grid(True, alpha=0.3)
            plt.legend()

            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "performance_by_regime.png"), dpi=300)

            # Create volatility robustness chart
            if "volatility_robustness" in summary:
                plt.figure(figsize=(12, 6))

                # Extract volatility robustness data
                robust_models = []
                performance_diffs = []

                for model, metrics in summary["volatility_robustness"].items():
                    if "performance_differential" in metrics:
                        robust_models.append(model)
                        performance_diffs.append(metrics["performance_differential"])

                if robust_models:
                    # Sort by performance differential (robustness)
                    sorted_indices = np.argsort(performance_diffs)
                    sorted_models = [robust_models[i] for i in sorted_indices]
                    sorted_diffs = [performance_diffs[i] for i in sorted_indices]

                    # Plot bars
                    bars = plt.bar(sorted_models, sorted_diffs)

                    # Color bars based on robustness threshold
                    for i, diff in enumerate(sorted_diffs):
                        if diff <= 10:  # Good robustness
                            bars[i].set_color("green")
                        elif diff <= 15:  # Acceptable
                            bars[i].set_color("yellow")
                        else:  # Poor
                            bars[i].set_color("red")

                    plt.title(
                        "Volatility Robustness - Win Rate Consistency Across Regimes"
                    )
                    plt.ylabel("Performance Differential (pp)")
                    plt.axhline(
                        y=10, color="green", linestyle="--", label="Target (10pp)"
                    )
                    plt.xticks(rotation=45)
                    plt.grid(axis="y", alpha=0.3)
                    plt.legend()

                    plt.tight_layout()
                    plt.savefig(
                        os.path.join(output_dir, "volatility_robustness.png"), dpi=300
                    )


async def main():
    """Main entry point for the evaluation script"""
    parser = argparse.ArgumentParser(
        description="Evaluate quantum models on market data across volatility regimes"
    )

    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "SPY", "QQQ"],
        help="Stock symbols to evaluate",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default="2018-01-01",
        help="Start date for data (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default="2023-12-31",
        help="End date for data (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="evaluation_results",
        help="Directory to save results",
    )
    parser.add_argument(
        "--n_qubits",
        type=int,
        default=4,
        help="Number of qubits to use in quantum models",
    )
    parser.add_argument(
        "--no_classical",
        action="store_true",
        help="Skip comparing with classical models",
    )
    parser.add_argument(
        "--no_volatility_test",
        action="store_true",
        help="Skip testing across volatility regimes",
    )
    parser.add_argument(
        "--extended_symbols",
        action="store_true",
        help="Include an extended set of symbols for more comprehensive testing",
    )

    args = parser.parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # Use extended symbol set if requested
    if args.extended_symbols:
        # Add more diverse symbols for better coverage
        args.symbols.extend(
            [
                "VIX",  # Volatility index
                "GLD",  # Gold
                "TLT",  # Long-term Treasury bonds
                "XLE",  # Energy sector
                "XLF",  # Financial sector
                "XLK",  # Technology sector
                "XLV",  # Healthcare sector
                "ARKK",  # Innovation ETF (high volatility)
                "VNQ",  # Real Estate
                "IWM",  # Small caps
            ]
        )
        logger.info(f"Using extended symbol set with {len(args.symbols)} symbols")

    # Create MarketDataService instance
    # Note: In a real implementation, this would be properly initialized
    # with authentication keys and configuration
    data_service = MarketDataService(
        alpha_vantage_api_key=os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
        finnhub_api_key=os.environ.get("FINNHUB_API_KEY", ""),
        fmp_api_key=os.environ.get("FMP_API_KEY", ""),
    )

    # Run evaluation
    try:
        logger.info(
            f"Starting evaluation of {len(args.symbols)} symbols from {args.start_date} to {args.end_date}"
        )
        logger.info(
            f"Volatility regime testing: {'ENABLED' if not args.no_volatility_test else 'DISABLED'}"
        )

        summary = await run_evaluation(
            symbols=args.symbols,
            start_date=start_date,
            end_date=end_date,
            data_service=data_service,
            output_dir=args.output_dir,
            n_qubits=args.n_qubits,
            include_classical_models=not args.no_classical,
            volatility_regime_test=not args.no_volatility_test,
        )

        # Print summary
        logger.info(f"Evaluation complete. Results saved to {args.output_dir}")
        if "overall" in summary and "best_model" in summary["overall"]:
            logger.info(f"Best performing model: {summary['overall']['best_model']}")
            logger.info(f"Best average return: {summary['overall']['best_return']:.4f}")

    except Exception as e:
        logger.error(f"Error in evaluation: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
