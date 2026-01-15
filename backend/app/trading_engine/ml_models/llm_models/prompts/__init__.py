"""
Elson Financial AI - Prompt Templates

Structured prompts for trading decisions, portfolio analysis, risk assessment,
and comprehensive wealth management advisory.
"""

from .trading_prompts import TradingPromptBuilder
from .wealth_management_prompts import (
    WealthManagementPromptBuilder,
    AdvisoryMode,
    WealthTier,
    WEALTH_MANAGEMENT_SYSTEM_PROMPT,
    ADVISORY_MODE_PROMPTS,
    WEALTH_TIER_CONTEXTS,
    get_system_prompt,
    get_advisory_mode_prompt,
    get_wealth_tier_context,
    create_prompt_builder,
)

__all__ = [
    # Trading prompts
    "TradingPromptBuilder",
    # Wealth management prompts
    "WealthManagementPromptBuilder",
    "AdvisoryMode",
    "WealthTier",
    "WEALTH_MANAGEMENT_SYSTEM_PROMPT",
    "ADVISORY_MODE_PROMPTS",
    "WEALTH_TIER_CONTEXTS",
    "get_system_prompt",
    "get_advisory_mode_prompt",
    "get_wealth_tier_context",
    "create_prompt_builder",
]
