"""Anomaly detection service for the Elson Trading Bot Platform.

This module provides anomaly detection capabilities for market data, 
system metrics, and API responses, helping to identify unusual patterns
and potential issues before they cause problems.
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.stats as stats

from app.core.alerts_manager import alert_manager
from app.core.config import settings
from app.core.exception_handlers import ServiceError, handle_errors
from app.core.metrics import metrics
from app.core.redis_service import redis_service

logger = logging.getLogger(__name__)


class AnomalyError(ServiceError):
    """Exception for anomaly detection related errors."""

    def __init__(self, message: str, detector_type: Optional[str] = None, **kwargs):
        details = {"service": "anomaly_detector"}
        if detector_type:
            details["detector_type"] = detector_type

        super().__init__(
            message=message,
            service_name="anomaly_detector",
            error_code="ANOMALY_DETECTION_ERROR",
            details=details,
            **kwargs,
        )


class AnomalyType:
    """Enum-like class for anomaly types."""

    PRICE_SPIKE = "PRICE_SPIKE"
    PRICE_DROP = "PRICE_DROP"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    VOLATILITY_CHANGE = "VOLATILITY_CHANGE"
    CORRELATION_BREAK = "CORRELATION_BREAK"
    SYSTEM_RESOURCE = "SYSTEM_RESOURCE"
    API_LATENCY = "API_LATENCY"
    ERROR_RATE = "ERROR_RATE"
    DATA_QUALITY = "DATA_QUALITY"
    TRADING_PATTERN = "TRADING_PATTERN"


class AnomalySeverity:
    """Enum-like class for anomaly severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AnomalyDetector:
    """Core anomaly detection service with multiple detection algorithms."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the anomaly detector with configuration.

        Args:
            config: Custom configuration parameters
        """
        self.config = config or {}

        # Default configuration
        self.default_config = {
            "zscore_threshold": 3.0,  # Z-score threshold for statistical anomalies
            "price_change_threshold": 0.05,  # 5% threshold for price changes
            "volume_change_threshold": 2.0,  # 2x threshold for volume changes
            "volatility_change_threshold": 2.0,  # 2x threshold for volatility changes
            "min_history_points": 20,  # Minimum data points needed for detection
            "lookback_window": {
                "price": 30,  # 30 data points for price anomalies
                "volume": 20,  # 20 data points for volume anomalies
                "volatility": 14,  # 14 data points for volatility anomalies
                "system": 60,  # 60 data points for system metrics
                "api": 100,  # 100 data points for API metrics
            },
            "detection_sensitivity": 0.8,  # 0.0-1.0 scale, higher is more sensitive
            "adaptive_thresholds": True,  # Use adaptive thresholds based on history
            "use_seasonal_adjustment": True,  # Adjust for time-of-day patterns
            "anomaly_cooldown_minutes": 30,  # Minimum time between similar anomalies
        }

        # Override defaults with provided config
        for key, value in self.config.items():
            if key in self.default_config:
                if isinstance(value, dict) and isinstance(
                    self.default_config[key], dict
                ):
                    # Merge nested dictionaries
                    self.default_config[key].update(value)
                else:
                    self.default_config[key] = value

        # Use the merged config
        self.config = self.default_config

        # Initialize anomaly history
        self._recent_anomalies = defaultdict(list)

        # Load saved anomaly history from Redis
        self._load_anomaly_history()

        logger.info("Anomaly detector initialized")

    def _load_anomaly_history(self):
        """Load anomaly detection history from Redis."""
        try:
            history = redis_service.get("anomaly_detector:history")
            if history and isinstance(history, dict):
                for key, anomalies in history.items():
                    self._recent_anomalies[key] = anomalies

            logger.debug(
                f"Loaded anomaly history with {sum(len(v) for v in self._recent_anomalies.values())} entries"
            )
        except Exception as e:
            logger.warning(f"Failed to load anomaly history: {e}")

    def _save_anomaly_history(self):
        """Save anomaly detection history to Redis."""
        try:
            # Clean up old anomalies
            cutoff_time = datetime.utcnow() - timedelta(days=1)
            for key in self._recent_anomalies:
                self._recent_anomalies[key] = [
                    a
                    for a in self._recent_anomalies[key]
                    if a.get("timestamp")
                    and datetime.fromisoformat(a["timestamp"]) > cutoff_time
                ]

            # Save to Redis
            redis_service.set(
                "anomaly_detector:history",
                dict(self._recent_anomalies),
                ttl=86400,  # 1 day
            )
        except Exception as e:
            logger.warning(f"Failed to save anomaly history: {e}")

    def _check_cooldown(self, entity_id: str, anomaly_type: str) -> bool:
        """Check if a similar anomaly was recently detected.

        Args:
            entity_id: Identifier for the entity (symbol, metric name, etc.)
            anomaly_type: Type of anomaly

        Returns:
            True if a similar anomaly was recently detected (in cooldown)
        """
        key = f"{entity_id}:{anomaly_type}"
        cooldown_minutes = self.config["anomaly_cooldown_minutes"]

        for anomaly in self._recent_anomalies.get(key, []):
            if "timestamp" in anomaly:
                detected_time = datetime.fromisoformat(anomaly["timestamp"])
                time_since = (datetime.utcnow() - detected_time).total_seconds() / 60
                if time_since < cooldown_minutes:
                    return True

        return False

    def _record_anomaly(self, anomaly: Dict[str, Any]):
        """Record a detected anomaly in history.

        Args:
            anomaly: Anomaly information dictionary
        """
        if "entity_id" not in anomaly or "type" not in anomaly:
            logger.warning("Cannot record anomaly without entity_id and type")
            return

        key = f"{anomaly['entity_id']}:{anomaly['type']}"

        # Add timestamp if not present
        if "timestamp" not in anomaly:
            anomaly["timestamp"] = datetime.utcnow().isoformat()

        # Add to history
        self._recent_anomalies[key].append(anomaly)

        # Limit history size
        if len(self._recent_anomalies[key]) > 20:
            self._recent_anomalies[key] = self._recent_anomalies[key][-20:]

        # Save history
        self._save_anomaly_history()

    @handle_errors()
    def detect_price_anomalies(
        self,
        symbol: str,
        prices: List[float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
        sensitivity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in price data for a symbol.

        Args:
            symbol: The trading symbol
            prices: List of price data points
            timestamps: Optional list of timestamps for each data point
            sensitivity: Override for detection sensitivity (0.0-1.0)

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting price anomalies for {symbol} with {len(prices)} data points"
        )

        if len(prices) < self.config["min_history_points"]:
            logger.debug(f"Not enough data points for {symbol} price anomaly detection")
            return []

        # Use provided sensitivity or config default
        sensitivity = sensitivity or self.config["detection_sensitivity"]

        # Adjust thresholds based on sensitivity
        z_threshold = self.config["zscore_threshold"] * (2 - sensitivity)
        price_threshold = self.config["price_change_threshold"] * (2 - sensitivity)

        # Calculate statistics
        try:
            # Calculate returns
            returns = [0.0]
            for i in range(1, len(prices)):
                if prices[i - 1] > 0:
                    returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
                else:
                    returns.append(0.0)

            # Calculate Z-scores
            mean_return = np.mean(returns)
            std_return = np.std(returns) or 0.001  # Avoid division by zero
            zscores = [(r - mean_return) / std_return for r in returns]

            # Look for anomalies
            anomalies = []

            for i in range(1, len(prices)):
                price_change = abs(returns[i])
                zscore = abs(zscores[i])

                # Skip if in cooldown period
                if self._check_cooldown(
                    symbol, AnomalyType.PRICE_SPIKE
                ) or self._check_cooldown(symbol, AnomalyType.PRICE_DROP):
                    continue

                # Detect significant price changes
                if price_change > price_threshold or zscore > z_threshold:
                    # Determine anomaly type and severity
                    anomaly_type = (
                        AnomalyType.PRICE_SPIKE
                        if returns[i] > 0
                        else AnomalyType.PRICE_DROP
                    )

                    severity = AnomalySeverity.INFO
                    if (
                        zscore > z_threshold * 1.5
                        or price_change > price_threshold * 1.5
                    ):
                        severity = AnomalySeverity.WARNING
                    if zscore > z_threshold * 2 or price_change > price_threshold * 2:
                        severity = AnomalySeverity.CRITICAL

                    # Create anomaly entry
                    anomaly = {
                        "entity_id": symbol,
                        "type": anomaly_type,
                        "severity": severity,
                        "timestamp": timestamps[i]
                        if timestamps and i < len(timestamps)
                        else datetime.utcnow().isoformat(),
                        "value": prices[i],
                        "previous_value": prices[i - 1],
                        "change": returns[i],
                        "zscore": zscores[i],
                        "threshold": {
                            "zscore": z_threshold,
                            "price_change": price_threshold,
                        },
                    }

                    anomalies.append(anomaly)

                    # Record this anomaly
                    self._record_anomaly(anomaly)

                    # Send alert for significant anomalies
                    if severity in [AnomalySeverity.WARNING, AnomalySeverity.CRITICAL]:
                        alert_level = (
                            "warning"
                            if severity == AnomalySeverity.WARNING
                            else "critical"
                        )
                        direction = (
                            "increase"
                            if anomaly_type == AnomalyType.PRICE_SPIKE
                            else "decrease"
                        )

                        alert_manager.send_alert(
                            f"Abnormal {symbol} price {direction}",
                            f"{symbol} price {direction}d by {price_change*100:.1f}% (Z-score: {zscore:.2f})",
                            level=alert_level,
                            data=anomaly,
                        )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting price anomalies for {symbol}: {e}")
            raise AnomalyError(
                f"Price anomaly detection failed: {e}", detector_type="price"
            )

    @handle_errors()
    def detect_volume_anomalies(
        self,
        symbol: str,
        volumes: List[float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
        sensitivity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in trading volume for a symbol.

        Args:
            symbol: The trading symbol
            volumes: List of volume data points
            timestamps: Optional list of timestamps for each data point
            sensitivity: Override for detection sensitivity (0.0-1.0)

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting volume anomalies for {symbol} with {len(volumes)} data points"
        )

        if len(volumes) < self.config["min_history_points"]:
            logger.debug(
                f"Not enough data points for {symbol} volume anomaly detection"
            )
            return []

        # Use provided sensitivity or config default
        sensitivity = sensitivity or self.config["detection_sensitivity"]

        # Adjust thresholds based on sensitivity
        z_threshold = self.config["zscore_threshold"] * (2 - sensitivity)
        volume_threshold = self.config["volume_change_threshold"] * (2 - sensitivity)

        try:
            # Calculate volume changes
            volume_changes = [0.0]
            for i in range(1, len(volumes)):
                if volumes[i - 1] > 0:
                    volume_changes.append(volumes[i] / volumes[i - 1])
                else:
                    volume_changes.append(1.0)

            # Calculate statistics (log-transform to handle multiplicative changes better)
            log_changes = [np.log(max(vc, 0.1)) for vc in volume_changes]
            mean_log_change = np.mean(log_changes)
            std_log_change = np.std(log_changes) or 0.001  # Avoid division by zero
            zscores = [(lc - mean_log_change) / std_log_change for lc in log_changes]

            # Look for anomalies
            anomalies = []

            for i in range(1, len(volumes)):
                if volumes[i - 1] == 0:
                    continue  # Skip if previous volume was zero

                volume_change = volume_changes[i]
                zscore = abs(zscores[i])

                # Skip if in cooldown period
                if self._check_cooldown(symbol, AnomalyType.VOLUME_SPIKE):
                    continue

                # Detect significant volume changes (focus on increases)
                if volume_change > volume_threshold and zscore > z_threshold:
                    # Determine severity
                    severity = AnomalySeverity.INFO
                    if (
                        zscore > z_threshold * 1.5
                        or volume_change > volume_threshold * 1.5
                    ):
                        severity = AnomalySeverity.WARNING
                    if zscore > z_threshold * 2 or volume_change > volume_threshold * 2:
                        severity = AnomalySeverity.CRITICAL

                    # Create anomaly entry
                    anomaly = {
                        "entity_id": symbol,
                        "type": AnomalyType.VOLUME_SPIKE,
                        "severity": severity,
                        "timestamp": timestamps[i]
                        if timestamps and i < len(timestamps)
                        else datetime.utcnow().isoformat(),
                        "value": volumes[i],
                        "previous_value": volumes[i - 1],
                        "change_factor": volume_change,
                        "zscore": zscores[i],
                        "threshold": {
                            "zscore": z_threshold,
                            "volume_change": volume_threshold,
                        },
                    }

                    anomalies.append(anomaly)

                    # Record this anomaly
                    self._record_anomaly(anomaly)

                    # Send alert for significant anomalies
                    if severity in [AnomalySeverity.WARNING, AnomalySeverity.CRITICAL]:
                        alert_level = (
                            "warning"
                            if severity == AnomalySeverity.WARNING
                            else "critical"
                        )

                        alert_manager.send_alert(
                            f"Abnormal {symbol} volume spike",
                            f"{symbol} volume increased by {(volume_change-1)*100:.1f}% (Z-score: {zscore:.2f})",
                            level=alert_level,
                            data=anomaly,
                        )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting volume anomalies for {symbol}: {e}")
            raise AnomalyError(
                f"Volume anomaly detection failed: {e}", detector_type="volume"
            )

    @handle_errors()
    def detect_volatility_anomalies(
        self,
        symbol: str,
        prices: List[float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
        window_size: int = 14,
        sensitivity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in price volatility for a symbol.

        Args:
            symbol: The trading symbol
            prices: List of price data points
            timestamps: Optional list of timestamps for each data point
            window_size: Window size for volatility calculation
            sensitivity: Override for detection sensitivity (0.0-1.0)

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting volatility anomalies for {symbol} with {len(prices)} data points"
        )

        # Need enough data for both window calculation and history
        if len(prices) < window_size + self.config["min_history_points"]:
            logger.debug(
                f"Not enough data points for {symbol} volatility anomaly detection"
            )
            return []

        # Use provided sensitivity or config default
        sensitivity = sensitivity or self.config["detection_sensitivity"]

        # Adjust thresholds based on sensitivity
        z_threshold = self.config["zscore_threshold"] * (2 - sensitivity)
        volatility_threshold = self.config["volatility_change_threshold"] * (
            2 - sensitivity
        )

        try:
            # Calculate returns
            returns = [0.0]
            for i in range(1, len(prices)):
                if prices[i - 1] > 0:
                    returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
                else:
                    returns.append(0.0)

            # Calculate rolling volatility
            volatilities = [0.0] * window_size  # Pad initial values

            for i in range(window_size, len(returns)):
                window_returns = returns[i - window_size : i]
                volatilities.append(np.std(window_returns))

            # Need enough volatility points for anomaly detection
            if len(volatilities) < self.config["min_history_points"]:
                return []

            # Calculate volatility changes
            volatility_changes = [0.0]
            for i in range(1, len(volatilities)):
                if volatilities[i - 1] > 0:
                    volatility_changes.append(volatilities[i] / volatilities[i - 1])
                else:
                    volatility_changes.append(1.0)

            # Calculate statistics
            log_changes = [np.log(max(vc, 0.1)) for vc in volatility_changes]
            mean_log_change = np.mean(log_changes)
            std_log_change = np.std(log_changes) or 0.001  # Avoid division by zero
            zscores = [(lc - mean_log_change) / std_log_change for lc in log_changes]

            # Look for anomalies
            anomalies = []

            for i in range(1, len(volatilities)):
                # Skip first values where change calculation isn't meaningful
                if i < window_size + 1:
                    continue

                if volatilities[i - 1] == 0:
                    continue  # Skip if previous volatility was zero

                volatility_change = volatility_changes[i]
                zscore = abs(zscores[i])

                # Skip if in cooldown period
                if self._check_cooldown(symbol, AnomalyType.VOLATILITY_CHANGE):
                    continue

                # Detect significant volatility changes
                if volatility_change > volatility_threshold and zscore > z_threshold:
                    # Determine severity
                    severity = AnomalySeverity.INFO
                    if (
                        zscore > z_threshold * 1.5
                        or volatility_change > volatility_threshold * 1.5
                    ):
                        severity = AnomalySeverity.WARNING
                    if (
                        zscore > z_threshold * 2
                        or volatility_change > volatility_threshold * 2
                    ):
                        severity = AnomalySeverity.CRITICAL

                    # Create anomaly entry
                    ts_index = i + window_size - 1  # Adjust for the initial window
                    anomaly = {
                        "entity_id": symbol,
                        "type": AnomalyType.VOLATILITY_CHANGE,
                        "severity": severity,
                        "timestamp": timestamps[ts_index]
                        if timestamps and ts_index < len(timestamps)
                        else datetime.utcnow().isoformat(),
                        "value": volatilities[i],
                        "previous_value": volatilities[i - 1],
                        "change_factor": volatility_change,
                        "zscore": zscores[i],
                        "window_size": window_size,
                        "threshold": {
                            "zscore": z_threshold,
                            "volatility_change": volatility_threshold,
                        },
                    }

                    anomalies.append(anomaly)

                    # Record this anomaly
                    self._record_anomaly(anomaly)

                    # Send alert for significant anomalies
                    if severity in [AnomalySeverity.WARNING, AnomalySeverity.CRITICAL]:
                        alert_level = (
                            "warning"
                            if severity == AnomalySeverity.WARNING
                            else "critical"
                        )

                        alert_manager.send_alert(
                            f"Abnormal {symbol} volatility increase",
                            f"{symbol} volatility increased by {(volatility_change-1)*100:.1f}% (Z-score: {zscore:.2f})",
                            level=alert_level,
                            data=anomaly,
                        )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting volatility anomalies for {symbol}: {e}")
            raise AnomalyError(
                f"Volatility anomaly detection failed: {e}", detector_type="volatility"
            )

    @handle_errors()
    def detect_system_metric_anomalies(
        self,
        metric_name: str,
        values: List[float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
        upper_limit: Optional[float] = None,
        lower_limit: Optional[float] = None,
        sensitivity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in system metrics.

        Args:
            metric_name: Name of the metric
            values: List of metric values
            timestamps: Optional list of timestamps for each data point
            upper_limit: Optional hard upper limit for this metric
            lower_limit: Optional hard lower limit for this metric
            sensitivity: Override for detection sensitivity (0.0-1.0)

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting system metric anomalies for {metric_name} with {len(values)} data points"
        )

        if len(values) < self.config["min_history_points"]:
            logger.debug(f"Not enough data points for {metric_name} anomaly detection")
            return []

        # Use provided sensitivity or config default
        sensitivity = sensitivity or self.config["detection_sensitivity"]

        # Adjust threshold based on sensitivity
        z_threshold = self.config["zscore_threshold"] * (2 - sensitivity)

        try:
            # Calculate statistics
            mean_value = np.mean(values)
            std_value = np.std(values) or 0.001  # Avoid division by zero
            zscores = [(v - mean_value) / std_value for v in values]

            # Look for anomalies
            anomalies = []

            for i in range(len(values)):
                value = values[i]
                zscore = abs(zscores[i])

                # Skip if in cooldown period
                if self._check_cooldown(metric_name, AnomalyType.SYSTEM_RESOURCE):
                    continue

                # Check for anomalies
                is_anomaly = False
                anomaly_reason = ""

                # Check Z-score
                if zscore > z_threshold:
                    is_anomaly = True
                    anomaly_reason = (
                        f"Z-score {zscore:.2f} exceeds threshold {z_threshold:.2f}"
                    )

                # Check hard limits if provided
                if upper_limit is not None and value > upper_limit:
                    is_anomaly = True
                    anomaly_reason = f"Value {value} exceeds upper limit {upper_limit}"

                if lower_limit is not None and value < lower_limit:
                    is_anomaly = True
                    anomaly_reason = f"Value {value} below lower limit {lower_limit}"

                if is_anomaly:
                    # Determine severity
                    severity = AnomalySeverity.INFO
                    if (
                        zscore > z_threshold * 1.5
                        or (upper_limit and value > upper_limit * 1.1)
                        or (lower_limit and value < lower_limit * 0.9)
                    ):
                        severity = AnomalySeverity.WARNING
                    if (
                        zscore > z_threshold * 2
                        or (upper_limit and value > upper_limit * 1.25)
                        or (lower_limit and value < lower_limit * 0.75)
                    ):
                        severity = AnomalySeverity.CRITICAL

                    # Create anomaly entry
                    anomaly = {
                        "entity_id": metric_name,
                        "type": AnomalyType.SYSTEM_RESOURCE,
                        "severity": severity,
                        "timestamp": timestamps[i]
                        if timestamps and i < len(timestamps)
                        else datetime.utcnow().isoformat(),
                        "value": value,
                        "mean_value": mean_value,
                        "zscore": zscores[i],
                        "reason": anomaly_reason,
                        "threshold": {
                            "zscore": z_threshold,
                            "upper_limit": upper_limit,
                            "lower_limit": lower_limit,
                        },
                    }

                    anomalies.append(anomaly)

                    # Record this anomaly
                    self._record_anomaly(anomaly)

                    # Send alert for significant anomalies
                    if severity in [AnomalySeverity.WARNING, AnomalySeverity.CRITICAL]:
                        alert_level = (
                            "warning"
                            if severity == AnomalySeverity.WARNING
                            else "critical"
                        )

                        alert_manager.send_alert(
                            f"System metric anomaly: {metric_name}",
                            f"{metric_name} value {value} is abnormal: {anomaly_reason}",
                            level=alert_level,
                            data=anomaly,
                        )

            return anomalies

        except Exception as e:
            logger.error(
                f"Error detecting system metric anomalies for {metric_name}: {e}"
            )
            raise AnomalyError(
                f"System metric anomaly detection failed: {e}",
                detector_type="system_metric",
            )

    @handle_errors()
    def detect_api_latency_anomalies(
        self,
        api_name: str,
        latencies: List[float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
        max_acceptable_latency: Optional[float] = None,
        sensitivity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in API latency.

        Args:
            api_name: Name of the API
            latencies: List of API latency values in milliseconds
            timestamps: Optional list of timestamps for each data point
            max_acceptable_latency: Optional maximum acceptable latency
            sensitivity: Override for detection sensitivity (0.0-1.0)

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting API latency anomalies for {api_name} with {len(latencies)} data points"
        )

        if len(latencies) < self.config["min_history_points"]:
            logger.debug(
                f"Not enough data points for {api_name} latency anomaly detection"
            )
            return []

        # Use provided sensitivity or config default
        sensitivity = sensitivity or self.config["detection_sensitivity"]

        # Adjust threshold based on sensitivity
        z_threshold = self.config["zscore_threshold"] * (2 - sensitivity)

        try:
            # Use log-transformed latencies for better distribution
            log_latencies = [np.log(max(l, 1.0)) for l in latencies]

            # Calculate statistics
            mean_log = np.mean(log_latencies)
            std_log = np.std(log_latencies) or 0.001  # Avoid division by zero
            zscores = [(l - mean_log) / std_log for l in log_latencies]

            # Look for anomalies
            anomalies = []

            for i in range(len(latencies)):
                latency = latencies[i]
                zscore = zscores[
                    i
                ]  # Use regular (not absolute) z-score to focus on high latencies

                # Skip if in cooldown period
                if self._check_cooldown(api_name, AnomalyType.API_LATENCY):
                    continue

                # Check for anomalies - only interested in high latencies
                is_anomaly = False
                anomaly_reason = ""

                # Check Z-score (only high values)
                if zscore > z_threshold:
                    is_anomaly = True
                    anomaly_reason = (
                        f"Z-score {zscore:.2f} exceeds threshold {z_threshold:.2f}"
                    )

                # Check hard limit if provided
                if (
                    max_acceptable_latency is not None
                    and latency > max_acceptable_latency
                ):
                    is_anomaly = True
                    anomaly_reason = f"Latency {latency:.2f}ms exceeds max acceptable {max_acceptable_latency:.2f}ms"

                if is_anomaly:
                    # Determine severity
                    severity = AnomalySeverity.INFO
                    if zscore > z_threshold * 1.5 or (
                        max_acceptable_latency
                        and latency > max_acceptable_latency * 1.5
                    ):
                        severity = AnomalySeverity.WARNING
                    if zscore > z_threshold * 2 or (
                        max_acceptable_latency and latency > max_acceptable_latency * 2
                    ):
                        severity = AnomalySeverity.CRITICAL

                    # Create anomaly entry
                    anomaly = {
                        "entity_id": api_name,
                        "type": AnomalyType.API_LATENCY,
                        "severity": severity,
                        "timestamp": timestamps[i]
                        if timestamps and i < len(timestamps)
                        else datetime.utcnow().isoformat(),
                        "value": latency,
                        "mean_value": np.exp(mean_log),  # Convert back to milliseconds
                        "zscore": zscore,
                        "reason": anomaly_reason,
                        "threshold": {
                            "zscore": z_threshold,
                            "max_latency": max_acceptable_latency,
                        },
                    }

                    anomalies.append(anomaly)

                    # Record this anomaly
                    self._record_anomaly(anomaly)

                    # Send alert for significant anomalies
                    if severity in [AnomalySeverity.WARNING, AnomalySeverity.CRITICAL]:
                        alert_level = (
                            "warning"
                            if severity == AnomalySeverity.WARNING
                            else "critical"
                        )

                        alert_manager.send_alert(
                            f"API latency anomaly: {api_name}",
                            f"{api_name} latency {latency:.2f}ms is abnormal: {anomaly_reason}",
                            level=alert_level,
                            data=anomaly,
                        )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting API latency anomalies for {api_name}: {e}")
            raise AnomalyError(
                f"API latency anomaly detection failed: {e}",
                detector_type="api_latency",
            )

    @handle_errors()
    def detect_error_rate_anomalies(
        self,
        service_name: str,
        error_rates: List[float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
        max_acceptable_rate: Optional[float] = None,
        sensitivity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in service error rates.

        Args:
            service_name: Name of the service
            error_rates: List of error rate values (0.0-1.0)
            timestamps: Optional list of timestamps for each data point
            max_acceptable_rate: Optional maximum acceptable error rate
            sensitivity: Override for detection sensitivity (0.0-1.0)

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting error rate anomalies for {service_name} with {len(error_rates)} data points"
        )

        if len(error_rates) < self.config["min_history_points"]:
            logger.debug(
                f"Not enough data points for {service_name} error rate anomaly detection"
            )
            return []

        # Use provided sensitivity or config default
        sensitivity = sensitivity or self.config["detection_sensitivity"]

        # For error rates, default to a lower Z-score threshold
        z_threshold = (self.config["zscore_threshold"] - 0.5) * (2 - sensitivity)

        try:
            # Use logit-transformed error rates for better distribution
            # (add small epsilon to avoid log(0) and log(1) issues)
            epsilon = 0.001
            logit_rates = [
                np.log((r + epsilon) / (1 - r + epsilon)) for r in error_rates
            ]

            # Calculate statistics
            mean_logit = np.mean(logit_rates)
            std_logit = np.std(logit_rates) or 0.001  # Avoid division by zero
            zscores = [(l - mean_logit) / std_logit for l in logit_rates]

            # Look for anomalies
            anomalies = []

            for i in range(len(error_rates)):
                error_rate = error_rates[i]
                zscore = zscores[
                    i
                ]  # Use regular (not absolute) z-score to focus on high error rates

                # Skip if in cooldown period
                if self._check_cooldown(service_name, AnomalyType.ERROR_RATE):
                    continue

                # Check for anomalies - only interested in high error rates
                is_anomaly = False
                anomaly_reason = ""

                # Check Z-score (only high values)
                if zscore > z_threshold:
                    is_anomaly = True
                    anomaly_reason = (
                        f"Z-score {zscore:.2f} exceeds threshold {z_threshold:.2f}"
                    )

                # Check hard limit if provided
                if max_acceptable_rate is not None and error_rate > max_acceptable_rate:
                    is_anomaly = True
                    anomaly_reason = f"Error rate {error_rate:.2%} exceeds max acceptable {max_acceptable_rate:.2%}"

                if is_anomaly:
                    # Determine severity based on error rate magnitude
                    severity = AnomalySeverity.INFO
                    if zscore > z_threshold * 1.5 or (
                        max_acceptable_rate and error_rate > max_acceptable_rate * 1.5
                    ):
                        severity = AnomalySeverity.WARNING
                    if zscore > z_threshold * 2 or (
                        max_acceptable_rate and error_rate > max_acceptable_rate * 2
                    ):
                        severity = AnomalySeverity.CRITICAL

                    # Create anomaly entry
                    anomaly = {
                        "entity_id": service_name,
                        "type": AnomalyType.ERROR_RATE,
                        "severity": severity,
                        "timestamp": timestamps[i]
                        if timestamps and i < len(timestamps)
                        else datetime.utcnow().isoformat(),
                        "value": error_rate,
                        "mean_value": 1
                        / (1 + np.exp(-mean_logit)),  # Convert back to rate
                        "zscore": zscore,
                        "reason": anomaly_reason,
                        "threshold": {
                            "zscore": z_threshold,
                            "max_error_rate": max_acceptable_rate,
                        },
                    }

                    anomalies.append(anomaly)

                    # Record this anomaly
                    self._record_anomaly(anomaly)

                    # Send alert for significant anomalies
                    if severity in [AnomalySeverity.WARNING, AnomalySeverity.CRITICAL]:
                        alert_level = (
                            "warning"
                            if severity == AnomalySeverity.WARNING
                            else "critical"
                        )

                        alert_manager.send_alert(
                            f"Error rate anomaly: {service_name}",
                            f"{service_name} error rate {error_rate:.2%} is abnormal: {anomaly_reason}",
                            level=alert_level,
                            data=anomaly,
                        )

            return anomalies

        except Exception as e:
            logger.error(
                f"Error detecting error rate anomalies for {service_name}: {e}"
            )
            raise AnomalyError(
                f"Error rate anomaly detection failed: {e}", detector_type="error_rate"
            )

    @handle_errors()
    def detect_data_quality_anomalies(
        self,
        data_source: str,
        data_points: List[Dict[str, Any]],
        quality_metrics: List[str],
        thresholds: Dict[str, float],
        timestamps: Optional[List[Union[str, datetime]]] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in data quality metrics.

        Args:
            data_source: Name of the data source
            data_points: List of data quality metric dictionaries
            quality_metrics: List of metric names to check in each data point
            thresholds: Dictionary of threshold values for each metric
            timestamps: Optional list of timestamps for each data point

        Returns:
            List of detected anomalies

        Raises:
            AnomalyError: If detection fails
        """
        logger.debug(
            f"Detecting data quality anomalies for {data_source} with {len(data_points)} data points"
        )

        if len(data_points) < 1:
            logger.debug(
                f"No data points for {data_source} data quality anomaly detection"
            )
            return []

        try:
            # Look for anomalies in each data point
            anomalies = []

            for i, data_point in enumerate(data_points):
                for metric in quality_metrics:
                    if metric not in data_point:
                        continue

                    value = data_point[metric]
                    threshold = thresholds.get(metric)

                    if threshold is None:
                        continue

                    # Skip if in cooldown period
                    if self._check_cooldown(
                        f"{data_source}:{metric}", AnomalyType.DATA_QUALITY
                    ):
                        continue

                    # Check if value exceeds threshold
                    if value > threshold:
                        # Determine severity based on how much threshold is exceeded
                        severity = AnomalySeverity.INFO
                        if value > threshold * 1.5:
                            severity = AnomalySeverity.WARNING
                        if value > threshold * 2:
                            severity = AnomalySeverity.CRITICAL

                        # Create anomaly entry
                        anomaly = {
                            "entity_id": f"{data_source}:{metric}",
                            "type": AnomalyType.DATA_QUALITY,
                            "severity": severity,
                            "timestamp": timestamps[i]
                            if timestamps and i < len(timestamps)
                            else datetime.utcnow().isoformat(),
                            "value": value,
                            "threshold": threshold,
                            "metric": metric,
                            "data_source": data_source,
                        }

                        anomalies.append(anomaly)

                        # Record this anomaly
                        self._record_anomaly(anomaly)

                        # Send alert for significant anomalies
                        if severity in [
                            AnomalySeverity.WARNING,
                            AnomalySeverity.CRITICAL,
                        ]:
                            alert_level = (
                                "warning"
                                if severity == AnomalySeverity.WARNING
                                else "critical"
                            )

                            alert_manager.send_alert(
                                f"Data quality issue: {data_source}",
                                f"{data_source} {metric} value {value} exceeds threshold {threshold}",
                                level=alert_level,
                                data=anomaly,
                            )

            return anomalies

        except Exception as e:
            logger.error(
                f"Error detecting data quality anomalies for {data_source}: {e}"
            )
            raise AnomalyError(
                f"Data quality anomaly detection failed: {e}",
                detector_type="data_quality",
            )

    def get_anomaly_history(
        self,
        entity_id: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get historical anomalies with optional filtering.

        Args:
            entity_id: Optional entity ID to filter by
            anomaly_type: Optional anomaly type to filter by
            severity: Optional severity level to filter by
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            limit: Maximum number of anomalies to return

        Returns:
            List of anomaly records matching the filters
        """
        # Convert time filters to datetime objects if they're strings
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)

        # Collect all anomalies
        all_anomalies = []
        for key, anomalies in self._recent_anomalies.items():
            all_anomalies.extend(anomalies)

        # Sort by timestamp (most recent first)
        all_anomalies.sort(key=lambda a: a.get("timestamp", ""), reverse=True)

        # Apply filters
        filtered_anomalies = []
        for anomaly in all_anomalies:
            # Entity ID filter
            if entity_id and anomaly.get("entity_id") != entity_id:
                continue

            # Anomaly type filter
            if anomaly_type and anomaly.get("type") != anomaly_type:
                continue

            # Severity filter
            if severity and anomaly.get("severity") != severity:
                continue

            # Time range filters
            if "timestamp" in anomaly:
                anomaly_time = datetime.fromisoformat(anomaly["timestamp"])

                if start_time and anomaly_time < start_time:
                    continue

                if end_time and anomaly_time > end_time:
                    continue

            filtered_anomalies.append(anomaly)

            # Apply limit
            if len(filtered_anomalies) >= limit:
                break

        return filtered_anomalies

    def get_anomaly_statistics(
        self,
        group_by: Optional[str] = "type",
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None,
    ) -> Dict[str, Dict[str, int]]:
        """Get statistics about detected anomalies.

        Args:
            group_by: Field to group statistics by ("type", "entity_id", "severity")
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering

        Returns:
            Dictionary of anomaly statistics
        """
        # Get all anomalies in the time range
        all_anomalies = self.get_anomaly_history(
            start_time=start_time,
            end_time=end_time,
            limit=10000,  # High limit to get all matching anomalies
        )

        if not group_by or group_by not in ["type", "entity_id", "severity"]:
            group_by = "type"  # Default grouping

        # Group anomalies
        stats = {}
        for anomaly in all_anomalies:
            group_value = anomaly.get(group_by, "unknown")
            severity = anomaly.get("severity", AnomalySeverity.INFO)

            if group_value not in stats:
                stats[group_value] = {
                    "total": 0,
                    AnomalySeverity.INFO: 0,
                    AnomalySeverity.WARNING: 0,
                    AnomalySeverity.CRITICAL: 0,
                }

            stats[group_value]["total"] += 1
            stats[group_value][severity] += 1

        return stats


# Singleton instance
anomaly_detector = AnomalyDetector()


def get_anomaly_detector() -> AnomalyDetector:
    """Get the global anomaly detector instance.

    Returns:
        Global anomaly detector instance
    """
    return anomaly_detector
