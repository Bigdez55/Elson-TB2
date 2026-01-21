"""
Change point detection algorithms for detecting regime changes in financial time series.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt
from scipy.stats import norm
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


class ChangePointDetector:
    """Base class for change point detection algorithms"""

    def __init__(self):
        self.name = "base_change_point_detector"

    def detect(self, data: np.ndarray, **kwargs) -> List[int]:
        """
        Detect change points in the time series

        Args:
            data: Input time series
            **kwargs: Additional parameters

        Returns:
            List of detected change point indices
        """
        raise NotImplementedError("Subclasses must implement detect method")

    def plot_change_points(
        self,
        data: np.ndarray,
        change_points: List[int],
        ax: Optional[plt.Axes] = None,
        title: str = "Change Point Detection",
        figsize: Tuple[int, int] = (12, 6),
    ) -> plt.Figure:
        """
        Plot the time series with detected change points

        Args:
            data: Input time series
            change_points: List of detected change point indices
            ax: Matplotlib axes (if None, a new figure is created)
            title: Title of the plot
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.figure

        # Plot the time series
        ax.plot(data, label="Time Series")

        # Plot change points
        for cp in change_points:
            if cp < len(data):
                ax.axvline(x=cp, color="r", linestyle="--", alpha=0.7)

        # Add labels and title
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.set_title(title)
        ax.legend()

        return fig


class BinarySegmentation(ChangePointDetector):
    """Change point detection using the binary segmentation algorithm"""

    def __init__(self, min_size: int = 30):
        """
        Initialize the binary segmentation detector

        Args:
            min_size: Minimum segment size
        """
        super().__init__()
        self.name = "binary_segmentation"
        self.min_size = min_size

    def detect(
        self,
        data: np.ndarray,
        n_changepoints: int = 5,
        penalty: Optional[float] = None,
        model: str = "l2",
    ) -> List[int]:
        """
        Detect change points using binary segmentation

        Args:
            data: Input time series
            n_changepoints: Maximum number of change points to detect
            penalty: Penalty for the cost function (if None, uses a default value)
            model: Cost model ("l1", "l2", "rbf", "linear", etc.)

        Returns:
            List of detected change point indices
        """
        # Use ruptures package for binary segmentation
        if len(data.shape) == 1:
            # Reshape to 2D for ruptures
            data_2d = data.reshape(-1, 1)
        else:
            data_2d = data

        # Create the algorithm
        algo = rpt.Binseg(model=model, min_size=self.min_size)

        # Fit the algorithm
        algo.fit(data_2d)

        # Compute optimal segmentation
        if penalty is not None:
            # With penalty value
            change_points = algo.predict(pen=penalty)
        else:
            # With predefined number of change points
            change_points = algo.predict(n_bkps=n_changepoints)

        # Remove the last point (it's always the end of the time series)
        if change_points and change_points[-1] == len(data):
            change_points = change_points[:-1]

        return change_points


class PELT(ChangePointDetector):
    """Change point detection using the PELT algorithm (Pruned Exact Linear Time)"""

    def __init__(self, min_size: int = 30):
        """
        Initialize the PELT detector

        Args:
            min_size: Minimum segment size
        """
        super().__init__()
        self.name = "pelt"
        self.min_size = min_size

    def detect(
        self, data: np.ndarray, penalty: Optional[float] = None, model: str = "l2"
    ) -> List[int]:
        """
        Detect change points using PELT

        Args:
            data: Input time series
            penalty: Penalty for the cost function (if None, uses a default value)
            model: Cost model ("l1", "l2", "rbf", "linear", etc.)

        Returns:
            List of detected change point indices
        """
        # Use ruptures package for PELT
        if len(data.shape) == 1:
            # Reshape to 2D for ruptures
            data_2d = data.reshape(-1, 1)
        else:
            data_2d = data

        # Create the algorithm
        algo = rpt.Pelt(model=model, min_size=self.min_size)

        # Fit the algorithm
        algo.fit(data_2d)

        # Compute optimal segmentation
        if penalty is not None:
            # Use provided penalty
            pen = penalty
        else:
            # Use a heuristic for penalty
            pen = np.log(len(data)) * np.std(data) * 0.5

        change_points = algo.predict(pen=pen)

        # Remove the last point (it's always the end of the time series)
        if change_points and change_points[-1] == len(data):
            change_points = change_points[:-1]

        return change_points


