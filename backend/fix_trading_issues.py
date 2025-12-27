#!/usr/bin/env python3
"""
Trading Services Quick Fix Script
=================================

This script applies the critical fixes identified in the trading services analysis.
Run this script to resolve the most urgent issues preventing trading functionality.
"""

import os
import sys
from pathlib import Path

def fix_trade_model():
    """Fix the Trade model constructor to handle side field properly."""
    
    trade_model_path = Path("app/models/trade.py")
    
    if not trade_model_path.exists():
        print(f"❌ Trade model file not found: {trade_model_path}")
        return False
    
    print("🔧 Fixing Trade model constructor...")
    
    # Read the current file
    with open(trade_model_path, 'r') as f:
        content = f.read()
    
    # Find the __init__ method and update it
    init_method = '''    def __init__(self, **kwargs):
        """Initialize Trade with proper defaults for TradeExecutor compatibility"""
        super().__init__(**kwargs)
        # Ensure side is set from trade_type if not provided
        if hasattr(self, "trade_type") and not hasattr(self, "side"):
            self.side = self.trade_type
        elif hasattr(self, "side") and not hasattr(self, "trade_type"):
            self.trade_type = self.side'''
    
    updated_init_method = '''    def __init__(self, **kwargs):
        """Initialize Trade with proper defaults for TradeExecutor compatibility"""
        # Set side from trade_type if provided but side is not
        if 'trade_type' in kwargs and 'side' not in kwargs:
            kwargs['side'] = kwargs['trade_type']
        elif 'side' in kwargs and 'trade_type' not in kwargs:
            kwargs['trade_type'] = kwargs['side']
            
        super().__init__(**kwargs)
        
        # Ensure both fields are set after initialization
        if hasattr(self, "trade_type") and not hasattr(self, "side"):
            self.side = self.trade_type
        elif hasattr(self, "side") and not hasattr(self, "trade_type"):
            self.trade_type = self.side'''
    
    # Replace the __init__ method
    if init_method in content:
        content = content.replace(init_method, updated_init_method)
        
        # Write the updated content back
        with open(trade_model_path, 'w') as f:
            f.write(content)
        
        print("✅ Trade model constructor fixed")
        return True
    else:
        print("⚠️ Could not find exact __init__ method to replace - manual fix needed")
        return False


def add_service_aliases():
    """Add service aliases for expected class names."""
    
    # Fix AI Trading Service
    ai_trading_path = Path("app/services/ai_trading.py")
    if ai_trading_path.exists():
        print("🔧 Adding AITradingService alias...")
        
        with open(ai_trading_path, 'r') as f:
            content = f.read()
        
        # Add alias at the end of the file
        if "AITradingService = PersonalTradingAI" not in content:
            content += "\n\n# Alias for backward compatibility\nAITradingService = PersonalTradingAI\n"
            
            with open(ai_trading_path, 'w') as f:
                f.write(content)
            
            print("✅ AITradingService alias added")
        else:
            print("✅ AITradingService alias already exists")
    
    # Fix Risk Management Service
    risk_mgmt_path = Path("app/services/risk_management.py")
    if risk_mgmt_path.exists():
        print("🔧 Adding RiskManager alias...")
        
        with open(risk_mgmt_path, 'r') as f:
            content = f.read()
        
        # Add alias at the end of the file
        if "RiskManager = RiskManagementService" not in content:
            content += "\n\n# Alias for backward compatibility\nRiskManager = RiskManagementService\n"
            
            with open(risk_mgmt_path, 'w') as f:
                f.write(content)
            
            print("✅ RiskManager alias added")
        else:
            print("✅ RiskManager alias already exists")


def fix_paper_trading_api():
    """Fix paper trading service API method calls."""
    
    paper_trading_path = Path("app/services/paper_trading.py")
    
    if not paper_trading_path.exists():
        print(f"❌ Paper trading file not found: {paper_trading_path}")
        return False
    
    print("🔧 Fixing paper trading API calls...")
    
    with open(paper_trading_path, 'r') as f:
        content = f.read()
    
    # Replace get_current_price calls with get_quote
    original_line = "            current_price = await self.market_data_service.get_current_price("
    replacement_line = "            quote = await self.market_data_service.get_quote("
    
    if original_line in content:
        # Replace the method call
        content = content.replace(
            original_line + "symbol\n            )",
            replacement_line + "symbol)\n            current_price = quote.get('price') if quote else None"
        )
        
        with open(paper_trading_path, 'w') as f:
            f.write(content)
        
        print("✅ Paper trading API calls fixed")
        return True
    else:
        print("⚠️ get_current_price call not found in expected location")
        return False


