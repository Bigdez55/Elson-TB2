"""
Reinforcement Learning Module for Trading

Provides RL-based trading agents for strategy selection and optimization.
Supports DQN, PPO, and other RL algorithms with TensorFlow/Gymnasium.
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from collections import deque
import random
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# Check availability
GYMNASIUM_AVAILABLE = False
TENSORFLOW_AVAILABLE = False

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
    logger.info("Gymnasium available for RL")
except ImportError:
    logger.info("Gymnasium not available")

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers
    TENSORFLOW_AVAILABLE = True
    logger.info(f"TensorFlow {tf.__version__} available for RL")
except ImportError:
    logger.info("TensorFlow not available for RL")


@dataclass
class TradingAction:
    """Represents a trading action"""
    action_type: str  # "buy", "sell", "hold"
    confidence: float
    position_size: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class TradingState:
    """Represents the current trading state"""
    position: float
    balance: float
    unrealized_pnl: float
    market_features: np.ndarray


class SimpleTradingEnvironment:
    """
    Simple trading environment that works without Gymnasium.

    This is a fallback implementation for environments where
    Gymnasium is not available.
    """

    def __init__(
        self,
        market_data: pd.DataFrame,
        initial_balance: float = 10000.0,
        transaction_cost: float = 0.001,
        window_size: int = 30
    ):
        self.market_data = market_data
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.window_size = window_size

        # State variables
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0
        self.position_price = 0
        self.done = False

        # Feature columns
        self.feature_columns = [
            col for col in market_data.columns
            if col not in ['date', 'datetime', 'timestamp']
        ]
        self.n_features = len(self.feature_columns)

        # Action space: 0=hold, 1=buy, 2=sell
        self.n_actions = 3

        # State space dimensions
        self.state_shape = (window_size, self.n_features + 3)  # +3 for position info

    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.position = 0
        self.position_price = 0
        self.done = False
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Take an action and return new state, reward, done, info"""
        if self.done:
            return self._get_state(), 0, True, {}

        current_price = self.market_data['close'].iloc[self.current_step]
        prev_total = self.balance + self.position * current_price

        # Execute action
        if action == 1:  # Buy
            if self.position <= 0:  # Can buy if not long
                position_value = self.balance * 0.95  # Use 95% of balance
                cost = position_value * self.transaction_cost
                self.position = position_value / current_price
                self.position_price = current_price
                self.balance -= (position_value + cost)

        elif action == 2:  # Sell
            if self.position > 0:  # Can sell if long
                sale_value = self.position * current_price
                cost = sale_value * self.transaction_cost
                self.balance += (sale_value - cost)
                self.position = 0
                self.position_price = 0

        # Move to next step
        self.current_step += 1

        # Check if done
        if self.current_step >= len(self.market_data) - 1:
            self.done = True

        # Calculate reward
        new_price = self.market_data['close'].iloc[self.current_step]
        new_total = self.balance + self.position * new_price
        reward = (new_total - prev_total) / self.initial_balance

        # Additional reward shaping
        if self.balance <= 0:
            reward -= 1.0
            self.done = True

        info = {
            'balance': self.balance,
            'position': self.position,
            'total_value': new_total,
            'step': self.current_step
        }

        return self._get_state(), reward, self.done, info

    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        start = max(0, self.current_step - self.window_size)
        end = self.current_step

        # Get market features
        market_features = self.market_data[self.feature_columns].iloc[start:end].values

        # Pad if necessary
        if len(market_features) < self.window_size:
            padding = np.zeros((self.window_size - len(market_features), self.n_features))
            market_features = np.vstack([padding, market_features])

        # Normalize
        market_features = (market_features - np.mean(market_features, axis=0)) / (
            np.std(market_features, axis=0) + 1e-8
        )

        # Add position info
        current_price = self.market_data['close'].iloc[self.current_step]
        position_features = np.array([
            [self.position / 100,  # Normalized position
             self.balance / self.initial_balance,  # Normalized balance
             (self.position * current_price) / self.initial_balance]  # Normalized position value
        ] * self.window_size)

        state = np.concatenate([market_features, position_features], axis=1)
        return state.astype(np.float32)