class WindowBasedDetector(ChangePointDetector):
    """Change point detection using a window-based approach"""

    def __init__(self, window_size: int = 50, overlap: int = 25):
        """
        Initialize the window-based detector

        Args:
            window_size: Size of the sliding window
            overlap: Overlap between windows
        """
        super().__init__()
        self.name = "window_based"
        self.window_size = window_size
        self.overlap = overlap

    def detect(
        self, data: np.ndarray, threshold: float = 2.0, metric: str = "mean"
    ) -> List[int]:
        """
        Detect change points using window-based statistics

        Args:
            data: Input time series
            threshold: Threshold for detecting change points
            metric: Metric to compare windows ("mean", "var", "std")

        Returns:
            List of detected change point indices
        """
        if len(data) < 2 * self.window_size:
            logger.warning(
                f"Data length ({len(data)}) is less than 2 * window_size ({2 * self.window_size})"
            )
            return []

        # Choose the appropriate statistic function
        if metric == "mean":
            stat_func = np.mean
        elif metric == "var":
            stat_func = np.var
        elif metric == "std":
            stat_func = np.std
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        # Calculate statistics for sliding windows
        change_points = []

        # Step size is window_size - overlap
        step = self.window_size - self.overlap

        for i in range(0, len(data) - 2 * self.window_size + 1, step):
            # Calculate statistics for two adjacent windows
            left_window = data[i : i + self.window_size]
            right_window = data[i + self.window_size : i + 2 * self.window_size]

            left_stat = stat_func(left_window)
            right_stat = stat_func(right_window)

            # Calculate the difference
            if left_stat == 0:
                # Avoid division by zero
                diff = np.abs(right_stat - left_stat)
            else:
                diff = np.abs(right_stat - left_stat) / np.abs(left_stat)

            # Check if it exceeds the threshold
            if diff > threshold:
                change_points.append(i + self.window_size)

        # If no change points were detected, return an empty list
        if not change_points:
            return []

        # Remove duplicates and sort
        change_points = sorted(list(set(change_points)))

        # Merge change points that are close to each other
        merged_change_points = [change_points[0]]

        for cp in change_points[1:]:
            if cp - merged_change_points[-1] > self.window_size // 2:
                merged_change_points.append(cp)

        return merged_change_points


class BayesianChangePointDetector(ChangePointDetector):
    """Change point detection using a Bayesian approach"""

    def __init__(self, hazard_rate: float = 0.01):
        """
        Initialize the Bayesian change point detector

        Args:
            hazard_rate: Prior probability of a change point
        """
        super().__init__()
        self.name = "bayesian"
        self.hazard_rate = hazard_rate

    def detect(
        self, data: np.ndarray, threshold: float = 0.5, prior_var: float = 1.0
    ) -> List[int]:
        """
        Detect change points using a Bayesian approach

        Args:
            data: Input time series
            threshold: Threshold for posterior probability
            prior_var: Prior variance

        Returns:
            List of detected change point indices
        """
        n = len(data)

        # Initialize run length distribution
        run_length = np.zeros((n + 1, n + 1))
        run_length[0, 0] = 1.0

        # Initialize message passing variables
        mean = np.zeros((n + 1, n + 1))
        var = np.zeros((n + 1, n + 1))

        # Initialize for r = 0
        mean[0, 0] = 0.0
        var[0, 0] = prior_var

        # Compute run length distribution
        for t in range(1, n + 1):
            # Growth probabilities
            growth_probs = np.zeros(t + 1)
            for r in range(t):
                if run_length[r, t - 1] > 0:
                    # Compute predictive probability
                    pred_mean = mean[r, t - 1]
                    pred_var = var[r, t - 1]

                    # Compute likelihood
                    likelihood = norm.pdf(data[t - 1], pred_mean, np.sqrt(pred_var))

                    # Update run length
                    growth_probs[r + 1] = (
                        run_length[r, t - 1] * (1 - self.hazard_rate) * likelihood
                    )

            # Change point probability
            cp_prob = (
                np.sum(run_length[:t, t - 1])
                * self.hazard_rate
                * norm.pdf(data[t - 1], 0, np.sqrt(prior_var))
            )
            growth_probs[0] = cp_prob

            # Normalize
            growth_probs = growth_probs / np.sum(growth_probs)

            # Update run length distribution
            run_length[: t + 1, t] = growth_probs

            # Update message passing variables
            for r in range(t + 1):
                if r == 0:
                    # Change point
                    mean[r, t] = data[t - 1]
                    var[r, t] = prior_var
                else:
                    # No change point
                    n_r = r
                    prev_mean = mean[r - 1, t - 1]
                    prev_var = var[r - 1, t - 1]

                    # Update mean and variance
                    var[r, t] = 1.0 / (1.0 / prev_var + 1.0)
                    mean[r, t] = var[r, t] * (prev_mean / prev_var + data[t - 1])

        # Extract change points
        change_points = []

        # Compute change point probabilities
        cp_probs = np.zeros(n)

        for t in range(1, n):
            cp_probs[t] = run_length[0, t + 1]

        # Find change points
        for t in range(1, n):
            if cp_probs[t] > threshold:
                change_points.append(t)

        return change_points