def create_service_factory():
    """Create a service factory to handle complex service initialization."""
    
    factory_path = Path("app/services/factory.py")
    
    if factory_path.exists():
        print("✅ Service factory already exists")
        return True
    
    print("🔧 Creating service factory...")
    
    factory_content = '''"""
Service Factory for Trading Platform
====================================

This module provides factory methods to properly initialize complex services
with their required dependencies.
"""

from sqlalchemy.orm import Session
from typing import Optional

from app.services.market_data import MarketDataService
from app.services.advanced_trading import AdvancedTradingService
from app.services.risk_management import RiskManagementService
from app.trading_engine.engine.risk_config import RiskProfile


class TradingServiceFactory:
    """Factory for creating properly configured trading services."""
    
    @staticmethod
    def create_advanced_trading_service(
        db: Session, 
        risk_profile: str = "moderate"
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
            "aggressive": RiskProfile.AGGRESSIVE
        }
        
        risk_enum = risk_profile_map.get(risk_profile.lower(), RiskProfile.MODERATE)
        market_data_service = MarketDataService()
        
        return AdvancedTradingService(
            db=db,
            market_data_service=market_data_service,
            risk_profile=risk_enum
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
def get_advanced_trading_service(db: Session, risk_profile: str = "moderate") -> AdvancedTradingService:
    """Get an advanced trading service instance."""
    return TradingServiceFactory.create_advanced_trading_service(db, risk_profile)


def get_risk_management_service(db: Session) -> RiskManagementService:
    """Get a risk management service instance."""
    return TradingServiceFactory.create_risk_management_service(db)
'''
    
    with open(factory_path, 'w') as f:
        f.write(factory_content)
    
    print("✅ Service factory created")
    return True


def create_env_template():
    """Create a template .env file with required configurations."""
    
    env_template_path = Path(".env.template")
    
    if env_template_path.exists():
        print("✅ Environment template already exists")
        return True
    
    print("🔧 Creating environment configuration template...")
    
    env_content = '''# Trading Platform Environment Configuration
# ==========================================
# Copy this file to .env and fill in your actual values

# Database Configuration (Required)
DATABASE_URL=sqlite:///./trading.db

# Trading Environment
ENVIRONMENT=development
LIVE_TRADING_ENABLED=false

# Alpaca Broker Integration (Optional)
# Get these from: https://alpaca.markets/
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Market Data APIs (Optional)
# Get this from: https://finnhub.io/
FINNHUB_API_KEY=your_finnhub_api_key_here

# Risk Management Configuration
MAX_POSITION_SIZE_PCT=0.15
MAX_DAILY_LOSS_PCT=0.05
MAX_SECTOR_CONCENTRATION_PCT=0.30

# Paper Trading Configuration
PAPER_TRADING_SLIPPAGE_BPS=2
PAPER_TRADING_COMMISSION=0.005
PAPER_TRADING_MIN_COMMISSION=1.0

# Security Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging Configuration
LOG_LEVEL=INFO
'''
    
    with open(env_template_path, 'w') as f:
        f.write(env_content)
    
    print("✅ Environment template created")
    print("ℹ️  Copy .env.template to .env and update with your actual values")
    return True


def run_verification_test():
    """Run a quick verification test to check if fixes work."""
    
    print("\n🧪 Running verification tests...")
    
    try:
        # Test imports
        sys.path.append('.')
        
        from app.services.ai_trading import AITradingService
        from app.services.risk_management import RiskManager
        from app.models.trade import Trade, TradeType, OrderType
        
        print("✅ Service imports working")
        
        # Test Trade model initialization
        trade_data = {
            'symbol': 'TEST',
            'trade_type': TradeType.BUY,
            'order_type': OrderType.MARKET,
            'quantity': 10,
            'portfolio_id': 1,
            'user_id': 1
        }
        
        trade = Trade(**trade_data)
        
        if hasattr(trade, 'side') and trade.side == TradeType.BUY:
            print("✅ Trade model initialization working")
        else:
            print("❌ Trade model side field not set properly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def main():
    """Run all fixes."""
    
    print("🚀 Trading Services Quick Fix Script")
    print("=" * 50)
    
    success_count = 0
    total_fixes = 5
    
    fixes = [
        ("Trade Model Constructor", fix_trade_model),
        ("Service Aliases", add_service_aliases),
        ("Paper Trading API", fix_paper_trading_api),
        ("Service Factory", create_service_factory),
        ("Environment Template", create_env_template),
    ]
    
    for fix_name, fix_function in fixes:
        print(f"\n📋 Applying: {fix_name}")
        try:
            if fix_function():
                success_count += 1
        except Exception as e:
            print(f"❌ Error applying {fix_name}: {e}")
    
    print(f"\n📊 Fix Summary: {success_count}/{total_fixes} fixes applied successfully")
    
    if success_count == total_fixes:
        print("🎉 All fixes applied successfully!")
        run_verification_test()
    else:
        print("⚠️  Some fixes failed - manual intervention may be required")
    
    print("\n📝 Next Steps:")
    print("1. Copy .env.template to .env and configure your API keys")
    print("2. Run the test suite to verify fixes: python test_trading_services_comprehensive.py")
    print("3. Check the TRADING_SERVICES_ANALYSIS_REPORT.md for detailed analysis")


if __name__ == "__main__":
    main()