class DQNAgent:
    """
    Deep Q-Network agent for trading.

    Works with TensorFlow when available, otherwise provides
    a simple heuristic-based fallback.
    """

    def __init__(
        self,
        state_shape: Tuple[int, int],
        n_actions: int,
        learning_rate: float = 0.001,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        memory_size: int = 10000,
        batch_size: int = 64
    ):
        self.state_shape = state_shape
        self.n_actions = n_actions
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size

        # Replay memory
        self.memory = deque(maxlen=memory_size)

        # Build model if TensorFlow available
        self.model = None
        self.target_model = None

        if TENSORFLOW_AVAILABLE:
            self.model = self._build_model()
            self.target_model = self._build_model()
            self.update_target_model()
            logger.info("DQN agent initialized with TensorFlow")
        else:
            logger.warning("DQN agent using heuristic fallback (no TensorFlow)")

    def _build_model(self) -> keras.Model:
        """Build the neural network model"""
        inputs = layers.Input(shape=self.state_shape)

        # CNN for spatial features
        x = layers.Reshape((self.state_shape[0], self.state_shape[1], 1))(inputs)
        x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.Flatten()(x)

        # LSTM for temporal features
        lstm_input = layers.Reshape((self.state_shape[0], self.state_shape[1]))(inputs)
        lstm = layers.LSTM(64)(lstm_input)

        # Combine
        combined = layers.Concatenate()([x, lstm])

        # Dense layers
        x = layers.Dense(128, activation='relu')(combined)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(64, activation='relu')(x)

        # Output
        outputs = layers.Dense(self.n_actions, activation='linear')(x)

        model = keras.Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )

        return model

    def update_target_model(self):
        """Update target model weights"""
        if self.target_model is not None:
            self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        """Store experience in memory"""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state: np.ndarray, training: bool = True) -> int:
        """Choose action using epsilon-greedy policy"""
        if training and random.random() < self.epsilon:
            return random.randrange(self.n_actions)

        if self.model is not None:
            q_values = self.model.predict(np.expand_dims(state, 0), verbose=0)
            return np.argmax(q_values[0])
        else:
            # Heuristic fallback
            return self._heuristic_action(state)

    def _heuristic_action(self, state: np.ndarray) -> int:
        """Simple heuristic for action selection"""
        # Use recent price trend
        recent_prices = state[-5:, 0]  # Assuming first column is close price
        trend = np.mean(np.diff(recent_prices))

        if trend > 0.01:
            return 1  # Buy
        elif trend < -0.01:
            return 2  # Sell
        else:
            return 0  # Hold

    def replay(self) -> Optional[float]:
        """Train on batch from memory"""
        if self.model is None:
            return None

        if len(self.memory) < self.batch_size:
            return None

        batch = random.sample(self.memory, self.batch_size)

        states = np.array([exp[0] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])

        # Predict Q-values
        current_q = self.model.predict(states, verbose=0)
        next_q = self.target_model.predict(next_states, verbose=0)

        # Update Q-values
        for i, (state, action, reward, next_state, done) in enumerate(batch):
            if done:
                current_q[i, action] = reward
            else:
                current_q[i, action] = reward + self.gamma * np.max(next_q[i])

        # Train
        history = self.model.fit(states, current_q, epochs=1, verbose=0)
        loss = history.history['loss'][0]

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return loss

    def save(self, filepath: str):
        """Save agent"""
        if self.model is not None:
            self.model.save_weights(f"{filepath}_model.weights.h5")

        params = {
            'state_shape': self.state_shape,
            'n_actions': self.n_actions,
            'epsilon': self.epsilon,
            'gamma': self.gamma
        }
        with open(f"{filepath}_params.json", 'w') as f:
            json.dump(params, f)

    def load(self, filepath: str):
        """Load agent"""
        if self.model is not None and os.path.exists(f"{filepath}_model.weights.h5"):
            self.model.load_weights(f"{filepath}_model.weights.h5")
            self.update_target_model()

        if os.path.exists(f"{filepath}_params.json"):
            with open(f"{filepath}_params.json", 'r') as f:
                params = json.load(f)
            self.epsilon = params.get('epsilon', self.epsilon)


