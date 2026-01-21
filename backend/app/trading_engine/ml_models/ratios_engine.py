"""
Financial Ratios Engine - Phase 1 Enhancement
Uses FinanceToolkit for 150+ transparent financial ratio calculations.

Integrates with existing ELSON trading platform to provide:
- Profitability ratios (ROE, ROA, margins)
- Liquidity ratios (current ratio, quick ratio)
- Solvency ratios (debt/equity, interest coverage)
- Efficiency ratios (asset turnover, inventory turnover)
- Valuation ratios (P/E, P/B, EV/EBITDA)
- Risk metrics (Sharpe, Sortino, VaR, Max Drawdown)
- Financial models (Altman Z-Score, Piotroski F-Score, DuPont)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

# FinanceToolkit import
try:
    from financetoolkit import Toolkit

    FINANCETOOLKIT_AVAILABLE = True
except ImportError:
    FINANCETOOLKIT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ElsonFinancialRatios:
    """
    150+ transparent financial ratios from FinanceToolkit

    Usage:
        ratios = ElsonFinancialRatios(['AAPL', 'GOOGL', 'MSFT'])
        all_ratios = ratios.get_all_ratios()
        risk_metrics = ratios.get_risk_metrics()
        models = ratios.get_financial_models()
    """

    def __init__(
        self,
        symbols: Union[str, List[str]],
        api_key: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        Initialize the financial ratios engine

        Args:
            symbols: Stock ticker symbol(s) to analyze
            api_key: Financial Modeling Prep API key (optional, uses free tier if not provided)
            start_date: Start date for historical data (YYYY-MM-DD)
            end_date: End date for historical data (YYYY-MM-DD)
        """
        self.symbols = [symbols] if isinstance(symbols, str) else symbols
        self.api_key = api_key
        self.start_date = start_date or (
            datetime.now() - timedelta(days=365 * 5)
        ).strftime("%Y-%m-%d")
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.available = FINANCETOOLKIT_AVAILABLE
        self.toolkit = None

        if not self.available:
            logger.warning(
                "FinanceToolkit not installed. Install with: pip install financetoolkit"
            )
            return

        self._initialize_toolkit()

    def _initialize_toolkit(self) -> None:
        """Initialize the FinanceToolkit instance"""
        if not self.available:
            return

        try:
            self.toolkit = Toolkit(
                tickers=self.symbols,
                api_key=self.api_key,
                start_date=self.start_date,
                end_date=self.end_date,
                quarterly=False,
            )
            logger.info(f"FinanceToolkit initialized for {len(self.symbols)} symbol(s)")
        except Exception as e:
            logger.error(f"Error initializing FinanceToolkit: {str(e)}")
            self.toolkit = None

    def get_all_ratios(self) -> Dict[str, pd.DataFrame]:
        """
        Get all financial ratios organized by category

        Returns:
            Dictionary with ratio categories as keys and DataFrames as values:
            - profitability: ROE, ROA, margins, etc.
            - liquidity: Current ratio, quick ratio, etc.
            - solvency: Debt/equity, interest coverage, etc.
            - efficiency: Asset turnover, inventory turnover, etc.
            - valuation: P/E, P/B, EV/EBITDA, etc.
        """
        if not self.available or self.toolkit is None:
            logger.warning("FinanceToolkit not available")
            return self._get_fallback_ratios()

        ratios = {}

        try:
            # Profitability Ratios
            try:
                ratios["profitability"] = (
                    self.toolkit.ratios.collect_profitability_ratios()
                )
            except Exception as e:
                logger.warning(f"Could not fetch profitability ratios: {str(e)}")
                ratios["profitability"] = pd.DataFrame()

            # Liquidity Ratios
            try:
                ratios["liquidity"] = self.toolkit.ratios.collect_liquidity_ratios()
            except Exception as e:
                logger.warning(f"Could not fetch liquidity ratios: {str(e)}")
                ratios["liquidity"] = pd.DataFrame()

            # Solvency Ratios
            try:
                ratios["solvency"] = self.toolkit.ratios.collect_solvency_ratios()
            except Exception as e:
                logger.warning(f"Could not fetch solvency ratios: {str(e)}")
                ratios["solvency"] = pd.DataFrame()

            # Efficiency Ratios
            try:
                ratios["efficiency"] = self.toolkit.ratios.collect_efficiency_ratios()
            except Exception as e:
                logger.warning(f"Could not fetch efficiency ratios: {str(e)}")
                ratios["efficiency"] = pd.DataFrame()

            # Valuation Ratios
            try:
                ratios["valuation"] = self.toolkit.ratios.collect_valuation_ratios()
            except Exception as e:
                logger.warning(f"Could not fetch valuation ratios: {str(e)}")
                ratios["valuation"] = pd.DataFrame()

        except Exception as e:
            logger.error(f"Error collecting ratios: {str(e)}")

        return ratios

    def _get_fallback_ratios(self) -> Dict[str, pd.DataFrame]:
        """Return empty DataFrames when FinanceToolkit is not available"""
        return {
            "profitability": pd.DataFrame(),
            "liquidity": pd.DataFrame(),
            "solvency": pd.DataFrame(),
            "efficiency": pd.DataFrame(),
            "valuation": pd.DataFrame(),
        }

    def get_profitability_ratios(self) -> pd.DataFrame:
        """
        Get profitability ratios

        Returns:
            DataFrame with ratios including:
            - Gross Margin
            - Operating Margin
            - Net Profit Margin
            - Return on Equity (ROE)
            - Return on Assets (ROA)
            - Return on Invested Capital (ROIC)
            - EBITDA Margin
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        try:
            return self.toolkit.ratios.collect_profitability_ratios()
        except Exception as e:
            logger.error(f"Error fetching profitability ratios: {str(e)}")
            return pd.DataFrame()

    def get_liquidity_ratios(self) -> pd.DataFrame:
        """
        Get liquidity ratios

        Returns:
            DataFrame with ratios including:
            - Current Ratio
            - Quick Ratio
            - Cash Ratio
            - Working Capital
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        try:
            return self.toolkit.ratios.collect_liquidity_ratios()
        except Exception as e:
            logger.error(f"Error fetching liquidity ratios: {str(e)}")
            return pd.DataFrame()

    def get_solvency_ratios(self) -> pd.DataFrame:
        """
        Get solvency ratios

        Returns:
            DataFrame with ratios including:
            - Debt to Equity Ratio
            - Debt to Assets Ratio
            - Interest Coverage Ratio
            - Equity Multiplier
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        try:
            return self.toolkit.ratios.collect_solvency_ratios()
        except Exception as e:
            logger.error(f"Error fetching solvency ratios: {str(e)}")
            return pd.DataFrame()

    def get_efficiency_ratios(self) -> pd.DataFrame:
        """
        Get efficiency ratios

        Returns:
            DataFrame with ratios including:
            - Asset Turnover Ratio
            - Inventory Turnover Ratio
            - Receivables Turnover Ratio
            - Days Sales Outstanding
            - Days Inventory Outstanding
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        try:
            return self.toolkit.ratios.collect_efficiency_ratios()
        except Exception as e:
            logger.error(f"Error fetching efficiency ratios: {str(e)}")
            return pd.DataFrame()

    def get_valuation_ratios(self) -> pd.DataFrame:
        """
        Get valuation ratios

        Returns:
            DataFrame with ratios including:
            - Price to Earnings (P/E) Ratio
            - Price to Book (P/B) Ratio
            - Price to Sales (P/S) Ratio
            - EV/EBITDA
            - PEG Ratio
            - Earnings Yield
            - Dividend Yield
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        try:
            return self.toolkit.ratios.collect_valuation_ratios()
        except Exception as e:
            logger.error(f"Error fetching valuation ratios: {str(e)}")
            return pd.DataFrame()

    def get_risk_metrics(self) -> pd.DataFrame:
        """
        Get risk metrics for the portfolio

        Returns:
            DataFrame with metrics including:
            - Sharpe Ratio
            - Sortino Ratio
            - Treynor Ratio
            - Value at Risk (VaR)
            - Conditional VaR (CVaR)
            - Maximum Drawdown
            - Beta
            - Alpha
            - Volatility
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        try:
            return self.toolkit.risk.collect_all_metrics()
        except Exception as e:
            logger.error(f"Error fetching risk metrics: {str(e)}")
            return pd.DataFrame()

    def get_financial_models(self) -> Dict[str, pd.DataFrame]:
        """
        Get financial model outputs

        Returns:
            Dictionary with model results:
            - altman_z_score: Bankruptcy prediction score
            - piotroski_score: Financial health score (0-9)
            - dupont_analysis: Extended DuPont breakdown
            - wacc: Weighted Average Cost of Capital
        """
        if not self.available or self.toolkit is None:
            return {}

        models = {}

        try:
            # Altman Z-Score (bankruptcy prediction)
            try:
                models["altman_z_score"] = self.toolkit.models.get_altman_z_score()
            except Exception as e:
                logger.warning(f"Could not calculate Altman Z-Score: {str(e)}")

            # Piotroski F-Score (financial health)
            try:
                models["piotroski_score"] = self.toolkit.models.get_piotroski_score()
            except Exception as e:
                logger.warning(f"Could not calculate Piotroski Score: {str(e)}")

            # Extended DuPont Analysis
            try:
                models["dupont_analysis"] = (
                    self.toolkit.models.get_extended_dupont_analysis()
                )
            except Exception as e:
                logger.warning(f"Could not calculate DuPont Analysis: {str(e)}")

            # WACC
            try:
                models["wacc"] = (
                    self.toolkit.models.get_weighted_average_cost_of_capital()
                )
            except Exception as e:
                logger.warning(f"Could not calculate WACC: {str(e)}")

        except Exception as e:
            logger.error(f"Error calculating financial models: {str(e)}")

        return models

    def get_company_score(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get an overall company health score based on multiple metrics

        Args:
            symbol: Specific symbol to score (uses first symbol if not provided)

        Returns:
            Dictionary with scoring components and overall score
        """
        if not self.available or self.toolkit is None:
            return {"overall_score": 0, "available": False}

        target_symbol = symbol or self.symbols[0]

        try:
            score_components = {}

            # Get Piotroski Score (0-9, higher is better)
            try:
                piotroski = self.toolkit.models.get_piotroski_score()
                if target_symbol in piotroski.index:
                    latest_score = piotroski.loc[target_symbol].iloc[-1]
                    score_components["piotroski"] = {
                        "value": float(latest_score) if pd.notna(latest_score) else 0,
                        "max": 9,
                        "interpretation": "Financial health (higher is better)",
                    }
            except Exception:
                pass

            # Get Altman Z-Score
            try:
                altman = self.toolkit.models.get_altman_z_score()
                if target_symbol in altman.index:
                    latest_z = altman.loc[target_symbol].iloc[-1]
                    score_components["altman_z"] = {
                        "value": float(latest_z) if pd.notna(latest_z) else 0,
                        "safe_zone": ">2.99",
                        "grey_zone": "1.81-2.99",
                        "distress_zone": "<1.81",
                        "interpretation": "Bankruptcy risk (higher is safer)",
                    }
            except Exception:
                pass

            # Calculate overall score (normalized 0-100)
            overall = 50  # Default neutral score
            if "piotroski" in score_components:
                # Piotroski contributes 50% of score
                overall = (score_components["piotroski"]["value"] / 9) * 50

            if "altman_z" in score_components:
                z = score_components["altman_z"]["value"]
                # Altman Z contributes 50% of score
                if z > 2.99:
                    overall += 50
                elif z > 1.81:
                    overall += 25
                # else: adds 0

            return {
                "symbol": target_symbol,
                "overall_score": round(overall, 2),
                "components": score_components,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating company score: {str(e)}")
            return {"symbol": target_symbol, "overall_score": 0, "error": str(e)}

    def compare_companies(self, metrics: List[str] = None) -> pd.DataFrame:
        """
        Compare multiple companies across selected metrics

        Args:
            metrics: List of metric names to compare

        Returns:
            DataFrame with companies as columns and metrics as rows
        """
        if not self.available or self.toolkit is None:
            return pd.DataFrame()

        if metrics is None:
            metrics = [
                "Return on Equity",
                "Net Profit Margin",
                "Current Ratio",
                "Debt to Equity Ratio",
                "Price to Earnings Ratio",
            ]

        try:
            all_ratios = self.get_all_ratios()

            # Combine all ratio DataFrames
            combined = pd.concat(
                [
                    all_ratios["profitability"],
                    all_ratios["liquidity"],
                    all_ratios["solvency"],
                    all_ratios["valuation"],
                ]
            )

            # Filter to selected metrics
            if not combined.empty:
                available_metrics = [m for m in metrics if m in combined.index]
                if available_metrics:
                    return combined.loc[available_metrics]

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error comparing companies: {str(e)}")
            return pd.DataFrame()


def quick_ratio_analysis(symbol: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform a quick financial ratio analysis for a single symbol

    Args:
        symbol: Stock ticker symbol
        api_key: Optional FMP API key

    Returns:
        Dictionary with key ratios and scores
    """
    ratios = ElsonFinancialRatios(symbol, api_key=api_key)

    return {
        "symbol": symbol,
        "profitability": (
            ratios.get_profitability_ratios().to_dict()
            if not ratios.get_profitability_ratios().empty
            else {}
        ),
        "valuation": (
            ratios.get_valuation_ratios().to_dict()
            if not ratios.get_valuation_ratios().empty
            else {}
        ),
        "risk": (
            ratios.get_risk_metrics().to_dict()
            if not ratios.get_risk_metrics().empty
            else {}
        ),
        "models": ratios.get_financial_models(),
        "score": ratios.get_company_score(),
    }
