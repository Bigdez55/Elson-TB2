"""
Hybrid Model Evaluation Module.

This module provides tools for backtesting the hybrid model with the enhanced
circuit breaker and adaptive parameter optimization across different volatility regimes.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, NamedTuple
import datetime
import logging
import json
import matplotlib.pyplot as plt
from enum import Enum
from dataclasses import dataclass

from Elson.trading_engine.volatility_regime.volatility_detector import VolatilityRegime, VolatilityDetector
from Elson.trading_engine.adaptive_parameters import AdaptiveParameterOptimizer, MarketCondition
from Elson.trading_engine.engine.circuit_breaker import CircuitBreaker, CircuitBreakerStatus, CircuitBreakerType

logger = logging.getLogger(__name__)

@dataclass
class RegimePerformance:
    """Performance metrics for a specific volatility regime."""
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    sample_count: int
    volatility_regime: VolatilityRegime
    avg_position_size: float
    circuit_breaker_activations: int
    

@dataclass
class BacktestResult:
    """Overall backtest results."""
    low_volatility: RegimePerformance
    normal_volatility: RegimePerformance
    high_volatility: RegimePerformance
    extreme_volatility: RegimePerformance
    overall_win_rate: float
    overall_return: float
    overall_sharpe: float
    volatility_robustness: float
    success_criteria_met: bool
    parameter_adaptation_count: int
    position_size_adjusted_win_rate: float
    test_period: Tuple[datetime.datetime, datetime.datetime]


class TradingDecision(Enum):
    """Enum for trading decisions."""
    BUY = 1
    SELL = 2
    HOLD = 0


class HybridModelBacktester:
    """
    Backtester for the hybrid model with adaptive parameters and enhanced circuit breaker.
    
    This backtester evaluates the performance of the hybrid model across different
    volatility regimes to validate that the Phase 2 implementation meets the
    win rate targets specified in the success criteria.
    """
    
    def __init__(
        self,
        data_path: Optional[str] = None,
        output_path: Optional[str] = None,
        enable_circuit_breaker: bool = True,
        enable_adaptive_parameters: bool = True,
    ):
        """
        Initialize the backtester.
        
        Args:
            data_path: Path to the market data for backtesting
            output_path: Path to store backtest results
            enable_circuit_breaker: Whether to enable the enhanced circuit breaker
            enable_adaptive_parameters: Whether to enable adaptive parameter optimization
        """
        self.data_path = data_path
        self.output_path = output_path or os.path.join(os.getcwd(), "backtest_results")
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_adaptive_parameters = enable_adaptive_parameters
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Initialize components
        self.volatility_detector = VolatilityDetector()
        self.parameter_optimizer = AdaptiveParameterOptimizer() if enable_adaptive_parameters else None
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        
        # Performance tracking
        self.trades: List[Dict[str, Any]] = []
        self.parameter_adaptations: List[Dict[str, Any]] = []
        self.circuit_breaker_events: List[Dict[str, Any]] = []
        
        # Configuration
        self.trading_fee = 0.001  # 0.1% trading fee
        self.slippage = 0.001  # 0.1% slippage
        
    def _load_market_data(self, data_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load market data for backtesting.
        
        Args:
            data_path: Path to the market data file
            
        Returns:
            DataFrame with market data
        """
        file_path = data_path or self.data_path
        if not file_path:
            raise ValueError("No data path specified")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        # Load the data
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            data = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
            
        # Ensure required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in data.columns]
            raise ValueError(f"Missing required columns: {missing}")
            
        # Convert date to datetime if it's not already
        if data['date'].dtype != 'datetime64[ns]':
            data['date'] = pd.to_datetime(data['date'])
            
        # Set the date as index
        data.set_index('date', inplace=True)
            
        return data
        
    def _generate_synthetic_data(
        self, 
        periods: int = 1000, 
        volatility_regimes: Optional[List[Tuple[int, VolatilityRegime]]] = None
    ) -> pd.DataFrame:
        """
        Generate synthetic market data for backtesting.
        
        Args:
            periods: Number of periods to generate
            volatility_regimes: List of (length, regime) tuples to control volatility regime sequencing
            
        Returns:
            DataFrame with synthetic market data
        """
        # Default volatility regime sequence if not provided
        if volatility_regimes is None:
            volatility_regimes = [
                (200, VolatilityRegime.LOW),
                (200, VolatilityRegime.NORMAL),
                (200, VolatilityRegime.HIGH),
                (200, VolatilityRegime.EXTREME),
                (200, VolatilityRegime.NORMAL)
            ]
            
        # Map regimes to annualized volatility values
        volatility_map = {
            VolatilityRegime.LOW: 0.008,      # 8% annualized
            VolatilityRegime.NORMAL: 0.018,   # 18% annualized
            VolatilityRegime.HIGH: 0.03,      # 30% annualized
            VolatilityRegime.EXTREME: 0.05    # 50% annualized
        }
        
        # Generate price series
        np.random.seed(42)  # For reproducibility
        start_price = 100
        returns = []
        
        # Generate returns for each regime
        for length, regime in volatility_regimes:
            vol = volatility_map[regime]
            # Add regime-specific drift
            if regime == VolatilityRegime.LOW or regime == VolatilityRegime.NORMAL:
                drift = 0.0001  # Slight positive drift for low/normal vol
            else:
                drift = -0.0001  # Slight negative drift for high/extreme vol
                
            regime_returns = np.random.normal(drift, vol, length)
            returns.extend(regime_returns)
            
        # Ensure we have exactly the requested number of periods
        returns = returns[:periods]
        if len(returns) < periods:
            # Add more normal volatility if needed
            additional = np.random.normal(0, volatility_map[VolatilityRegime.NORMAL], periods - len(returns))
            returns.extend(additional)
            
        # Convert returns to prices
        prices = start_price * np.cumprod(1 + np.array(returns))
        
        # Create date range
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=periods)
        dates = pd.date_range(start=start_date, end=end_date, periods=periods)
        
        # Create DataFrame
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, periods)),
            'high': prices * (1 + abs(np.random.normal(0, 0.002, periods))),
            'low': prices * (1 - abs(np.random.normal(0, 0.002, periods))),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, periods)
        }, index=dates)
        
        return df
        
    def _simulate_simple_prediction(
        self, 
        data: pd.DataFrame, 
        lookback: int = 20, 
        confidence_multiplier: float = 1.0
    ) -> List[TradingDecision]:
        """
        Simulate predictions from a simple trading strategy.
        
        This is a placeholder for the actual hybrid model predictions.
        In a real implementation, this would call the hybrid model to generate predictions.
        
        Args:
            data: Market data
            lookback: Number of periods to look back for prediction
            confidence_multiplier: Multiplier for confidence threshold
            
        Returns:
            List of trading decisions (BUY, SELL, HOLD)
        """
        # Calculate some basic indicators
        data = data.copy()
        
        # Calculate moving averages
        data['ma_fast'] = data['close'].rolling(window=lookback // 2).mean()
        data['ma_slow'] = data['close'].rolling(window=lookback).mean()
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=lookback).mean()
        avg_loss = loss.rolling(window=lookback).mean()
        rs = avg_gain / avg_loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Generate trading signals
        decisions = []
        
        for i in range(lookback, len(data)):
            # Moving average crossover strategy with RSI filter
            if (data['ma_fast'].iloc[i-1] < data['ma_slow'].iloc[i-1] and 
                data['ma_fast'].iloc[i] > data['ma_slow'].iloc[i] and
                data['rsi'].iloc[i] < 70 * confidence_multiplier):
                decisions.append(TradingDecision.BUY)
            elif (data['ma_fast'].iloc[i-1] > data['ma_slow'].iloc[i-1] and 
                  data['ma_fast'].iloc[i] < data['ma_slow'].iloc[i] and
                  data['rsi'].iloc[i] > 30 / confidence_multiplier):
                decisions.append(TradingDecision.SELL)
            else:
                decisions.append(TradingDecision.HOLD)
                
        # Pad with HOLD decisions for the initial lookback period
        padding = [TradingDecision.HOLD] * lookback
        return padding + decisions
        
    def _execute_trade(
        self, 
        decision: TradingDecision, 
        current_price: float, 
        position_size: float = 1.0
    ) -> Dict[str, Any]:
        """
        Execute a simulated trade.
        
        Args:
            decision: Trading decision (BUY, SELL, HOLD)
            current_price: Current market price
            position_size: Position size multiplier (0.0-1.0)
            
        Returns:
            Trade details
        """
        # Skip HOLD decisions
        if decision == TradingDecision.HOLD:
            return None
            
        # Apply slippage
        executed_price = current_price * (1 + self.slippage) if decision == TradingDecision.BUY else current_price * (1 - self.slippage)
        
        # Calculate fee
        fee = executed_price * self.trading_fee
        
        # Create trade record
        trade = {
            'timestamp': datetime.datetime.now().isoformat(),
            'decision': decision.name,
            'price': current_price,
            'executed_price': executed_price,
            'fee': fee,
            'position_size': position_size
        }
        
        return trade
        
    def _evaluate_performance(
        self, 
        trades: List[Dict[str, Any]], 
        data: pd.DataFrame, 
        volatility_data: Dict[int, Tuple[VolatilityRegime, float]]
    ) -> BacktestResult:
        """
        Evaluate the performance of the trading strategy.
        
        Args:
            trades: List of executed trades
            data: Market data
            volatility_data: Dictionary mapping data indices to (regime, volatility_value) tuples
            
        Returns:
            Backtest results
        """
        # Group trades by volatility regime
        trades_by_regime = {
            VolatilityRegime.LOW: [],
            VolatilityRegime.NORMAL: [],
            VolatilityRegime.HIGH: [],
            VolatilityRegime.EXTREME: []
        }
        
        # Account for position sizing in win rate calculation
        position_size_adjusted_wins = 0
        total_position_size = 0
        
        # Process trades
        for i, trade in enumerate(trades):
            if trade is None:  # Skip None trades (HOLDs)
                continue
                
            # Find the next trade to calculate profit/loss
            next_trade = None
            for j in range(i + 1, len(trades)):
                if trades[j] is not None and trades[j]['decision'] != trade['decision']:
                    next_trade = trades[j]
                    break
                    
            if next_trade is None:
                # No matching closing trade found
                continue
                
            # Calculate profit/loss
            if trade['decision'] == 'BUY':
                profit = (next_trade['executed_price'] - trade['executed_price']) / trade['executed_price']
                profit -= (trade['fee'] + next_trade['fee']) / trade['executed_price']
            else:  # SELL
                profit = (trade['executed_price'] - next_trade['executed_price']) / trade['executed_price']
                profit -= (trade['fee'] + next_trade['fee']) / trade['executed_price']
                
            # Apply position sizing
            position_size = trade['position_size']
            adjusted_profit = profit * position_size
                
            # Add trade performance
            trade_performance = {
                'entry_time': trade['timestamp'],
                'exit_time': next_trade['timestamp'],
                'entry_price': trade['executed_price'],
                'exit_price': next_trade['executed_price'],
                'direction': trade['decision'],
                'profit_pct': profit * 100,  # Convert to percentage
                'position_size': position_size,
                'adjusted_profit_pct': adjusted_profit * 100
            }
            
            # Find the volatility regime at the time of trade
            # Use a different approach since method='nearest' may not be supported
            trade_time = pd.to_datetime(trade['timestamp'])
            time_diffs = abs(data.index - trade_time)
            trade_index = time_diffs.argmin() if len(time_diffs) > 0 else 0
            regime, volatility_value = volatility_data.get(trade_index, (VolatilityRegime.NORMAL, 20.0))
            
            trade_performance['volatility_regime'] = regime.name
            trade_performance['volatility_value'] = volatility_value
            
            # Add to appropriate regime list
            trades_by_regime[regime].append(trade_performance)
            
            # Adjusted win rate calculation
            if profit > 0:
                position_size_adjusted_wins += position_size
            total_position_size += position_size
            
        # Calculate performance metrics for each regime
        regime_performance = {}
        
        for regime, regime_trades in trades_by_regime.items():
            if not regime_trades:
                # No trades for this regime
                regime_performance[regime] = RegimePerformance(
                    win_rate=0.0,
                    avg_return=0.0,
                    sharpe_ratio=0.0,
                    sample_count=0,
                    volatility_regime=regime,
                    avg_position_size=0.0,
                    circuit_breaker_activations=0
                )
                continue
                
            # Calculate win rate
            winning_trades = [t for t in regime_trades if t['profit_pct'] > 0]
            win_rate = len(winning_trades) / len(regime_trades)
            
            # Calculate average return
            avg_return = sum(t['adjusted_profit_pct'] for t in regime_trades) / len(regime_trades)
            
            # Calculate Sharpe ratio
            returns = np.array([t['adjusted_profit_pct'] for t in regime_trades])
            sharpe_ratio = 0.0
            if len(returns) > 1 and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns)
                
            # Average position size
            avg_position_size = sum(t['position_size'] for t in regime_trades) / len(regime_trades)
            
            # Count circuit breaker activations
            circuit_breaker_activations = len([e for e in self.circuit_breaker_events 
                                            if e['volatility_regime'] == regime.name])
            
            regime_performance[regime] = RegimePerformance(
                win_rate=win_rate,
                avg_return=avg_return,
                sharpe_ratio=sharpe_ratio,
                sample_count=len(regime_trades),
                volatility_regime=regime,
                avg_position_size=avg_position_size,
                circuit_breaker_activations=circuit_breaker_activations
            )
            
        # Calculate overall performance metrics
        all_trades = []
        for trades in trades_by_regime.values():
            all_trades.extend(trades)
            
        if not all_trades:
            logger.warning("No trades executed during the backtest period")
            overall_win_rate = 0.0
            overall_return = 0.0
            overall_sharpe = 0.0
            volatility_robustness = 0.0
        else:
            # Overall win rate
            winning_trades = [t for t in all_trades if t['profit_pct'] > 0]
            overall_win_rate = len(winning_trades) / len(all_trades)
            
            # Overall average return
            overall_return = sum(t['adjusted_profit_pct'] for t in all_trades) / len(all_trades)
            
            # Overall Sharpe ratio
            returns = np.array([t['adjusted_profit_pct'] for t in all_trades])
            overall_sharpe = 0.0
            if len(returns) > 1 and np.std(returns) > 0:
                overall_sharpe = np.mean(returns) / np.std(returns)
                
            # Position size adjusted win rate
            position_size_adjusted_win_rate = position_size_adjusted_wins / total_position_size if total_position_size > 0 else 0.0
                
            # Volatility robustness (difference between best and worst regime performance)
            non_empty_regimes = {r: p for r, p in regime_performance.items() if p.sample_count > 0}
            if len(non_empty_regimes) >= 2:
                win_rates = [p.win_rate for p in non_empty_regimes.values()]
                volatility_robustness = (max(win_rates) - min(win_rates)) * 100  # Convert to percentage points
            else:
                volatility_robustness = 0.0
                
        # Check if success criteria are met
        success_criteria_met = True
        
        # 1. High volatility win rate >= 65%
        if regime_performance[VolatilityRegime.HIGH].sample_count > 0:
            high_vol_target = regime_performance[VolatilityRegime.HIGH].win_rate >= 0.65
            success_criteria_met = success_criteria_met and high_vol_target
        
        # 2. Extreme volatility win rate >= 60%
        if regime_performance[VolatilityRegime.EXTREME].sample_count > 0:
            extreme_vol_target = regime_performance[VolatilityRegime.EXTREME].win_rate >= 0.60
            success_criteria_met = success_criteria_met and extreme_vol_target
        
        # 3. Maximum 10% performance differential between regimes
        if volatility_robustness <= 10.0:
            diff_target = True
        else:
            diff_target = False
        success_criteria_met = success_criteria_met and diff_target
        
        # Get test period
        start_date = data.index[0]
        end_date = data.index[-1]
        
        # Record parameter adaptations count
        parameter_adaptation_count = len(self.parameter_adaptations)
        
        # Create final result
        result = BacktestResult(
            low_volatility=regime_performance[VolatilityRegime.LOW],
            normal_volatility=regime_performance[VolatilityRegime.NORMAL],
            high_volatility=regime_performance[VolatilityRegime.HIGH],
            extreme_volatility=regime_performance[VolatilityRegime.EXTREME],
            overall_win_rate=overall_win_rate,
            overall_return=overall_return,
            overall_sharpe=overall_sharpe,
            volatility_robustness=volatility_robustness,
            success_criteria_met=success_criteria_met,
            parameter_adaptation_count=parameter_adaptation_count,
            position_size_adjusted_win_rate=position_size_adjusted_win_rate,
            test_period=(start_date, end_date)
        )
        
        return result
    
    def run_backtest(
        self, 
        data: Optional[pd.DataFrame] = None,
        test_name: str = "hybrid_model_backtest",
        generate_plots: bool = True
    ) -> BacktestResult:
        """
        Run a backtest for the hybrid model with adaptive parameters and circuit breaker.
        
        Args:
            data: Market data (if None, will load from data_path or generate synthetic data)
            test_name: Name for the test run (used for saving results)
            generate_plots: Whether to generate performance plots
            
        Returns:
            Backtest results
        """
        # Load or generate data
        if data is None:
            try:
                data = self._load_market_data()
                logger.info(f"Loaded market data with {len(data)} records")
            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"Could not load market data: {str(e)}. Generating synthetic data.")
                data = self._generate_synthetic_data()
                logger.info(f"Generated synthetic market data with {len(data)} records")
                
        # Reset performance tracking
        self.trades = []
        self.parameter_adaptations = []
        self.circuit_breaker_events = []
        
        # Track volatility regimes
        volatility_data = {}
        
        # Backtest loop
        executed_trades = [None] * len(data)  # Initialize with None for each data point
        
        for i in range(len(data)):
            # Get current data window for volatility detection
            if i < 20:  # Need some minimum data for volatility detection
                continue
                
            data_window = data.iloc[:i+1]
            
            # Detect volatility regime
            volatility_regime, volatility_value = self.volatility_detector.detect_regime(data_window)
            
            # Store volatility regime for this data point
            volatility_data[i] = (volatility_regime, volatility_value)
            
            # Convert volatility regime to circuit breaker level
            if self.enable_circuit_breaker:
                # Handle circuit breaker
                symbol = "BACKTEST"
                
                # Process volatility with circuit breaker
                tripped, cb_status, base_position_size = self.circuit_breaker.process_volatility(
                    volatility_level=volatility_regime.value,
                    volatility_value=volatility_value,
                    symbol=symbol
                )
                
                if tripped:
                    # Record circuit breaker event
                    self.circuit_breaker_events.append({
                        'timestamp': data.index[i].isoformat(),
                        'volatility_regime': volatility_regime.name,
                        'volatility_value': volatility_value,
                        'circuit_breaker_status': cb_status.name,
                        'position_size': base_position_size
                    })
            else:
                # No circuit breaker enabled
                cb_status = CircuitBreakerStatus.CLOSED
                base_position_size = 1.0
                
            # Get optimized parameters if enabled
            if self.enable_adaptive_parameters:
                # Get market data window for parameter optimization
                market_data = data_window.copy()
                
                # Get optimized parameters
                optimized_params = self.parameter_optimizer.get_optimized_parameters(
                    data=market_data,
                    circuit_breaker_status=cb_status if self.enable_circuit_breaker else None
                )
                
                # Record parameter adaptation
                self.parameter_adaptations.append({
                    'timestamp': data.index[i].isoformat(),
                    'volatility_regime': optimized_params['regime_info']['volatility_regime'],
                    'market_condition': optimized_params['regime_info'].get('market_condition', 'UNKNOWN'),
                    'volatility_value': optimized_params['regime_info']['volatility_value'],
                    'lookback_periods': optimized_params['lookback_periods'],
                    'prediction_horizon': optimized_params['prediction_horizon'],
                    'confidence_threshold': optimized_params['confidence_threshold'],
                    'position_sizing': optimized_params['position_sizing']
                })
                
                # Use optimized parameters for prediction
                lookback = optimized_params['lookback_periods']
                confidence_multiplier = optimized_params['confidence_threshold'] / 0.6  # Normalize
                position_size = optimized_params['position_sizing']
            else:
                # Default parameters if not using adaptive optimization
                lookback = 20
                confidence_multiplier = 1.0
                position_size = base_position_size
                
            # Generate prediction
            predictions = self._simulate_simple_prediction(
                data=data_window,
                lookback=lookback,
                confidence_multiplier=confidence_multiplier
            )
            
            # Get the latest prediction (for the current data point)
            latest_prediction = predictions[-1] if predictions else TradingDecision.HOLD
            
            # Execute trade if conditions met
            can_trade = True
            if self.enable_circuit_breaker:
                # Check if circuit breaker allows trading
                allowed, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, "BACKTEST")
                can_trade = allowed
                
            if can_trade and latest_prediction != TradingDecision.HOLD:
                # Execute the trade
                trade = self._execute_trade(
                    decision=latest_prediction,
                    current_price=data.iloc[i]['close'],
                    position_size=position_size
                )
                
                # Add timestamp using the data index
                if trade:
                    trade['timestamp'] = data.index[i].isoformat()
                    executed_trades[i] = trade
        
        # Evaluate performance
        result = self._evaluate_performance(
            trades=executed_trades,
            data=data,
            volatility_data=volatility_data
        )
        
        # Generate plots if requested
        if generate_plots:
            self._generate_performance_plots(result, data, volatility_data, test_name)
            
        # Save results
        self._save_results(result, test_name)
        
        return result
    
    def _generate_performance_plots(
        self, 
        result: BacktestResult, 
        data: pd.DataFrame, 
        volatility_data: Dict[int, Tuple[VolatilityRegime, float]],
        test_name: str
    ) -> None:
        """
        Generate performance plots for the backtest.
        
        Args:
            result: Backtest results
            data: Market data
            volatility_data: Dictionary mapping data indices to (regime, volatility_value) tuples
            test_name: Name for the test run
        """
        # Create a figure directory
        fig_dir = os.path.join(self.output_path, f"{test_name}_figures")
        os.makedirs(fig_dir, exist_ok=True)
        
        # 1. Win Rate by Volatility Regime
        plt.figure(figsize=(10, 6))
        regimes = ['LOW', 'NORMAL', 'HIGH', 'EXTREME']
        win_rates = [
            result.low_volatility.win_rate * 100,
            result.normal_volatility.win_rate * 100,
            result.high_volatility.win_rate * 100,
            result.extreme_volatility.win_rate * 100
        ]
        sample_counts = [
            result.low_volatility.sample_count,
            result.normal_volatility.sample_count,
            result.high_volatility.sample_count,
            result.extreme_volatility.sample_count
        ]
        
        # Colors for each regime
        colors = ['green', 'blue', 'orange', 'red']
        
        # Create the bar chart
        bars = plt.bar(regimes, win_rates, color=colors)
        
        # Add sample count as text
        for i, (bar, count) in enumerate(zip(bars, sample_counts)):
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2, 
                height, 
                f'n={count}', 
                ha='center', 
                va='bottom'
            )
        
        # Add target lines
        plt.axhline(y=65, color='orange', linestyle='--', label='High Vol Target (65%)')
        plt.axhline(y=60, color='red', linestyle='--', label='Extreme Vol Target (60%)')
        
        plt.title('Win Rate by Volatility Regime')
        plt.xlabel('Volatility Regime')
        plt.ylabel('Win Rate (%)')
        plt.ylim(0, 100)
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(os.path.join(fig_dir, 'win_rate_by_regime.png'))
        plt.close()
        
        # 2. Position Sizing by Volatility Regime
        plt.figure(figsize=(10, 6))
        position_sizes = [
            result.low_volatility.avg_position_size * 100,
            result.normal_volatility.avg_position_size * 100,
            result.high_volatility.avg_position_size * 100,
            result.extreme_volatility.avg_position_size * 100
        ]
        
        # Create the bar chart
        plt.bar(regimes, position_sizes, color=colors)
        
        plt.title('Average Position Size by Volatility Regime')
        plt.xlabel('Volatility Regime')
        plt.ylabel('Position Size (%)')
        plt.ylim(0, 105)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(os.path.join(fig_dir, 'position_size_by_regime.png'))
        plt.close()
        
        # 3. Parameter Adaptation Timeline
        if self.parameter_adaptations:
            plt.figure(figsize=(12, 8))
            
            # Prepare data
            timestamps = [pd.to_datetime(p['timestamp']) for p in self.parameter_adaptations]
            lookback_periods = [p['lookback_periods'] for p in self.parameter_adaptations]
            confidence_thresholds = [p['confidence_threshold'] for p in self.parameter_adaptations]
            position_sizing = [p['position_sizing'] for p in self.parameter_adaptations]
            
            # Plot parameters
            plt.subplot(3, 1, 1)
            plt.plot(timestamps, lookback_periods, 'b-', label='Lookback Periods')
            plt.ylabel('Lookback Periods')
            plt.title('Parameter Adaptation Timeline')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            plt.subplot(3, 1, 2)
            plt.plot(timestamps, confidence_thresholds, 'g-', label='Confidence Threshold')
            plt.ylabel('Confidence Threshold')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            plt.subplot(3, 1, 3)
            plt.plot(timestamps, position_sizing, 'r-', label='Position Sizing')
            plt.ylabel('Position Sizing')
            plt.xlabel('Time')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            plt.tight_layout()
            
            # Save the figure
            plt.savefig(os.path.join(fig_dir, 'parameter_adaptation_timeline.png'))
            plt.close()
            
        # 4. Circuit Breaker Activations
        if self.circuit_breaker_events:
            plt.figure(figsize=(12, 6))
            
            # Convert volatility data to DataFrame for plotting
            vol_indices = list(volatility_data.keys())
            vol_regimes = [v[0].name for v in volatility_data.values()]
            vol_values = [v[1] for v in volatility_data.values()]
            
            vol_df = pd.DataFrame({
                'timestamp': [data.index[i] for i in vol_indices],
                'regime': vol_regimes,
                'value': vol_values
            })
            
            # Plot volatility values
            plt.plot(vol_df['timestamp'], vol_df['value'], 'b-', alpha=0.7, label='Volatility (%)')
            
            # Plot circuit breaker events
            cb_timestamps = [pd.to_datetime(e['timestamp']) for e in self.circuit_breaker_events]
            cb_statuses = [e['circuit_breaker_status'] for e in self.circuit_breaker_events]
            
            # Map statuses to y-values for plotting
            status_map = {
                'OPEN': 50,      # Red dot
                'RESTRICTED': 35,  # Orange dot
                'CAUTIOUS': 20,    # Yellow dot
                'CLOSED': 5        # Green dot
            }
            
            # Map statuses to colors
            color_map = {
                'OPEN': 'red',
                'RESTRICTED': 'orange',
                'CAUTIOUS': 'yellow',
                'CLOSED': 'green'
            }
            
            # Plot each status type separately for the legend
            for status in ['OPEN', 'RESTRICTED', 'CAUTIOUS', 'CLOSED']:
                indices = [i for i, s in enumerate(cb_statuses) if s == status]
                if indices:
                    plt.scatter(
                        [cb_timestamps[i] for i in indices],
                        [status_map[status]] * len(indices),
                        color=color_map[status],
                        s=100,
                        label=f'{status} Circuit Breaker'
                    )
            
            plt.title('Volatility and Circuit Breaker Activations')
            plt.xlabel('Time')
            plt.ylabel('Volatility (%)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save the figure
            plt.savefig(os.path.join(fig_dir, 'circuit_breaker_activations.png'))
            plt.close()
            
        # 5. Summary Plot
        plt.figure(figsize=(10, 8))
        
        # Prepare metrics for summary chart
        metrics = [
            result.overall_win_rate * 100,
            result.overall_return,
            result.position_size_adjusted_win_rate * 100,
            result.volatility_robustness
        ]
        
        metric_labels = [
            'Overall Win Rate (%)',
            'Avg Return (%)',
            'Position-Adjusted Win Rate (%)',
            'Volatility Robustness (pp)'
        ]
        
        # Create the summary chart
        plt.barh(metric_labels, metrics, color=['navy', 'teal', 'darkgreen', 'purple'])
        
        # Add target line for volatility robustness
        plt.axvline(x=10, color='red', linestyle='--', label='Robustness Target (≤10pp)')
        
        plt.title('Performance Summary')
        plt.xlabel('Value')
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(os.path.join(fig_dir, 'performance_summary.png'))
        plt.close()
    
    def _save_results(self, result: BacktestResult, test_name: str) -> None:
        """
        Save backtest results to file.
        
        Args:
            result: Backtest results
            test_name: Name for the test run
        """
        # Create result dictionary
        result_dict = {
            'test_name': test_name,
            'test_time': datetime.datetime.now().isoformat(),
            'test_period': {
                'start': result.test_period[0].isoformat(),
                'end': result.test_period[1].isoformat()
            },
            'configuration': {
                'enable_circuit_breaker': self.enable_circuit_breaker,
                'enable_adaptive_parameters': self.enable_adaptive_parameters,
                'trading_fee': self.trading_fee,
                'slippage': self.slippage
            },
            'performance': {
                'overall': {
                    'win_rate': result.overall_win_rate,
                    'avg_return': result.overall_return,
                    'sharpe_ratio': result.overall_sharpe,
                    'volatility_robustness': result.volatility_robustness,
                    'position_size_adjusted_win_rate': result.position_size_adjusted_win_rate
                },
                'by_regime': {
                    'LOW': {
                        'win_rate': result.low_volatility.win_rate,
                        'avg_return': result.low_volatility.avg_return,
                        'sharpe_ratio': result.low_volatility.sharpe_ratio,
                        'sample_count': result.low_volatility.sample_count,
                        'avg_position_size': result.low_volatility.avg_position_size,
                        'circuit_breaker_activations': result.low_volatility.circuit_breaker_activations
                    },
                    'NORMAL': {
                        'win_rate': result.normal_volatility.win_rate,
                        'avg_return': result.normal_volatility.avg_return,
                        'sharpe_ratio': result.normal_volatility.sharpe_ratio,
                        'sample_count': result.normal_volatility.sample_count,
                        'avg_position_size': result.normal_volatility.avg_position_size,
                        'circuit_breaker_activations': result.normal_volatility.circuit_breaker_activations
                    },
                    'HIGH': {
                        'win_rate': result.high_volatility.win_rate,
                        'avg_return': result.high_volatility.avg_return,
                        'sharpe_ratio': result.high_volatility.sharpe_ratio,
                        'sample_count': result.high_volatility.sample_count,
                        'avg_position_size': result.high_volatility.avg_position_size,
                        'circuit_breaker_activations': result.high_volatility.circuit_breaker_activations
                    },
                    'EXTREME': {
                        'win_rate': result.extreme_volatility.win_rate,
                        'avg_return': result.extreme_volatility.avg_return,
                        'sharpe_ratio': result.extreme_volatility.sharpe_ratio,
                        'sample_count': result.extreme_volatility.sample_count,
                        'avg_position_size': result.extreme_volatility.avg_position_size,
                        'circuit_breaker_activations': result.extreme_volatility.circuit_breaker_activations
                    }
                }
            },
            'success_criteria': {
                'met': result.success_criteria_met,
                'high_volatility_target': result.high_volatility.win_rate >= 0.65,
                'extreme_volatility_target': result.extreme_volatility.win_rate >= 0.60,
                'volatility_robustness_target': result.volatility_robustness <= 10.0
            },
            'adaptation_metrics': {
                'parameter_adaptation_count': result.parameter_adaptation_count,
                'circuit_breaker_event_count': len(self.circuit_breaker_events)
            }
        }
        
        # Save as JSON
        result_file = os.path.join(self.output_path, f"{test_name}_results.json")
        with open(result_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
            
        logger.info(f"Saved backtest results to {result_file}")
        
        # Save adaptation and circuit breaker event data if available
        if self.parameter_adaptations:
            param_file = os.path.join(self.output_path, f"{test_name}_parameter_adaptations.json")
            with open(param_file, 'w') as f:
                json.dump(self.parameter_adaptations, f, indent=2)
                
        if self.circuit_breaker_events:
            cb_file = os.path.join(self.output_path, f"{test_name}_circuit_breaker_events.json")
            with open(cb_file, 'w') as f:
                json.dump(self.circuit_breaker_events, f, indent=2)


def run_hybrid_model_backtest(
    data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    enable_circuit_breaker: bool = True,
    enable_adaptive_parameters: bool = True,
    test_name: str = "hybrid_model_backtest",
    generate_plots: bool = True
) -> BacktestResult:
    """
    Run a backtest for the hybrid model with adaptive parameters and circuit breaker.
    
    This is a convenience function that creates and runs a HybridModelBacktester.
    
    Args:
        data_path: Path to the market data for backtesting
        output_path: Path to store backtest results
        enable_circuit_breaker: Whether to enable the enhanced circuit breaker
        enable_adaptive_parameters: Whether to enable adaptive parameter optimization
        test_name: Name for the test run
        generate_plots: Whether to generate performance plots
        
    Returns:
        Backtest results
    """
    # Create and run backtester
    backtester = HybridModelBacktester(
        data_path=data_path,
        output_path=output_path,
        enable_circuit_breaker=enable_circuit_breaker,
        enable_adaptive_parameters=enable_adaptive_parameters
    )
    
    # Run backtest
    result = backtester.run_backtest(
        test_name=test_name,
        generate_plots=generate_plots
    )
    
    return result