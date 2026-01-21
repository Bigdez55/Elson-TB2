"""
Service Factory for Trading Platform
====================================

This module provides factory methods to properly initialize complex services
with their required dependencies.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.services.advanced_trading import AdvancedTradingService
from app.services.market_data import MarketDataService
from app.services.risk_management import RiskManagementService
from app.trading_engine.engine.risk_config import RiskProfile


class TradingServiceFactory:
    """Factory for creating properly configured trading services."""

    @staticmethod
    def create_advanced_trading_service(
        db: Session, risk_profile: str = "moderate"
    ) -> AdvancedTradingService:
        """Create an AdvancedTradingService with proper dependencies.

        Args:
            db: Database session
            risk_profile: Risk profile name ('conservative', 'moderate', 'aggressive')

        Returns:
            Configured AdvancedTradingService instance
        """
        # Map string to enum
        risk_profile_map = {
            "conservative": RiskProfile.CONSERVATIVE,
            "moderate": RiskProfile.MODERATE,
            "aggressive": RiskProfile.AGGRESSIVE,
        }

        risk_enum = risk_profile_map.get(risk_profile.lower(), RiskProfile.MODERATE)
        market_data_service = MarketDataService()

        return AdvancedTradingService(
            db=db, market_data_service=market_data_service, risk_profile=risk_enum
        )

    @staticmethod
    def create_risk_management_service(db: Session) -> RiskManagementService:
        """Create a RiskManagementService with proper dependencies.

        Args:
            db: Database session

        Returns:
            Configured RiskManagementService instance
        """
        return RiskManagementService(db=db)


# Convenience functions
def get_advanced_trading_service(
    db: Session, risk_profile: str = "moderate"
) -> AdvancedTradingService:
    """Get an advanced trading service instance."""
    return TradingServiceFactory.create_advanced_trading_service(db, risk_profile)


def get_risk_management_service(db: Session) -> RiskManagementService:
    """Get a risk management service instance."""
    return TradingServiceFactory.create_risk_management_service(db)
