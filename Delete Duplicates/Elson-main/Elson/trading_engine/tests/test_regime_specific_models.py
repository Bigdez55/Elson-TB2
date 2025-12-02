#!/usr/bin/env python3
"""
Unit tests for the regime-specific models component.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

from Elson.trading_engine.volatility_regime.regime_specific_models import (
    RegimeSpecificModelSelector
)
from Elson.trading_engine.volatility_regime.volatility_detector import VolatilityRegime
from Elson.trading_engine.ai_model_engine.hybrid_models import HybridMachineLearningModel


class TestRegimeSpecificModels(unittest.TestCase):
    """Test cases for regime-specific model selection and training."""

    def setUp(self):
        """Set up test environment."""
        self.model_selector = RegimeSpecificModelSelector(enable_smooth_transitions=True)
        
        # Create a mock HybridMachineLearningModel
        self.mock_model = MagicMock(spec=HybridMachineLearningModel)
        self.mock_model.lookback_periods = 20
        self.mock_model.prediction_horizon = 3
        self.mock_model.ensemble_params = {
            'voting': 'soft',
            'threshold': 0.6,
            'weights': {
                'random_forest': 1.0,
                'gradient_boosting': 1.0,
                'neural_network': 1.0,
                'quantum_kernel': 1.0,
                'quantum_variational': 1.0
            }
        }
        
        # Mock the train method
        self.mock_model.train = MagicMock(return_value=None)
        
        # Create synthetic test data
        self.test_data = pd.DataFrame({
            'volatility_regime': ['low'] * 25 + ['normal'] * 25 + ['high'] * 25 + ['extreme'] * 25,
            'returns': np.random.normal(0, 0.01, 100),
            'feature1': np.random.random(100),
            'feature2': np.random.random(100),
            'feature3': np.random.random(100),
            'label': np.random.choice([0, 1], size=100)
        })

    @patch('Elson.trading_engine.volatility_regime.regime_specific_models.HybridMachineLearningModel')
    def test_initialize_models(self, mock_hybrid_model_class):
        """Test initialization of regime-specific models."""
        # Configure the mock to return our mock model
        mock_hybrid_model_class.return_value = self.mock_model
        
        # Initialize models
        self.model_selector.initialize_models()
        
        # Verify that models were created for each regime
        self.assertEqual(len(self.model_selector.models), 4)
        for regime in VolatilityRegime:
            self.assertIn(regime, self.model_selector.models)
            
        # Check that normal regime is set as default
        self.assertIsNotNone(self.model_selector.default_model)
        
        # Verify model configurations
        high_vol_model = self.model_selector.models.get(VolatilityRegime.HIGH)
        self.assertIsNotNone(high_vol_model)
        
        extreme_vol_model = self.model_selector.models.get(VolatilityRegime.EXTREME)
        self.assertIsNotNone(extreme_vol_model)

    def test_get_regime_config(self):
        """Test getting configuration for specific regimes."""
        base_config = {
            'feature_engineering_params': {'add_technical_indicators': True}
        }
        
        # Test different regime configurations
        for regime in VolatilityRegime:
            config = self.model_selector._get_regime_config(regime, base_config)
            
            # Should include the base config
            self.assertIn('feature_engineering_params', config)
            self.assertTrue(config['feature_engineering_params']['add_technical_indicators'])
            
            # Should have regime-specific parameters
            self.assertIn('lookback_periods', config)
            self.assertIn('prediction_horizon', config)
            self.assertIn('ensemble_params', config)
            
            # Ensemble parameters should have weights
            self.assertIn('weights', config['ensemble_params'])
            
        # Specific checks for high volatility
        high_config = self.model_selector._get_regime_config(VolatilityRegime.HIGH, base_config)
        self.assertEqual(high_config['lookback_periods'], 8)
        self.assertEqual(high_config['prediction_horizon'], 1)
        self.assertAlmostEqual(high_config['ensemble_params']['threshold'], 0.82)
        
        # Specific checks for extreme volatility
        extreme_config = self.model_selector._get_regime_config(VolatilityRegime.EXTREME, base_config)
        self.assertEqual(extreme_config['lookback_periods'], 5)
        self.assertEqual(extreme_config['prediction_horizon'], 1)
        self.assertAlmostEqual(extreme_config['ensemble_params']['threshold'], 0.90)
        
        # Check model weights for extreme regime
        extreme_weights = extreme_config['ensemble_params']['weights']
        self.assertGreater(extreme_weights['random_forest'], extreme_weights['neural_network'])
        self.assertGreater(extreme_weights['gradient_boosting'], extreme_weights['quantum_variational'])

    @patch('Elson.trading_engine.volatility_regime.regime_specific_models.HybridMachineLearningModel')
    def test_train_regime_specific_models(self, mock_hybrid_model_class):
        """Test training regime-specific models."""
        # Configure the mock to return our mock model
        mock_hybrid_model_class.return_value = self.mock_model
        
        # Initialize models
        self.model_selector.initialize_models()
        
        # Train models
        self.model_selector.train_regime_specific_models(self.test_data)
        
        # Verify that trained models were created
        self.assertTrue(hasattr(self.model_selector, 'trained_models'))
        
        # Since our test data has all regimes, we should have trained models for each
        expected_regimes = {VolatilityRegime.LOW, VolatilityRegime.NORMAL, 
                           VolatilityRegime.HIGH, VolatilityRegime.EXTREME}
        
        # Check if the mock's train method was called
        self.mock_model.train.assert_called()

    @patch('Elson.trading_engine.volatility_regime.regime_specific_models.HybridMachineLearningModel')
    def test_get_model_for_regime(self, mock_hybrid_model_class):
        """Test getting appropriate model for a regime."""
        # Configure the mock to return our mock model
        mock_hybrid_model_class.return_value = self.mock_model
        
        # Initialize models
        self.model_selector.initialize_models()
        
        # Simple case: get model for a regime when no previous regime
        model = self.model_selector.get_model_for_regime(VolatilityRegime.NORMAL)
        self.assertEqual(model, self.mock_model)
        
        # Check current regime is tracked
        self.assertEqual(self.model_selector.current_regime, VolatilityRegime.NORMAL)
        
        # Test getting model for different regime (should trigger transition)
        model = self.model_selector.get_model_for_regime(VolatilityRegime.HIGH)
        self.assertEqual(model, self.mock_model)  # In our test setup, all models are the same mock
        
        # Check transition state
        self.assertTrue(self.model_selector.transition_state['in_transition'])
        self.assertEqual(self.model_selector.transition_state['from_regime'], VolatilityRegime.NORMAL)
        self.assertEqual(self.model_selector.transition_state['to_regime'], VolatilityRegime.HIGH)
        
        # Check previous and current regime are tracked
        self.assertEqual(self.model_selector.previous_regime, VolatilityRegime.NORMAL)
        self.assertEqual(self.model_selector.current_regime, VolatilityRegime.HIGH)

    @patch('Elson.trading_engine.volatility_regime.regime_specific_models.HybridMachineLearningModel')
    def test_regime_transition(self, mock_hybrid_model_class):
        """Test transition between regimes."""
        # Configure the mock to return our mock model
        mock_hybrid_model_class.return_value = self.mock_model
        
        # Initialize models
        self.model_selector.initialize_models()
        
        # Get model for initial regime
        self.model_selector.get_model_for_regime(VolatilityRegime.NORMAL)
        
        # Start transition
        transition_model = self.model_selector._handle_regime_transition(
            VolatilityRegime.NORMAL, VolatilityRegime.HIGH
        )
        
        # Verify transition state
        self.assertTrue(self.model_selector.transition_state['in_transition'])
        self.assertEqual(self.model_selector.transition_state['from_regime'], VolatilityRegime.NORMAL)
        self.assertEqual(self.model_selector.transition_state['to_regime'], VolatilityRegime.HIGH)
        self.assertGreaterEqual(self.model_selector.transition_state['transition_progress'], 0.0)
        
        # Update transition progress
        old_progress = self.model_selector.transition_state['transition_progress']
        self.model_selector.transition_state['transition_progress'] += self.model_selector.transition_state['transition_speed']
        
        # Continue transition
        transition_model = self.model_selector._handle_regime_transition(
            VolatilityRegime.NORMAL, VolatilityRegime.HIGH
        )
        
        # Verify progress increased
        self.assertGreater(self.model_selector.transition_state['transition_progress'], old_progress)
        
        # Complete transition
        self.model_selector.transition_state['transition_progress'] = 1.0
        transition_model = self.model_selector._handle_regime_transition(
            VolatilityRegime.NORMAL, VolatilityRegime.HIGH
        )
        
        # Verify transition completed
        self.assertFalse(self.model_selector.transition_state['in_transition'])

    def test_update_regime_performance(self):
        """Test updating performance metrics by regime."""
        # Initialize performance tracking
        for regime in VolatilityRegime:
            self.assertIn(regime, self.model_selector.regime_performance)
            self.assertEqual(self.model_selector.regime_performance[regime]['win_rate'], 0.0)
            self.assertEqual(self.model_selector.regime_performance[regime]['samples'], 0)
        
        # Update with some test data
        predictions = [True, False, True, True, False]
        actual = [True, False, False, True, True]
        
        self.model_selector.update_regime_performance(VolatilityRegime.HIGH, predictions, actual)
        
        # Verify performance was updated
        self.assertEqual(self.model_selector.regime_performance[VolatilityRegime.HIGH]['samples'], 5)
        self.assertEqual(self.model_selector.regime_performance[VolatilityRegime.HIGH]['win_rate'], 0.6)
        
        # Update with more data
        predictions2 = [True, True, True, False, False]
        actual2 = [True, True, False, False, True]
        
        self.model_selector.update_regime_performance(VolatilityRegime.HIGH, predictions2, actual2)
        
        # Verify performance was updated with weighted average
        self.assertEqual(self.model_selector.regime_performance[VolatilityRegime.HIGH]['samples'], 10)
        # Expected: (0.6*5 + 0.6*5) / 10 = 0.6
        self.assertEqual(self.model_selector.regime_performance[VolatilityRegime.HIGH]['win_rate'], 0.6)

    def test_create_blended_model(self):
        """Test creating a blended model during transitions."""
        # Create two test models with different parameters
        from_model = MagicMock(spec=HybridMachineLearningModel)
        from_model.lookback_periods = 30
        from_model.prediction_horizon = 5
        from_model.ensemble_params = {
            'threshold': 0.55,
            'position_sizing_factor': 1.0,
            'weights': {
                'random_forest': 1.0,
                'gradient_boosting': 1.0,
                'neural_network': 1.0
            }
        }
        
        to_model = MagicMock(spec=HybridMachineLearningModel)
        to_model.lookback_periods = 10
        to_model.prediction_horizon = 1
        to_model.ensemble_params = {
            'threshold': 0.85,
            'position_sizing_factor': 0.25,
            'weights': {
                'random_forest': 2.0,
                'gradient_boosting': 1.5,
                'neural_network': 0.5
            }
        }
        
        # Test with different blend factors
        blend_factors = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for blend_factor in blend_factors:
            with patch('Elson.trading_engine.volatility_regime.regime_specific_models.HybridMachineLearningModel') as mock_hybrid_model_class:
                # Mock the model creation
                mock_hybrid_model_class.return_value = MagicMock(spec=HybridMachineLearningModel)
                
                # Create blended model
                blended_model = self.model_selector.create_blended_model(
                    from_model, to_model, blend_factor=blend_factor
                )
                
                # Check that HybridMachineLearningModel was called with blended parameters
                call_args = mock_hybrid_model_class.call_args[1]
                
                # Check lookback and horizon are blended
                expected_lookback = int(from_model.lookback_periods * (1-blend_factor) + 
                                      to_model.lookback_periods * blend_factor)
                expected_horizon = int(from_model.prediction_horizon * (1-blend_factor) + 
                                     to_model.prediction_horizon * blend_factor)
                
                self.assertEqual(call_args['lookback_periods'], expected_lookback)
                self.assertEqual(call_args['prediction_horizon'], expected_horizon)
                
                # Check ensemble parameters are blended
                ensemble_params = call_args['ensemble_params']
                expected_threshold = from_model.ensemble_params['threshold'] * (1-blend_factor) + \
                                   to_model.ensemble_params['threshold'] * blend_factor
                expected_sizing = from_model.ensemble_params['position_sizing_factor'] * (1-blend_factor) + \
                                to_model.ensemble_params['position_sizing_factor'] * blend_factor
                
                self.assertAlmostEqual(ensemble_params['threshold'], expected_threshold)
                self.assertAlmostEqual(ensemble_params['position_sizing_factor'], expected_sizing)
                
                # Check weights are blended properly
                weights = ensemble_params['weights']
                for model_type in ['random_forest', 'gradient_boosting', 'neural_network']:
                    expected_weight = from_model.ensemble_params['weights'][model_type] * (1-blend_factor) + \
                                    to_model.ensemble_params['weights'][model_type] * blend_factor
                    self.assertAlmostEqual(weights[model_type], expected_weight)


if __name__ == '__main__':
    unittest.main()