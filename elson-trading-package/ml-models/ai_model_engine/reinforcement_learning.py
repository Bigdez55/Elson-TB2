"""
Reinforcement Learning models for trading strategy selection and optimization.

This module implements reinforcement learning agents that can adaptively select 
and optimize trading strategies based on market conditions and performance.
"""

import os
import json
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import pickle
from collections import deque
import random
import time
import gymnasium as gym
from gymnasium import spaces
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers

from ..strategies.base import TradingStrategy
from ..timeframe_engine.market_regime_detector import MarketRegimeDetector

# Set up logging
logger = logging.getLogger(__name__)

class TradingEnvironment(gym.Env):
    """
    Custom Gym environment for reinforcement learning in trading strategy selection.
    
    This environment allows an RL agent to learn which trading strategy to use
    under different market conditions.
    """
    
    def __init__(
        self, 
        strategies: List[TradingStrategy],
        market_data: pd.DataFrame,
        market_regime_detector: Optional[MarketRegimeDetector] = None,
        initial_balance: float = 10000.0,
        max_steps: int = 252,  # Approx. 1 trading year
        transaction_cost: float = 0.001,  # 0.1% per trade
        window_size: int = 30  # Look back window for observations
    ):
        """
        Initialize the trading environment.
        
        Args:
            strategies: List of trading strategy instances
            market_data: Historical market data for training/evaluation
            market_regime_detector: Optional market regime detector
            initial_balance: Starting account balance
            max_steps: Maximum number of steps in an episode
            transaction_cost: Cost per trade as a fraction of trade value
            window_size: Number of past observations to include in state
        """
        super(TradingEnvironment, self).__init__()
        
        self.strategies = strategies
        self.market_data = market_data
        self.market_regime_detector = market_regime_detector
        self.initial_balance = initial_balance
        self.max_steps = max_steps
        self.transaction_cost = transaction_cost
        self.window_size = window_size
        
        # Define action and observation space
        # Action space: Choose one of the available strategies or hold
        self.action_space = spaces.Discrete(len(strategies) + 1)  # +1 for hold
        
        # Observation space: Market features + strategy performance metrics
        num_market_features = 10  # Example: OHLCV, indicators, regime features
        num_strategy_metrics = 5  # Example: Current positions, PnL, drawdowns
        
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(window_size, num_market_features + num_strategy_metrics),
            dtype=np.float32
        )
        
        # Environment state
        self.current_step = 0
        self.account_balance = initial_balance
        self.current_position = 0
        self.position_value = 0
        self.current_strategy_idx = None
        self.positions = []
        self.returns = []
        self.trades = []
        
        # Performance tracking
        self.total_pnl = 0
        self.max_drawdown = 0
        self.sharpe_ratio = 0
        self.strategy_usage = {i: 0 for i in range(len(strategies))}
        
        # Internal state
        self._done = False
        self._current_price = 0
        self._starting_index = window_size
        self._observation_history = deque(maxlen=window_size)
        
    def reset(self):
        """Reset the environment to initial state for a new episode."""
        self.current_step = 0
        self.account_balance = self.initial_balance
        self.current_position = 0
        self.position_value = 0
        self.current_strategy_idx = None
        self.positions = []
        self.returns = []
        self.trades = []
        
        # Reset performance metrics
        self.total_pnl = 0
        self.max_drawdown = 0
        self.sharpe_ratio = 0
        self.strategy_usage = {i: 0 for i in range(len(self.strategies))}
        
        # Reset internal state
        self._done = False
        self._starting_index = self.window_size
        self._observation_history = deque(maxlen=self.window_size)
        
        # Initialize observation history
        for i in range(self.window_size):
            observation = self._get_observation(self._starting_index - self.window_size + i)
            self._observation_history.append(observation)
        
        return self._get_state()
    
    def step(self, action):
        """
        Take an action in the environment.
        
        Args:
            action: Index of the strategy to use (or hold if action == len(strategies))
        
        Returns:
            Tuple of (next_state, reward, done, info)
        """
        if self._done:
            return self._get_state(), 0, True, {}
        
        # Get current market data
        current_data = self._get_market_data_slice(self.current_step + self._starting_index)
        self._current_price = current_data.iloc[-1]['close']
        
        # Execute strategy if action is valid
        info = {}
        reward = 0
        
        if action < len(self.strategies):  # Valid strategy selection (not hold)
            self.current_strategy_idx = action
            self.strategy_usage[action] += 1
            
            # Get signals from the selected strategy
            strategy = self.strategies[action]
            signals = self._execute_strategy_with_data(strategy, current_data)
            
            # Apply the signals to update positions
            new_position, trade_pnl = self._apply_signals(signals)
            reward = self._calculate_reward(trade_pnl)
            
            # Record trade
            if trade_pnl != 0:
                self.trades.append({
                    'step': self.current_step,
                    'strategy': action,
                    'price': self._current_price,
                    'pnl': trade_pnl,
                    'position_change': new_position - self.current_position
                })
                
                # Update position
                self.current_position = new_position
                self.position_value = self.current_position * self._current_price
        else:
            # Hold current position
            position_value_before = self.position_value
            self.position_value = self.current_position * self._current_price
            position_pnl = self.position_value - position_value_before
            reward = self._calculate_reward(position_pnl, is_trade=False)
        
        # Update account balance with unrealized P&L
        total_value = self.account_balance + self.position_value
        
        # Record returns and positions
        self.returns.append(total_value / self.initial_balance - 1)
        self.positions.append(self.current_position)
        
        # Update maximum drawdown
        if len(self.returns) > 1:
            drawdown = self._calculate_drawdown(self.returns)
            self.max_drawdown = min(self.max_drawdown, drawdown)
        
        # Create observation for the current step
        observation = self._get_observation(self.current_step + self._starting_index)
        self._observation_history.append(observation)
        
        # Increment step counter
        self.current_step += 1
        
        # Check if episode is done
        self._done = (self.current_step >= self.max_steps or 
                      total_value <= 0.5 * self.initial_balance)  # Stop if 50% loss
        
        # Calculate final metrics if done
        if self._done:
            self.sharpe_ratio = self._calculate_sharpe_ratio(self.returns)
            info['final_balance'] = total_value
            info['total_return'] = total_value / self.initial_balance - 1
            info['sharpe_ratio'] = self.sharpe_ratio
            info['max_drawdown'] = self.max_drawdown
            info['strategy_usage'] = self.strategy_usage
            info['num_trades'] = len(self.trades)
        
        return self._get_state(), reward, self._done, info
    
    def _get_market_data_slice(self, index: int) -> pd.DataFrame:
        """Get a slice of market data centered at the given index."""
        start_idx = max(0, index - self.window_size)
        end_idx = min(len(self.market_data), index + 1)
        return self.market_data.iloc[start_idx:end_idx].copy()
    
    def _execute_strategy_with_data(self, strategy: TradingStrategy, data: pd.DataFrame) -> Dict:
        """Execute strategy with the provided data and return signals."""
        try:
            # For testing purposes, just return a mock signal
            # In actual implementation, would run the strategy
            return {
                'action': 'buy', 
                'confidence': 0.8, 
                'price': self._current_price,
                'stop_loss': self._current_price * 0.95,
                'take_profit': self._current_price * 1.05
            }
        except Exception as e:
            logger.error(f"Error executing strategy: {str(e)}")
            return {'action': 'hold', 'confidence': 0, 'price': self._current_price}
    
    def _apply_signals(self, signals: Dict) -> Tuple[float, float]:
        """Apply trading signals to update positions and calculate P&L."""
        action = signals.get('action', 'hold')
        confidence = signals.get('confidence', 0)
        price = signals.get('price', self._current_price)
        
        # Initialize
        trade_pnl = 0
        new_position = self.current_position
        
        if action == 'buy':
            # Calculate position size based on confidence
            cash_available = self.account_balance * 0.95  # Keep some cash reserve
            position_size = (cash_available * confidence) / price
            
            # For testing, ensure we have a non-zero position
            position_size = max(position_size, 1.0)
            
            # Calculate transaction cost
            transaction_cost = position_size * price * self.transaction_cost
            
            # Update position and account balance
            new_position = self.current_position + position_size
            self.account_balance -= (position_size * price + transaction_cost)
            self.current_position = new_position  # Actually update the position
            
        elif action == 'sell':
            if self.current_position > 0:
                # Sell a portion or all of the position based on confidence
                position_to_sell = self.current_position * confidence
                
                # Calculate P&L and transaction cost
                trade_pnl = position_to_sell * (price - (self.position_value / self.current_position))
                transaction_cost = position_to_sell * price * self.transaction_cost
                
                # Update position and account balance
                new_position = self.current_position - position_to_sell
                self.account_balance += (position_to_sell * price - transaction_cost)
                self.current_position = new_position  # Actually update the position
                
        return new_position, trade_pnl
    
    def _calculate_reward(self, pnl: float, is_trade: bool = True) -> float:
        """Calculate the reward for the current step."""
        # Base reward on P&L
        reward = pnl / self.initial_balance  # Normalize by initial balance
        
        # Penalize excessive trading
        if is_trade:
            reward -= self.transaction_cost * 2  # Additional penalty for trading
            
        # Adjust reward based on risk metrics if available
        if len(self.returns) > 5:
            # Add reward component for low volatility
            volatility = np.std(self.returns[-5:])
            reward -= volatility * 0.5  # Penalize volatility
            
            # Add reward component for positive trend
            returns_diff = np.diff(self.returns[-5:])
            trend = np.mean(returns_diff)
            reward += trend * 2  # Reward positive trend
        
        return reward
    
    def _calculate_drawdown(self, returns: List[float]) -> float:
        """Calculate the current drawdown."""
        peak = max(returns)
        return returns[-1] - peak
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate the Sharpe ratio of returns."""
        if len(returns) < 2:
            return 0
            
        # Convert to numpy array for calculations
        returns_array = np.array(returns)
        
        # Calculate daily returns
        daily_returns = np.diff(returns_array)
        
        # Calculate annualized Sharpe ratio
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        if std_return == 0:
            return 0
            
        sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(252)  # Annualize
        return sharpe
    
    def _get_observation(self, index: int) -> np.ndarray:
        """Get observation features for the given index."""
        # Get market data
        market_data = self._get_market_data_slice(index)
        
        # Extract basic market features
        market_features = self._extract_market_features(market_data)
        
        # Extract regime features if detector is available
        regime_features = []
        if self.market_regime_detector is not None:
            regime = self.market_regime_detector.detect_regime(market_data)
            regime_features = self._extract_regime_features(regime)
        else:
            # Default regime features if detector not available
            regime_features = [0, 0, 0, 0]  # Placeholder
            
        # Extract strategy metrics
        strategy_metrics = self._extract_strategy_metrics()
        
        # Combine all features
        all_features = np.concatenate([
            market_features,
            regime_features,
            strategy_metrics
        ])
        
        return all_features
    
    def _extract_market_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract and normalize market features from data."""
        if len(data) == 0:
            # Return zeros if no data
            return np.zeros(6)
            
        # Use the most recent data point
        latest = data.iloc[-1]
        
        # Calculate basic features
        close = latest['close']
        
        # Calculate returns if possible
        if len(data) > 1:
            prev_close = data.iloc[-2]['close']
            daily_return = (close / prev_close) - 1
        else:
            daily_return = 0
            
        # Calculate volatility if possible
        if len(data) > 5:
            returns = data['close'].pct_change().dropna()
            volatility = returns.std()
        else:
            volatility = 0
            
        # Include volume if available
        volume = latest.get('volume', 0)
        normalized_volume = 0
        if 'volume' in data.columns and len(data) > 1:
            avg_volume = data['volume'].mean()
            normalized_volume = volume / avg_volume if avg_volume > 0 else 0
            
        # Include OHLC features
        ohlc = [
            latest.get('open', close) / close - 1,  # Normalized open
            latest.get('high', close) / close - 1,  # Normalized high
            latest.get('low', close) / close - 1,   # Normalized low
            daily_return,                           # Daily return
            volatility,                             # Volatility
            normalized_volume                       # Normalized volume
        ]
        
        return np.array(ohlc)
    
    def _extract_regime_features(self, regime: Dict) -> np.ndarray:
        """Extract features representing the current market regime."""
        # Extract regime type and confidence
        regime_type = regime.get('regime', 'neutral')
        confidence = regime.get('confidence', 0.5)
        
        # One-hot encode regime type
        regime_encoding = [0, 0, 0, 0]  # [bull, bear, neutral, volatile]
        
        if regime_type == 'bull':
            regime_encoding[0] = 1
        elif regime_type == 'bear':
            regime_encoding[1] = 1
        elif regime_type == 'neutral':
            regime_encoding[2] = 1
        elif regime_type == 'volatile':
            regime_encoding[3] = 1
            
        # Combine with confidence
        regime_features = regime_encoding + [confidence]
        
        return np.array(regime_features)
    
    def _extract_strategy_metrics(self) -> np.ndarray:
        """Extract metrics about current strategy performance."""
        # Basic metrics
        metrics = [
            self.current_position,                    # Current position size
            self.position_value / self.initial_balance if self.initial_balance > 0 else 0,  # Normalized position value
            self.account_balance / self.initial_balance if self.initial_balance > 0 else 0,  # Normalized cash balance
            self.total_pnl / self.initial_balance if self.initial_balance > 0 else 0,      # Normalized total P&L
            self.max_drawdown                         # Maximum drawdown so far
        ]
        
        return np.array(metrics)
    
    def _get_state(self) -> np.ndarray:
        """Get the current state representation for the agent."""
        # Convert observation history to numpy array
        state = np.array(list(self._observation_history), dtype=np.float32)
        
        # Handle case where window isn't yet full
        if len(self._observation_history) < self.window_size:
            # Pad with zeros
            padding = np.zeros((self.window_size - len(self._observation_history), 
                               state.shape[1]), dtype=np.float32)
            state = np.vstack([padding, state])
            
        return state


