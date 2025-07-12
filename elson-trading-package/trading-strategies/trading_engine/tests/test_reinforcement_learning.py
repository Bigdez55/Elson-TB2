import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import tensorflow as tf
import gymnasium as gym
import os
import tempfile
import json

# Set environment variable to avoid GPU errors in tests
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Import the module with relative import
import sys
sys.path.append('/workspaces/Elson/Elson')  # Add the project root to path
from trading_engine.ai_model_engine.reinforcement_learning import (
    TradingEnvironment, DQNAgent, StrategySelector
)
from trading_engine.strategies.base import TradingStrategy


class MockStrategy(MagicMock):
    """Mock strategy for testing."""
    
    async def generate_signals(self, data):
        # Return a simple mock signal
        return {
            'action': 'buy',
            'confidence': 0.8,
            'price': 100.0,
            'stop_loss': 95.0,
            'take_profit': 110.0
        }


class TestTradingEnvironment(unittest.TestCase):
    """Test the TradingEnvironment class."""
    
    def setUp(self):
        # Create mock strategies
        self.strategies = [
            MockStrategy(name="Strategy 1"),
            MockStrategy(name="Strategy 2"),
            MockStrategy(name="Strategy 3")
        ]
        
        # Create sample market data
        dates = pd.date_range(start='2023-01-01', periods=100)
        self.market_data = pd.DataFrame({
            'open': np.random.normal(100, 5, 100),
            'high': np.random.normal(105, 5, 100),
            'low': np.random.normal(95, 5, 100),
            'close': np.random.normal(100, 5, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Create mock market regime detector
        self.market_regime_detector = MagicMock()
        self.market_regime_detector.detect_regime.return_value = {
            'regime': 'neutral',
            'confidence': 0.7
        }
        
        # Create the environment
        self.env = TradingEnvironment(
            strategies=self.strategies,
            market_data=self.market_data,
            market_regime_detector=self.market_regime_detector,
            window_size=10,
            max_steps=50
        )
    
    def test_reset(self):
        """Test environment reset."""
        # Reset the environment
        state = self.env.reset()
        
        # Check state shape
        expected_shape = (10, 16)  # window_size x feature_size
        self.assertEqual(state.shape, expected_shape)
        
        # Check initial values
        self.assertEqual(self.env.current_step, 0)
        self.assertEqual(self.env.account_balance, self.env.initial_balance)
        self.assertEqual(self.env.current_position, 0)
        self.assertEqual(self.env.current_strategy_idx, None)
    
    def test_step_hold(self):
        """Test taking a hold action."""
        # Reset the environment
        self.env.reset()
        
        # Take a hold action (index = len(strategies))
        action = len(self.strategies)
        next_state, reward, done, info = self.env.step(action)
        
        # Check state and info
        self.assertEqual(next_state.shape, (10, 16))
        self.assertEqual(self.env.current_step, 1)
        self.assertFalse(done)
        
        # Check that position remains unchanged
        self.assertEqual(self.env.current_position, 0)
    
    def test_step_select_strategy(self):
        """Test selecting a strategy."""
        # Reset the environment
        self.env.reset()
        
        # Take action to select first strategy
        action = 0
        next_state, reward, done, info = self.env.step(action)
        
        # Check that strategy was selected
        self.assertEqual(self.env.current_strategy_idx, 0)
        self.assertEqual(self.env.strategy_usage[0], 1)
        
        # Ensure buy signal was executed
        self.assertGreater(self.env.current_position, 0)


class TestDQNAgent(unittest.TestCase):
    """Test the DQNAgent class."""
    
    def setUp(self):
        # Define state and action sizes
        self.state_size = (10, 15)
        self.action_size = 4
        
        # Create the agent
        self.agent = DQNAgent(
            state_size=self.state_size,
            action_size=self.action_size,
            memory_size=1000,
            batch_size=32
        )
    
    def test_initialization(self):
        """Test agent initialization."""
        # Check model structure
        self.assertIsNotNone(self.agent.model)
        self.assertIsNotNone(self.agent.target_model)
        
        # Check memory
        self.assertEqual(len(self.agent.memory), 0)
        self.assertEqual(self.agent.memory.maxlen, 1000)
    
    def test_act_exploration(self):
        """Test agent's exploration behavior."""
        # Force exploration
        self.agent.epsilon = 1.0
        
        # Create a random state
        state = np.random.random(self.state_size)
        
        # With random seed and exploration set to 1.0, actions should be random
        actions = [self.agent.act(state) for _ in range(40)]
        
        # Check that we have some variety in actions (statistical test)
        unique_actions = len(set(actions))
        self.assertGreater(unique_actions, 1)
    
    def test_act_exploitation(self):
        """Test agent's exploitation behavior."""
        # Force exploitation
        self.agent.epsilon = 0.0
        
        # Create a random state
        state = np.random.random(self.state_size)
        
        # Get the action
        action = self.agent.act(state)
        
        # Should be a valid action
        self.assertGreaterEqual(action, 0)
        self.assertLess(action, self.action_size)
    
    def test_replay(self):
        """Test agent's replay method."""
        # Fill memory with some experiences
        for _ in range(50):
            state = np.random.random(self.state_size)
            action = np.random.randint(0, self.action_size)
            reward = np.random.random()
            next_state = np.random.random(self.state_size)
            done = bool(np.random.randint(0, 2))
            
            self.agent.memorize(state, action, reward, next_state, done)
        
        # Check memory size
        self.assertEqual(len(self.agent.memory), 50)
        
        # Perform replay
        loss = self.agent.replay(batch_size=32)
        
        # Check that loss is returned
        self.assertIsNotNone(loss)
    
    def test_save_load(self):
        """Test model saving and loading."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_model")
            
            # Save the model
            self.agent.save(model_path)
            
            # Check that files were created
            self.assertTrue(os.path.exists(f"{model_path}.weights.h5"))
            self.assertTrue(os.path.exists(f"{model_path}_params.json"))
            
            # Create a new agent
            new_agent = DQNAgent(
                state_size=self.state_size,
                action_size=self.action_size
            )
            
            # Load the saved model
            new_agent.load(model_path)
            
            # Check that parameters were loaded
            self.assertEqual(new_agent.gamma, self.agent.gamma)
            self.assertEqual(new_agent.epsilon, self.agent.epsilon)


class TestStrategySelector(unittest.TestCase):
    """Test the StrategySelector class."""
    
    def setUp(self):
        # Create mock strategies
        self.strategies = [
            MockStrategy(name="Strategy 1"),
            MockStrategy(name="Strategy 2"),
            MockStrategy(name="Strategy 3")
        ]
        
        # Create mock market regime detector
        self.market_regime_detector = MagicMock()
        self.market_regime_detector.detect_regime.return_value = {
            'regime': 'bull',
            'confidence': 0.8
        }
        
        # Create sample market data
        dates = pd.date_range(start='2023-01-01', periods=100)
        self.market_data = pd.DataFrame({
            'open': np.random.normal(100, 5, 100),
            'high': np.random.normal(105, 5, 100),
            'low': np.random.normal(95, 5, 100),
            'close': np.random.normal(100, 5, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Create the strategy selector
        self.selector = StrategySelector(
            strategies=self.strategies,
            market_regime_detector=self.market_regime_detector,
            window_size=10,
            training_episodes=2  # Small number for testing
        )
    
    @patch('tensorflow.keras.Model.predict')
    async def test_select_strategy_baseline(self, mock_predict):
        """Test strategy selection using baseline (without trained agent)."""
        # Ensure no agent is available
        self.selector.agent = None
        
        # Select a strategy
        strategy_idx, info = await self.selector.select_strategy(self.market_data)
        
        # Check the result
        self.assertIsInstance(strategy_idx, int)
        self.assertGreaterEqual(strategy_idx, 0)
        self.assertLess(strategy_idx, len(self.strategies))
        
        # Check that info contains expected fields
        self.assertIn('strategy_idx', info)
        self.assertIn('strategy_name', info)
        self.assertIn('method', info)
        self.assertEqual(info['method'], 'baseline')
    
    @patch('tensorflow.keras.Model.predict')
    @patch('tensorflow.keras.Model.fit')
    async def test_select_strategy_with_agent(self, mock_fit, mock_predict):
        """Test strategy selection using a trained agent."""
        # Mock the agent's predict method
        mock_predict.return_value = np.array([[0.2, 0.8, 0.1, 0.3]])
        
        # Create a simple agent
        self.selector.agent = DQNAgent(
            state_size=(10, 15),
            action_size=len(self.strategies) + 1
        )
        
        # Select a strategy
        strategy_idx, info = await self.selector.select_strategy(self.market_data)
        
        # Based on our mock predict values, it should choose index 1 (highest Q-value)
        self.assertEqual(strategy_idx, 1)
        
        # Check that info contains expected fields
        self.assertIn('strategy_idx', info)
        self.assertIn('strategy_name', info)
        self.assertIn('confidence', info)
        self.assertIn('q_values', info)
    
    @unittest.skip("Skip full training test as it's time-consuming")
    async def test_train(self):
        """Test the training process (optional, can be time-consuming)."""
        # Train the selector (reduced settings for testing)
        result = await self.selector.train(self.market_data)
        
        # Check that training produced results
        self.assertIn('training_returns', result)
        self.assertIn('validation_returns', result)
        self.assertIn('best_return', result)
        
        # Agent should be created
        self.assertIsNotNone(self.selector.agent)


if __name__ == '__main__':
    unittest.main()