class RLTradingService:
    """
    Reinforcement Learning Trading Service.

    Provides training and inference for RL-based trading strategies.
    """

    def __init__(self, model_dir: str = "models/rl"):
        self.model_dir = model_dir
        self.agents: Dict[str, DQNAgent] = {}
        self.environments: Dict[str, SimpleTradingEnvironment] = {}

        os.makedirs(model_dir, exist_ok=True)

    async def train_agent(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        episodes: int = 100,
        batch_size: int = 64,
        save_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Train a DQN agent for a symbol.

        Args:
            symbol: Trading symbol
            market_data: Historical market data
            episodes: Number of training episodes
            batch_size: Batch size for training
            save_interval: Save model every N episodes

        Returns:
            Training results
        """
        try:
            # Create environment
            env = SimpleTradingEnvironment(market_data)
            self.environments[symbol] = env

            # Create agent
            agent = DQNAgent(
                state_shape=env.state_shape,
                n_actions=env.n_actions,
                batch_size=batch_size
            )
            self.agents[symbol] = agent

            # Training metrics
            episode_rewards = []
            episode_values = []
            losses = []

            # Training loop
            for episode in range(episodes):
                state = env.reset()
                total_reward = 0
                done = False

                while not done:
                    action = agent.act(state)
                    next_state, reward, done, info = env.step(action)

                    agent.remember(state, action, reward, next_state, done)
                    state = next_state
                    total_reward += reward

                    # Train
                    loss = agent.replay()
                    if loss is not None:
                        losses.append(loss)

                # Update target network
                if episode % 5 == 0:
                    agent.update_target_model()

                episode_rewards.append(total_reward)
                episode_values.append(info.get('total_value', 0))

                # Save periodically
                if episode % save_interval == 0:
                    self._save_agent(symbol, agent)

                if episode % 10 == 0:
                    logger.info(
                        f"Episode {episode}/{episodes} - "
                        f"Reward: {total_reward:.4f}, "
                        f"Value: {info.get('total_value', 0):.2f}, "
                        f"Epsilon: {agent.epsilon:.4f}"
                    )

            # Save final model
            self._save_agent(symbol, agent)

            return {
                "success": True,
                "symbol": symbol,
                "episodes": episodes,
                "final_value": episode_values[-1] if episode_values else 0,
                "mean_reward": float(np.mean(episode_rewards)),
                "mean_loss": float(np.mean(losses)) if losses else None,
                "final_epsilon": agent.epsilon
            }

        except Exception as e:
            logger.error(f"Error training RL agent for {symbol}: {e}")
            return {"success": False, "error": str(e)}

    async def get_action(
        self,
        symbol: str,
        current_state: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Get trading action from trained agent.

        Args:
            symbol: Trading symbol
            current_state: Current market state

        Returns:
            Recommended action
        """
        try:
            if symbol not in self.agents:
                # Try to load
                loaded = self._load_agent(symbol)
                if not loaded:
                    return {
                        "success": False,
                        "error": f"No trained agent for {symbol}"
                    }

            agent = self.agents[symbol]

            # Prepare state
            if symbol in self.environments:
                env = self.environments[symbol]
            else:
                env = SimpleTradingEnvironment(current_state)
                self.environments[symbol] = env

            state = env._get_state()
            action = agent.act(state, training=False)

            action_map = {0: "hold", 1: "buy", 2: "sell"}

            # Get Q-values for confidence
            if agent.model is not None:
                q_values = agent.model.predict(np.expand_dims(state, 0), verbose=0)[0]
                confidence = float(np.max(q_values) / (np.sum(np.abs(q_values)) + 1e-8))
            else:
                confidence = 0.5

            return {
                "success": True,
                "action": action_map[action],
                "action_code": action,
                "confidence": confidence,
                "symbol": symbol
            }

        except Exception as e:
            logger.error(f"Error getting action for {symbol}: {e}")
            return {"success": False, "error": str(e)}

    def _save_agent(self, symbol: str, agent: DQNAgent):
        """Save agent to disk"""
        filepath = os.path.join(self.model_dir, symbol)
        agent.save(filepath)
        logger.info(f"Saved agent for {symbol}")

    def _load_agent(self, symbol: str) -> bool:
        """Load agent from disk"""
        filepath = os.path.join(self.model_dir, symbol)
        if not os.path.exists(f"{filepath}_params.json"):
            return False

        with open(f"{filepath}_params.json", 'r') as f:
            params = json.load(f)

        agent = DQNAgent(
            state_shape=tuple(params['state_shape']),
            n_actions=params['n_actions']
        )
        agent.load(filepath)
        self.agents[symbol] = agent
        logger.info(f"Loaded agent for {symbol}")
        return True

    def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            "tensorflow_available": TENSORFLOW_AVAILABLE,
            "gymnasium_available": GYMNASIUM_AVAILABLE,
            "loaded_agents": list(self.agents.keys()),
            "model_dir": self.model_dir
        }


# Convenience function
def get_rl_service(model_dir: str = "models/rl") -> RLTradingService:
    """Get an instance of the RL trading service"""
    return RLTradingService(model_dir=model_dir)