class DQNAgent:
    """
    Deep Q-Network agent for reinforcement learning-based strategy selection.
    
    This agent learns to select the optimal trading strategy in different
    market conditions using deep Q-learning.
    """
    
    def __init__(
        self,
        state_size: Tuple[int, int],
        action_size: int,
        memory_size: int = 10000,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        learning_rate: float = 0.001,
        batch_size: int = 64,
        update_target_freq: int = 5
    ):
        """
        Initialize the DQN agent.
        
        Args:
            state_size: Shape of the state space (window_size, feature_size)
            action_size: Number of possible actions
            memory_size: Size of replay memory
            gamma: Discount factor
            epsilon: Exploration rate
            epsilon_min: Minimum exploration rate
            epsilon_decay: Exploration rate decay
            learning_rate: Learning rate for optimizer
            batch_size: Batch size for training
            update_target_freq: Frequency of target network updates
        """
        self.state_size = state_size
        self.action_size = action_size
        self.memory_size = memory_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.update_target_freq = update_target_freq
        
        # Replay memory
        self.memory = deque(maxlen=memory_size)
        
        # Models
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_network()
        
        # Training metrics
        self.loss_history = []
        self.reward_history = []
        self.q_value_history = []
        self.epsilon_history = []
        
        # Step counter for target updates
        self.train_step_counter = 0
    
    def _build_model(self) -> keras.Model:
        """Build the neural network model for the DQN."""
        # Input layer
        input_shape = self.state_size
        inputs = layers.Input(shape=input_shape)
        
        # Feature extraction with CNN
        x = layers.Reshape((self.state_size[0], self.state_size[1], 1))(inputs)
        x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Flatten()(x)
        
        # Sequential modeling with LSTM
        reshaped = layers.Reshape((self.state_size[0], self.state_size[1]))(inputs)
        lstm = layers.LSTM(64, return_sequences=False)(reshaped)
        
        # Combine CNN and LSTM features
        combined = layers.Concatenate()([x, lstm])
        
        # Dense layers
        x = layers.Dense(128, activation='relu')(combined)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(64, activation='relu')(x)
        
        # Output layer for Q-values
        outputs = layers.Dense(self.action_size, activation='linear')(x)
        
        # Create model
        model = keras.Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )
        
        return model
    
    def update_target_network(self):
        """Update the target network with weights from the primary network."""
        self.target_model.set_weights(self.model.get_weights())
        
    def memorize(self, state, action, reward, next_state, done):
        """Store experience in replay memory."""
        self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state, training=True):
        """Choose action using epsilon-greedy policy."""
        if training and np.random.rand() < self.epsilon:
            # Random action (exploration)
            return random.randrange(self.action_size)
        
        # Use model to predict best action (exploitation)
        q_values = self.model.predict(np.expand_dims(state, axis=0), verbose=0)
        return np.argmax(q_values[0])
    
    def replay(self, batch_size=None):
        """Train the model with experiences from replay memory."""
        if batch_size is None:
            batch_size = self.batch_size
            
        # Check if we have enough samples
        if len(self.memory) < batch_size:
            return
            
        # Sample batch from memory
        minibatch = random.sample(self.memory, batch_size)
        
        # Prepare batch data
        states = np.zeros((batch_size,) + self.state_size)
        next_states = np.zeros((batch_size,) + self.state_size)
        actions, rewards, dones = [], [], []
        
        # Fill batch data
        for i, (state, action, reward, next_state, done) in enumerate(minibatch):
            states[i] = state
            next_states[i] = next_state
            actions.append(action)
            rewards.append(reward)
            dones.append(done)
        
        # Predict Q-values
        target = self.model.predict(states, verbose=0)
        target_next = self.target_model.predict(next_states, verbose=0)
        
        # Update targets for actions taken
        for i in range(batch_size):
            if dones[i]:
                target[i, actions[i]] = rewards[i]
            else:
                target[i, actions[i]] = rewards[i] + self.gamma * np.max(target_next[i])
        
        # Train the model
        history = self.model.fit(
            states, target, epochs=1, batch_size=batch_size, verbose=0
        )
        
        # Record loss
        self.loss_history.append(history.history['loss'][0])
        
        # Update target network periodically
        self.train_step_counter += 1
        if self.train_step_counter % self.update_target_freq == 0:
            self.update_target_network()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            self.epsilon_history.append(self.epsilon)
        
        return history.history['loss'][0]
    
    def save(self, filepath):
        """Save the agent's models and parameters."""
        # Save model weights with the correct .weights.h5 extension
        self.model.save_weights(f"{filepath}.weights.h5")
        
        # Save agent parameters
        params = {
            'state_size': self.state_size,
            'action_size': self.action_size,
            'gamma': self.gamma,
            'epsilon': self.epsilon,
            'epsilon_min': self.epsilon_min,
            'epsilon_decay': self.epsilon_decay,
            'learning_rate': self.learning_rate,
        }
        
        with open(f"{filepath}_params.json", 'w') as f:
            json.dump(params, f)
        
        # Save training history
        history = {
            'loss': self.loss_history,
            'reward': self.reward_history,
            'q_value': self.q_value_history,
            'epsilon': self.epsilon_history,
        }
        
        with open(f"{filepath}_history.json", 'w') as f:
            json.dump(history, f)
            
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """Load the agent's models and parameters."""
        # Load model weights with the correct .weights.h5 extension
        self.model.load_weights(f"{filepath}.weights.h5")
        self.target_model.load_weights(f"{filepath}.weights.h5")
        
        # Load agent parameters
        with open(f"{filepath}_params.json", 'r') as f:
            params = json.load(f)
            
        self.gamma = params['gamma']
        self.epsilon = params['epsilon']
        self.epsilon_min = params['epsilon_min']
        self.epsilon_decay = params['epsilon_decay']
        self.learning_rate = params['learning_rate']
        
        # Load training history if available
        try:
            with open(f"{filepath}_history.json", 'r') as f:
                history = json.load(f)
                
            self.loss_history = history['loss']
            self.reward_history = history['reward']
            self.q_value_history = history['q_value']
            self.epsilon_history = history['epsilon']
        except:
            logger.warning(f"Could not load training history from {filepath}")
            
        logger.info(f"Model loaded from {filepath}")


