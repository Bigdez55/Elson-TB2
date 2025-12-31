"""Trade schemas - re-exports from trade_advanced for compatibility."""

from app.schemas.trade_advanced import (
    DollarBasedInvestmentBase,
    DollarBasedInvestmentCreate,
    RecurringInvestmentBase,
    RecurringInvestmentCreate,
    RecurringInvestmentResponse,
    RecurringInvestmentUpdate,
    TradeResponse,
)

# Alias for backward compatibility
DollarBasedInvestmentResponse = DollarBasedInvestmentBase

__all__ = [
    "DollarBasedInvestmentBase",
    "DollarBasedInvestmentCreate",
    "DollarBasedInvestmentResponse",
    "RecurringInvestmentBase",
    "RecurringInvestmentCreate",
    "RecurringInvestmentResponse",
    "RecurringInvestmentUpdate",
    "TradeResponse",
]