def detect_regime_changes(
    data: pd.DataFrame,
    column: str = "close",
    detector_type: str = "binary_segmentation",
    n_changepoints: int = 5,
    plot: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Detect regime changes in price data

    Args:
        data: DataFrame with price data
        column: Column to analyze
        detector_type: Type of detector to use
        n_changepoints: Number of change points to detect
        plot: Whether to generate a plot
        **kwargs: Additional parameters for the detector

    Returns:
        Dictionary with change points and other information
    """
    # Extract the data
    values = data[column].values

    # Create the detector
    if detector_type == "binary_segmentation":
        detector = BinarySegmentation(**kwargs)
    elif detector_type == "pelt":
        detector = PELT(**kwargs)
    elif detector_type == "window_based":
        detector = WindowBasedDetector(**kwargs)
    elif detector_type == "bayesian":
        detector = BayesianChangePointDetector(**kwargs)
    else:
        raise ValueError(f"Unsupported detector type: {detector_type}")

    # Detect change points
    change_points = detector.detect(values, n_changepoints=n_changepoints)

    # Convert to actual data points
    change_points_dates = [data.index[cp] for cp in change_points if cp < len(data)]

    # Create result dictionary
    result = {
        "change_points": change_points,
        "change_points_dates": change_points_dates,
        "detector_type": detector_type,
        "detector_params": kwargs,
    }

    # Generate plot if requested
    if plot:
        fig = detector.plot_change_points(
            values, change_points, title=f"Change Point Detection ({detector_type})"
        )
        result["figure"] = fig

    return result


def define_market_regimes(
    data: pd.DataFrame,
    change_points: List[int],
    column: str = "close",
    n_regimes: int = 3,
) -> pd.DataFrame:
    """
    Define market regimes based on detected change points

    Args:
        data: DataFrame with price data
        change_points: List of change point indices
        column: Column to analyze
        n_regimes: Number of regimes to identify

    Returns:
        DataFrame with added 'regime' column
    """
    # Create a copy of the data
    result_df = data.copy()

    # Add segment column
    segment = np.zeros(len(data))

    # Mark segments based on change points
    for i, cp in enumerate(change_points):
        if cp < len(data):
            segment[cp:] = i + 1

    result_df["segment"] = segment

    # Extract features for clustering
    segments = []
    for i in range(int(np.max(segment)) + 1):
        segment_data = result_df[result_df["segment"] == i]

        if len(segment_data) > 0:
            # Calculate segment features
            mean_return = segment_data[column].pct_change().mean()
            std_return = segment_data[column].pct_change().std()
            trend = (
                (segment_data[column].iloc[-1] / segment_data[column].iloc[0] - 1)
                if len(segment_data) > 1
                else 0
            )

            segments.append([mean_return, std_return, trend])

    if not segments:
        # No segments found
        result_df["regime"] = 0
        return result_df

    # Cluster segments into regimes
    kmeans = KMeans(n_clusters=min(n_regimes, len(segments)), random_state=42)
    regimes = kmeans.fit_predict(segments)

    # Map segments to regimes
    segment_to_regime = {}
    for i, regime in enumerate(regimes):
        segment_to_regime[i] = regime

    # Add regime column
    result_df["regime"] = result_df["segment"].map(segment_to_regime)

    # Analyze regimes
    regime_stats = {}
    for regime in range(n_regimes):
        regime_data = result_df[result_df["regime"] == regime]

        if len(regime_data) > 0:
            mean_return = regime_data[column].pct_change().mean()
            std_return = regime_data[column].pct_change().std()
            trend = (
                (regime_data[column].iloc[-1] / regime_data[column].iloc[0] - 1)
                if len(regime_data) > 1
                else 0
            )

            # Classify regime
            if trend > 0.03:
                regime_type = "bullish"
            elif trend < -0.03:
                regime_type = "bearish"
            elif std_return > 0.015:
                regime_type = "volatile"
            else:
                regime_type = "sideways"

            regime_stats[regime] = {
                "mean_return": mean_return,
                "std_return": std_return,
                "trend": trend,
                "type": regime_type,
            }

    # Map regime types back to the DataFrame
    result_df["regime_type"] = result_df["regime"].map(
        lambda x: regime_stats.get(x, {}).get("type", "unknown")
    )

    return result_df