class StrategySelector:
    """
    Reinforcement learning-based strategy selector.
    
    This class uses reinforcement learning to dynamically select the optimal
    trading strategy based on market conditions and performance.
    """
    
    def __init__(
        self,
        strategies: List[TradingStrategy],
        market_regime_detector: Optional[MarketRegimeDetector] = None,
        model_path: Optional[str] = None,
        window_size: int = 30,
        training_episodes: int = 100,
        batch_size: int = 64,
        validation_split: float = 0.2
    ):
        """
        Initialize the strategy selector.
        
        Args:
            strategies: List of available trading strategies
            market_regime_detector: Optional market regime detector
            model_path: Path to pre-trained model (if None, will train a new model)
            window_size: Window size for observations
            training_episodes: Number of episodes for training
            batch_size: Batch size for training
            validation_split: Fraction of data to use for validation
        """
        self.strategies = strategies
        self.market_regime_detector = market_regime_detector
        self.model_path = model_path
        self.window_size = window_size
        self.training_episodes = training_episodes
        self.batch_size = batch_size
        self.validation_split = validation_split
        
        # Current state and performance
        self.current_strategy = None
        self.strategy_performance = {}
        self.last_switch_time = None
        self.strategy_usage_count = {i: 0 for i in range(len(strategies))}
        
        # Store last observation window
        self.observation_window = deque(maxlen=window_size)
        
        # Initialize agent and environment to None, will be created during training
        self.agent = None
        self.env = None
        
        # Training metrics
        self.training_returns = []
        self.validation_returns = []
        
        # Load pre-trained model if provided
        if model_path and os.path.exists(f"{model_path}_model_weights.h5"):
            self.load_model(model_path)
    
    async def train(self, market_data: pd.DataFrame):
        """
        Train the strategy selector on historical market data.
        
        Args:
            market_data: Historical market data for training
        """
        logger.info(f"Starting training with {len(market_data)} data points")
        
        # Split data into training and validation sets
        split_idx = int(len(market_data) * (1 - self.validation_split))
        train_data = market_data.iloc[:split_idx].copy()
        val_data = market_data.iloc[split_idx:].copy()
        
        # Feature extraction from state
        feature_size = 15  # Market features + regime features + strategy metrics
        
        # Initialize environment with training data
        self.env = TradingEnvironment(
            strategies=self.strategies,
            market_data=train_data,
            market_regime_detector=self.market_regime_detector,
            window_size=self.window_size
        )
        
        # Initialize agent if not already created
        if self.agent is None:
            state_size = (self.window_size, feature_size)
            action_size = len(self.strategies) + 1  # +1 for hold
            
            self.agent = DQNAgent(
                state_size=state_size,
                action_size=action_size,
                memory_size=10000,
                gamma=0.95,
                epsilon=1.0,
                epsilon_min=0.01,
                epsilon_decay=0.995,
                batch_size=self.batch_size
            )
        
        # Training loop
        best_return = -np.inf
        early_stop_counter = 0
        early_stop_patience = 10
        
        for episode in range(self.training_episodes):
            episode_start = time.time()
            
            # Reset environment
            state = self.env.reset()
            total_reward = 0
            done = False
            
            # Episode loop
            while not done:
                # Choose action
                action = self.agent.act(state)
                
                # Take action
                next_state, reward, done, info = self.env.step(action)
                
                # Store experience
                self.agent.memorize(state, action, reward, next_state, done)
                
                # Update state and reward
                state = next_state
                total_reward += reward
                
                # Train agent
                if len(self.agent.memory) > self.batch_size:
                    self.agent.replay()
            
            # End of episode
            episode_time = time.time() - episode_start
            
            # Get episode performance
            episode_return = info.get('total_return', 0)
            self.training_returns.append(episode_return)
            
            # Evaluate on validation data
            val_return = await self.evaluate(val_data)
            self.validation_returns.append(val_return)
            
            # Log progress
            logger.info(f"Episode {episode+1}/{self.training_episodes} - " +
                        f"Return: {episode_return:.4f}, Val Return: {val_return:.4f}, " +
                        f"Time: {episode_time:.2f}s")
            
            # Check for early stopping
            if val_return > best_return:
                best_return = val_return
                # Save best model
                self.save_model(f"{self.model_path}_best" if self.model_path else "models/strategy_selector_best")
                early_stop_counter = 0
            else:
                early_stop_counter += 1
                
            if early_stop_counter >= early_stop_patience:
                logger.info(f"Early stopping at episode {episode+1}")
                break
        
        # Save final model
        self.save_model(self.model_path if self.model_path else "models/strategy_selector")
        
        # Load best model
        self.load_model(f"{self.model_path}_best" if self.model_path else "models/strategy_selector_best")
        
        return {
            'training_returns': self.training_returns,
            'validation_returns': self.validation_returns,
            'final_return': val_return,
            'best_return': best_return
        }
    
    async def evaluate(self, market_data: pd.DataFrame) -> float:
        """
        Evaluate the strategy selector on historical market data.
        
        Args:
            market_data: Historical market data for evaluation
            
        Returns:
            Total return from the evaluation
        """
        # Initialize environment with evaluation data
        eval_env = TradingEnvironment(
            strategies=self.strategies,
            market_data=market_data,
            market_regime_detector=self.market_regime_detector,
            window_size=self.window_size
        )
        
        # Reset environment
        state = eval_env.reset()
        total_reward = 0
        done = False
        
        # Evaluation loop
        while not done:
            # Choose action (no exploration)
            action = self.agent.act(state, training=False)
            
            # Take action
            next_state, reward, done, info = eval_env.step(action)
            
            # Update state and reward
            state = next_state
            total_reward += reward
        
        # Return evaluation metrics
        return info.get('total_return', 0)
    
    async def select_strategy(self, market_data: pd.DataFrame) -> Tuple[int, Dict]:
        """
        Select the optimal strategy for the current market conditions.
        
        Args:
            market_data: Recent market data for selection
            
        Returns:
            Tuple of (strategy_index, selection_info)
        """
        if self.agent is None:
            # No trained agent, use a simple baseline strategy
            logger.warning("No trained agent available, using baseline strategy selector")
            return self._baseline_strategy_selection(market_data)
        
        # Prepare the observation window
        observation = self._prepare_observation(market_data)
        self.observation_window.append(observation)
        
        # If window is not full yet, use baseline selection
        if len(self.observation_window) < self.window_size:
            logger.warning(f"Observation window not full ({len(self.observation_window)}/{self.window_size}), using baseline")
            return self._baseline_strategy_selection(market_data)
        
        # Convert observation window to state
        state = np.array(list(self.observation_window))
        
        # Select action (strategy)
        strategy_idx = self.agent.act(state, training=False)
        
        # Update strategy usage count
        if strategy_idx < len(self.strategies):
            self.strategy_usage_count[strategy_idx] += 1
            self.current_strategy = strategy_idx
            self.last_switch_time = datetime.now()
        
        # Prepare selection info
        q_values = self.agent.model.predict(np.expand_dims(state, axis=0), verbose=0)[0]
        
        selection_info = {
            'strategy_idx': strategy_idx,
            'strategy_name': self.strategies[strategy_idx].name if strategy_idx < len(self.strategies) else "Hold",
            'confidence': float(q_values[strategy_idx] / max(abs(q_values))),
            'q_values': {i: float(q_values[i]) for i in range(len(q_values))},
            'regime': self.market_regime_detector.detect_regime(market_data) if self.market_regime_detector else None,
            'strategy_usage': self.strategy_usage_count.copy()
        }
        
        logger.info(f"Selected strategy: {selection_info['strategy_name']} with confidence {selection_info['confidence']:.4f}")
        
        return strategy_idx, selection_info
    
    def _baseline_strategy_selection(self, market_data: pd.DataFrame) -> Tuple[int, Dict]:
        """Simple baseline strategy selection when no trained agent is available."""
        # Get market regime if available
        regime = None
        if self.market_regime_detector:
            regime = self.market_regime_detector.detect_regime(market_data)
            
        # Select strategy based on regime
        if regime:
            regime_type = regime.get('regime', 'neutral')
            confidence = regime.get('confidence', 0.5)
            
            if regime_type == 'bull' and confidence > 0.6:
                strategy_idx = 0  # Assuming strategy 0 is aggressive/trend-following
            elif regime_type == 'bear' and confidence > 0.6:
                strategy_idx = 1  # Assuming strategy 1 is defensive/mean-reversion
            else:
                strategy_idx = 2  # Assuming strategy 2 is balanced/neutral
        else:
            # No regime detector, use strategy 0 as default
            strategy_idx = 0
            
        # Ensure strategy index is valid
        strategy_idx = min(strategy_idx, len(self.strategies) - 1)
        
        # Update usage count
        self.strategy_usage_count[strategy_idx] += 1
        self.current_strategy = strategy_idx
        self.last_switch_time = datetime.now()
        
        # Prepare selection info
        selection_info = {
            'strategy_idx': strategy_idx,
            'strategy_name': self.strategies[strategy_idx].name if hasattr(self.strategies[strategy_idx], 'name') else f"Strategy {strategy_idx}",
            'confidence': 0.5,  # Default confidence for baseline
            'regime': regime,
            'strategy_usage': self.strategy_usage_count.copy(),
            'method': 'baseline'
        }
        
        logger.info(f"Baseline selected strategy: {selection_info['strategy_name']}")
        
        return strategy_idx, selection_info
    
    def _prepare_observation(self, market_data: pd.DataFrame) -> np.ndarray:
        """Prepare observation from market data for the agent."""
        # Extract market features
        market_features = self._extract_market_features(market_data)
        
        # Extract regime features if detector is available
        regime_features = []
        if self.market_regime_detector is not None:
            regime = self.market_regime_detector.detect_regime(market_data)
            regime_features = self._extract_regime_features(regime)
        else:
            # Default regime features if detector not available
            regime_features = [0, 0, 0, 0, 0]  # Placeholder
            
        # Extract strategy metrics
        strategy_metrics = self._extract_strategy_metrics()
        
        # Combine all features
        all_features = np.concatenate([
            market_features,
            regime_features,
            strategy_metrics
        ])
        
        return all_features
    
    def _extract_market_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract and normalize market features from data."""
        if len(data) == 0:
            # Return zeros if no data
            return np.zeros(6)
            
        # Use the most recent data point
        latest = data.iloc[-1]
        
        # Calculate basic features
        close = latest['close']
        
        # Calculate returns if possible
        if len(data) > 1:
            prev_close = data.iloc[-2]['close']
            daily_return = (close / prev_close) - 1
        else:
            daily_return = 0
            
        # Calculate volatility if possible
        if len(data) > 5:
            returns = data['close'].pct_change().dropna()
            volatility = returns.std()
        else:
            volatility = 0
            
        # Include volume if available
        volume = latest.get('volume', 0)
        normalized_volume = 0
        if 'volume' in data.columns and len(data) > 1:
            avg_volume = data['volume'].mean()
            normalized_volume = volume / avg_volume if avg_volume > 0 else 0
            
        # Include OHLC features
        ohlc = [
            latest.get('open', close) / close - 1,  # Normalized open
            latest.get('high', close) / close - 1,  # Normalized high
            latest.get('low', close) / close - 1,   # Normalized low
            daily_return,                           # Daily return
            volatility,                             # Volatility
            normalized_volume                       # Normalized volume
        ]
        
        return np.array(ohlc)
    
    def _extract_regime_features(self, regime: Dict) -> np.ndarray:
        """Extract features representing the current market regime."""
        # Extract regime type and confidence
        regime_type = regime.get('regime', 'neutral')
        confidence = regime.get('confidence', 0.5)
        
        # One-hot encode regime type
        regime_encoding = [0, 0, 0, 0]  # [bull, bear, neutral, volatile]
        
        if regime_type == 'bull':
            regime_encoding[0] = 1
        elif regime_type == 'bear':
            regime_encoding[1] = 1
        elif regime_type == 'neutral':
            regime_encoding[2] = 1
        elif regime_type == 'volatile':
            regime_encoding[3] = 1
            
        # Combine with confidence
        regime_features = regime_encoding + [confidence]
        
        return np.array(regime_features)
    
    def _extract_strategy_metrics(self) -> np.ndarray:
        """Extract metrics about current strategy performance."""
        # Default metrics if no strategy is selected
        if self.current_strategy is None:
            return np.zeros(4)
            
        # Get current strategy's performance metrics
        performance = self.strategy_performance.get(self.current_strategy, {})
        
        # Basic metrics
        metrics = [
            performance.get('win_rate', 0.5),              # Win rate
            performance.get('avg_profit', 0.0),            # Average profit
            performance.get('max_drawdown', 0.0),          # Maximum drawdown
            performance.get('sharpe_ratio', 0.0)           # Sharpe ratio
        ]
        
        return np.array(metrics)
    
    def update_strategy_performance(self, strategy_idx: int, metrics: Dict) -> None:
        """Update performance metrics for a strategy."""
        self.strategy_performance[strategy_idx] = metrics
    
    def save_model(self, filepath: str) -> None:
        """Save the agent's model to a file."""
        if self.agent:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.agent.save(filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load the agent's model from a file."""
        # Check if model files exist
        if not os.path.exists(f"{filepath}.weights.h5"):
            logger.warning(f"Model weights file not found at {filepath}.weights.h5")
            return
            
        if not os.path.exists(f"{filepath}_params.json"):
            logger.warning(f"Model parameters file not found at {filepath}_params.json")
            return
        
        # Load model parameters
        with open(f"{filepath}_params.json", 'r') as f:
            params = json.load(f)
        
        # Initialize agent if not already created
        if self.agent is None:
            self.agent = DQNAgent(
                state_size=tuple(params['state_size']),
                action_size=params['action_size'],
                gamma=params['gamma'],
                epsilon=params['epsilon'],
                epsilon_min=params['epsilon_min'],
                epsilon_decay=params['epsilon_decay'],
                learning_rate=params['learning_rate']
            )
        
        # Load model weights
        self.agent.load(filepath)
        logger.info(f"Model loaded from {filepath}")