"""Risk-related enums and models."""

from enum import Enum


class RiskLevel(str, Enum):
    """Risk level categorization for trading and portfolio management."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"
