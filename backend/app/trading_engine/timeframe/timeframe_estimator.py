"""
Timeframe estimation for trading signals.
Estimates the appropriate timeframe for a prediction based on market conditions.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from .change_point_detector import define_market_regimes, detect_regime_changes

logger = logging.getLogger(__name__)


class TimeframeEstimator:
    """
    Estimates the appropriate timeframe for trading based on market conditions
    """

    def __init__(self, timeframes: List[str] = ["1d", "3d", "1w", "2w", "1m"]):
        """
        Initialize the timeframe estimator

        Args:
            timeframes: List of timeframes to consider
        """
        self.timeframes = timeframes
        self.timeframe_mapping = {tf: i for i, tf in enumerate(timeframes)}
        self.model = None
        self.feature_names = None

    def extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features for timeframe estimation

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with extracted features
        """
        # Ensure we have required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Input data must contain columns: {required_cols}")

        # Create a copy to avoid modifying the original
        df = data.copy()

        # Calculate basic price features
        df["returns"] = df["close"].pct_change()
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))

        # Calculate volatility
        df["volatility_10d"] = df["returns"].rolling(window=10).std()
        df["volatility_20d"] = df["returns"].rolling(window=20).std()

        # Calculate momentum
        df["momentum_5d"] = df["returns"].rolling(window=5).sum()
        df["momentum_10d"] = df["returns"].rolling(window=10).sum()

        # Calculate volume features
        df["volume_change"] = df["volume"].pct_change()
        df["volume_ma_ratio"] = df["volume"] / df["volume"].rolling(window=20).mean()

        # Calculate trend indicators
        df["ma_5"] = df["close"].rolling(window=5).mean()
        df["ma_20"] = df["close"].rolling(window=20).mean()
        df["ma_50"] = df["close"].rolling(window=50).mean()

        df["trend_5_20"] = df["ma_5"] / df["ma_20"] - 1
        df["trend_5_50"] = df["ma_5"] / df["ma_50"] - 1
        df["trend_20_50"] = df["ma_20"] / df["ma_50"] - 1

        # Calculate price range
        df["daily_range"] = (df["high"] - df["low"]) / df["close"]
        df["daily_range_ma5"] = df["daily_range"].rolling(window=5).mean()

        # Detect regime changes
        result = detect_regime_changes(df, column="close", n_changepoints=3, plot=False)
        change_points = result["change_points"]

        # Define market regimes
        regime_df = define_market_regimes(
            df, change_points, column="close", n_regimes=4
        )

        # Add regime information
        df["regime"] = regime_df["regime"]
        df["regime_type"] = regime_df["regime_type"]

        # Process categorical variables
        regime_dummies = pd.get_dummies(df["regime_type"], prefix="regime")
        df = pd.concat([df, regime_dummies], axis=1)

        # Drop NaN values
        df = df.dropna()

        return df

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepare features for model input

        Args:
            df: DataFrame with extracted features

        Returns:
            Feature array
        """
        # Select numeric features
        features = [
            "volatility_10d",
            "volatility_20d",
            "momentum_5d",
            "momentum_10d",
            "volume_ma_ratio",
            "trend_5_20",
            "trend_5_50",
            "trend_20_50",
            "daily_range_ma5",
        ]

        # Add regime dummy variables if they exist
        regime_features = [col for col in df.columns if col.startswith("regime_")]
        features.extend(regime_features)

        # Store feature names for later use
        self.feature_names = features

        # Extract feature array
        X = df[features].values

        return X

    def fit(
        self,
        X_data: Union[pd.DataFrame, np.ndarray],
        y_data: Union[pd.Series, np.ndarray, List[str]],
        extract_features: bool = False,
        test_size: float = 0.2,
        random_state: int = 42,
        n_estimators: int = 100,
    ) -> "TimeframeEstimator":
        """
        Train the timeframe estimator model

        Args:
            X_data: Input data (either a DataFrame with OHLCV data or pre-extracted features)
            y_data: Target timeframes (either strings from self.timeframes or already encoded as integers)
            extract_features: Whether to extract features from X_data
            test_size: Test set size for evaluation
            random_state: Random state for train-test split
            n_estimators: Number of trees in the random forest

        Returns:
            Self
        """
        # Process input data
        if extract_features:
            if not isinstance(X_data, pd.DataFrame):
                raise ValueError(
                    "X_data must be a DataFrame when extract_features=True"
                )

            # Extract features
            feature_df = self.extract_features(X_data)
            X = self.prepare_features(feature_df)
        else:
            X = X_data

        # Process target data
        if isinstance(y_data, (list, pd.Series)) and isinstance(y_data[0], str):
            # Convert string timeframes to integers
            y = np.array([self.timeframe_mapping[tf] for tf in y_data])
        else:
            y = np.array(y_data)

        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Initialize and train the model
        self.model = RandomForestClassifier(
            n_estimators=n_estimators, random_state=random_state
        )

        self.model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"Timeframe estimator trained with accuracy: {accuracy:.4f}")
        logger.info(f"Classification report:\n{classification_report(y_test, y_pred)}")

        return self

    def predict(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        extract_features: bool = False,
        return_probabilities: bool = False,
    ) -> Union[List[str], Tuple[List[str], np.ndarray]]:
        """
        Predict the optimal timeframe

        Args:
            data: Input data (either a DataFrame with OHLCV data or pre-extracted features)
            extract_features: Whether to extract features from data
            return_probabilities: Whether to return probabilities

        Returns:
            List of predicted timeframes, or tuple of (timeframes, probabilities)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")

        # Process input data
        if extract_features:
            if not isinstance(data, pd.DataFrame):
                raise ValueError("data must be a DataFrame when extract_features=True")

            # Extract features
            feature_df = self.extract_features(data)
            X = self.prepare_features(feature_df)
        else:
            X = data

        # Make predictions
        if return_probabilities:
            # Get predicted class and probabilities
            y_pred = self.model.predict(X)
            proba = self.model.predict_proba(X)

            # Convert class indices to timeframe strings
            timeframes = [self.timeframes[idx] for idx in y_pred]

            return timeframes, proba
        else:
            # Get predicted class
            y_pred = self.model.predict(X)

            # Convert class indices to timeframe strings
            timeframes = [self.timeframes[idx] for idx in y_pred]

            return timeframes

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importances from the model

        Returns:
            DataFrame with feature importances
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")

        if self.feature_names is None:
            # Use generic feature names
            feature_names = [f"feature_{i}" for i in range(self.model.n_features_in_)]
        else:
            feature_names = self.feature_names

        # Extract feature importances
        importances = self.model.feature_importances_

        # Create DataFrame
        importance_df = pd.DataFrame(
            {"feature": feature_names, "importance": importances}
        )

        # Sort by importance
        importance_df = importance_df.sort_values("importance", ascending=False)

        return importance_df

    def plot_feature_importance(
        self, top_n: int = 10, figsize: Tuple[int, int] = (10, 6)
    ) -> plt.Figure:
        """
        Plot feature importances

        Args:
            top_n: Number of top features to plot
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        # Get feature importances
        importance_df = self.get_feature_importance()

        # Select top N features
        top_features = importance_df.head(top_n)

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        # Create horizontal bar plot
        ax.barh(top_features["feature"], top_features["importance"])

        # Add labels and title
        ax.set_xlabel("Importance")
        ax.set_ylabel("Feature")
        ax.set_title("Feature Importance for Timeframe Estimation")

        # Invert y-axis to show most important at the top
        ax.invert_yaxis()

        return fig


class EventBasedTimeframeEstimator:
    """
    Estimates timeframes based on detected events in financial markets
    """

    def __init__(self, event_weights: Dict[str, float] = None):
        """
        Initialize the event-based timeframe estimator

        Args:
            event_weights: Dictionary mapping event types to their weights
        """
        # Default event weights
        if event_weights is None:
            self.event_weights = {
                "earnings": 0.8,
                "fed_announcement": 0.9,
                "economic_data": 0.7,
                "geopolitical": 0.6,
                "trend_change": 0.8,
                "volatility_change": 0.7,
                "volume_spike": 0.5,
                "news_sentiment": 0.6,
            }
        else:
            self.event_weights = event_weights

        # Timeframe mappings (event strength to timeframe)
        self.timeframe_mappings = {
            "very_short": "1d",
            "short": "3d",
            "medium": "1w",
            "long": "2w",
            "very_long": "1m",
        }

        # Default event impacts on timeframe
        self.default_event_impact = {
            "earnings": {"high": "short", "medium": "medium", "low": "long"},
            "fed_announcement": {"high": "short", "medium": "medium", "low": "medium"},
            "economic_data": {"high": "short", "medium": "medium", "low": "long"},
            "geopolitical": {"high": "medium", "medium": "long", "low": "very_long"},
            "trend_change": {"high": "very_short", "medium": "short", "low": "medium"},
            "volatility_change": {
                "high": "very_short",
                "medium": "short",
                "low": "medium",
            },
            "volume_spike": {"high": "short", "medium": "medium", "low": "long"},
            "news_sentiment": {"high": "short", "medium": "medium", "low": "long"},
        }

    def calculate_event_strength(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate the strength of each event

        Args:
            events: List of event dictionaries, each with 'type' and 'impact' keys

        Returns:
            List of events with added 'strength' key
        """
        for event in events:
            event_type = event["type"]
            impact = event.get("impact", "medium")

            # Get weight for this event type
            weight = self.event_weights.get(event_type, 0.5)

            # Calculate strength based on impact
            if impact == "high":
                strength = weight * 1.0
            elif impact == "medium":
                strength = weight * 0.6
            elif impact == "low":
                strength = weight * 0.3
            else:
                strength = weight * 0.5

            # Add strength to the event
            event["strength"] = strength

        return events

    def recommend_timeframe(
        self, events: List[Dict[str, Any]], method: str = "weighted_avg"
    ) -> str:
        """
        Recommend a timeframe based on detected events

        Args:
            events: List of event dictionaries
            method: Method for combining events ('weighted_avg', 'max_impact', 'entropy')

        Returns:
            Recommended timeframe
        """
        if not events:
            # Default to medium timeframe if no events
            return self.timeframe_mappings["medium"]

        # Calculate event strengths
        events = self.calculate_event_strength(events)

        if method == "weighted_avg":
            # Weighted average of event impacts
            total_strength = 0
            total_weight = 0

            for event in events:
                strength = event["strength"]
                weight = self.event_weights.get(event["type"], 0.5)

                total_strength += strength * weight
                total_weight += weight

            if total_weight == 0:
                avg_strength = 0.5
            else:
                avg_strength = total_strength / total_weight

            # Map average strength to timeframe
            if avg_strength >= 0.8:
                return self.timeframe_mappings["very_short"]
            elif avg_strength >= 0.6:
                return self.timeframe_mappings["short"]
            elif avg_strength >= 0.4:
                return self.timeframe_mappings["medium"]
            elif avg_strength >= 0.2:
                return self.timeframe_mappings["long"]
            else:
                return self.timeframe_mappings["very_long"]

        elif method == "max_impact":
            # Use timeframe of the highest impact event
            max_event = max(events, key=lambda x: x["strength"])
            event_type = max_event["type"]
            impact = max_event.get("impact", "medium")

            # Get timeframe from default impact mappings
            timeframe_key = self.default_event_impact.get(event_type, {}).get(
                impact, "medium"
            )
            return self.timeframe_mappings[timeframe_key]

        elif method == "entropy":
            # Use uncertainty (entropy) to determine timeframe
            # Higher entropy (more uncertainty) -> longer timeframe

            # Count event types
            event_counts = {}
            for event in events:
                event_type = event["type"]
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Calculate entropy
            total_events = len(events)
            probabilities = [count / total_events for count in event_counts.values()]
            ent = entropy(probabilities)

            # Normalize entropy (log2(n) is max entropy for n event types)
            max_entropy = np.log2(len(event_counts)) if len(event_counts) > 0 else 1
            normalized_entropy = ent / max_entropy if max_entropy > 0 else 0

            # Map entropy to timeframe (higher entropy -> longer timeframe)
            if normalized_entropy < 0.3:
                return self.timeframe_mappings["very_short"]
            elif normalized_entropy < 0.5:
                return self.timeframe_mappings["short"]
            elif normalized_entropy < 0.7:
                return self.timeframe_mappings["medium"]
            elif normalized_entropy < 0.9:
                return self.timeframe_mappings["long"]
            else:
                return self.timeframe_mappings["very_long"]

        else:
            raise ValueError(f"Unsupported method: {method}")

    def get_event_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a summary of the events and their impact on timeframe

        Args:
            events: List of event dictionaries

        Returns:
            Dictionary with event summary
        """
        # Calculate event strengths
        events = self.calculate_event_strength(events)

        # Count event types
        event_counts = {}
        for event in events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Calculate average strength by event type
        event_strengths = {}
        for event_type in event_counts.keys():
            type_events = [e for e in events if e["type"] == event_type]
            avg_strength = sum(e["strength"] for e in type_events) / len(type_events)
            event_strengths[event_type] = avg_strength

        # Get timeframe recommendations by method
        recommendations = {
            "weighted_avg": self.recommend_timeframe(events, "weighted_avg"),
            "max_impact": self.recommend_timeframe(events, "max_impact"),
            "entropy": self.recommend_timeframe(events, "entropy"),
        }

        return {
            "event_counts": event_counts,
            "event_strengths": event_strengths,
            "recommendations": recommendations,
            "total_events": len(events),
        }


def detect_market_events(
    price_data: pd.DataFrame,
    news_data: Optional[pd.DataFrame] = None,
    economic_data: Optional[pd.DataFrame] = None,
    volatility_threshold: float = 0.02,
    volume_threshold: float = 2.0,
    trend_threshold: float = 0.1,
    sentiment_threshold: float = 0.7,
) -> List[Dict[str, Any]]:
    """
    Detect market events from price and external data

    Args:
        price_data: DataFrame with OHLCV data
        news_data: Optional DataFrame with news articles and sentiment
        economic_data: Optional DataFrame with economic indicators
        volatility_threshold: Threshold for volatility events
        volume_threshold: Threshold for volume spike events
        trend_threshold: Threshold for trend change events
        sentiment_threshold: Threshold for sentiment events

    Returns:
        List of detected events
    """
    events = []

    # Ensure we have required columns
    required_cols = ["open", "high", "low", "close", "volume"]
    if not all(col in price_data.columns for col in required_cols):
        raise ValueError(f"Price data must contain columns: {required_cols}")

    # Calculate basic indicators
    price_data = price_data.copy()
    price_data["returns"] = price_data["close"].pct_change()
    price_data["log_returns"] = np.log(
        price_data["close"] / price_data["close"].shift(1)
    )
    price_data["volatility_10d"] = price_data["returns"].rolling(window=10).std()
    price_data["volume_ratio"] = (
        price_data["volume"] / price_data["volume"].rolling(window=20).mean()
    )
    price_data["ma_20"] = price_data["close"].rolling(window=20).mean()
    price_data["ma_50"] = price_data["close"].rolling(window=50).mean()

    # Drop NaN values
    price_data = price_data.dropna()

    # Detect trend changes
    trend_changes = []
    ma_cross = (price_data["ma_20"] > price_data["ma_50"]) != (
        price_data["ma_20"].shift(1) > price_data["ma_50"].shift(1)
    )
    trend_change_days = price_data.index[ma_cross]

    for day in trend_change_days:
        # Determine impact based on price change after crossing
        idx = price_data.index.get_loc(day)
        if idx + 5 < len(price_data):
            change = abs(
                price_data["close"].iloc[idx + 5] / price_data["close"].iloc[idx] - 1
            )

            if change > trend_threshold:
                impact = "high"
            elif change > trend_threshold / 2:
                impact = "medium"
            else:
                impact = "low"

            trend_changes.append(
                {
                    "type": "trend_change",
                    "date": day,
                    "impact": impact,
                    "details": {
                        "direction": (
                            "up"
                            if price_data["ma_20"].iloc[idx]
                            > price_data["ma_50"].iloc[idx]
                            else "down"
                        ),
                        "change": change,
                    },
                }
            )

    events.extend(trend_changes)

    # Detect volatility changes
    volatility_changes = []
    high_vol = price_data["volatility_10d"] > volatility_threshold
    vol_change = high_vol != high_vol.shift(1)
    vol_change_days = price_data.index[vol_change]

    for day in vol_change_days:
        idx = price_data.index.get_loc(day)
        vol = price_data["volatility_10d"].iloc[idx]

        if vol > volatility_threshold * 2:
            impact = "high"
        elif vol > volatility_threshold * 1.5:
            impact = "medium"
        else:
            impact = "low"

        volatility_changes.append(
            {
                "type": "volatility_change",
                "date": day,
                "impact": impact,
                "details": {
                    "direction": "up" if high_vol.iloc[idx] else "down",
                    "volatility": vol,
                },
            }
        )

    events.extend(volatility_changes)

    # Detect volume spikes
    volume_spikes = []
    high_vol = price_data["volume_ratio"] > volume_threshold
    vol_spike_days = price_data.index[high_vol]

    for day in vol_spike_days:
        idx = price_data.index.get_loc(day)
        vol_ratio = price_data["volume_ratio"].iloc[idx]

        if vol_ratio > volume_threshold * 2:
            impact = "high"
        elif vol_ratio > volume_threshold * 1.5:
            impact = "medium"
        else:
            impact = "low"

        volume_spikes.append(
            {
                "type": "volume_spike",
                "date": day,
                "impact": impact,
                "details": {"volume_ratio": vol_ratio},
            }
        )

    events.extend(volume_spikes)

    # Process news sentiment if provided
    if (
        news_data is not None
        and "sentiment" in news_data.columns
        and "date" in news_data.columns
    ):
        news_events = []

        # Group by date
        news_by_date = news_data.groupby("date")

        for date, group in news_by_date:
            # Calculate average sentiment
            if "score" in group.columns:
                avg_sentiment = group["score"].mean()

                # Check if sentiment is strong enough
                if abs(avg_sentiment) > sentiment_threshold:
                    impact = (
                        "high"
                        if abs(avg_sentiment) > sentiment_threshold * 1.3
                        else "medium"
                    )

                    news_events.append(
                        {
                            "type": "news_sentiment",
                            "date": date,
                            "impact": impact,
                            "details": {
                                "sentiment": (
                                    "positive" if avg_sentiment > 0 else "negative"
                                ),
                                "score": avg_sentiment,
                                "count": len(group),
                            },
                        }
                    )

        events.extend(news_events)

    # Process economic data if provided
    if economic_data is not None and "date" in economic_data.columns:
        economic_events = []

        # Check if there's an importance column
        has_importance = "importance" in economic_data.columns

        for _, row in economic_data.iterrows():
            impact = row["importance"] if has_importance else "medium"

            economic_events.append(
                {
                    "type": "economic_data",
                    "date": row["date"],
                    "impact": impact,
                    "details": {
                        "indicator": row.get("indicator", "unknown"),
                        "actual": row.get("actual", None),
                        "forecast": row.get("forecast", None),
                        "previous": row.get("previous", None),
                    },
                }
            )

        events.extend(economic_events)

    # Sort events by date
    events.sort(key=lambda x: x["date"])

    return events
