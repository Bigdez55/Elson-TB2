"""
Tests for quantum models implementation.
"""

import unittest
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from trading_engine.ai_model_engine.quantum_models import (
    QuantumFeatureEncoder,
    QuantumKernelClassifier,
    QuantumVariationalClassifier,
    quantum_range_prediction
)


class TestQuantumFeatureEncoder:
    """Test suite for QuantumFeatureEncoder"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.n_qubits = 4
        self.encoder = QuantumFeatureEncoder(n_qubits=self.n_qubits)
        self.sample_data = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 1.1, 1.2]
        ])
    
    def test_initialization(self):
        """Test if encoder initializes with correct parameters"""
        assert self.encoder.n_qubits == self.n_qubits
        assert self.encoder.reps == 2  # Default value
        
    def test_fit_transform(self):
        """Test if fit_transform works correctly"""
        transformed = self.encoder.fit_transform(self.sample_data)
        assert transformed.shape == self.sample_data.shape
        
    def test_transform_dimension_reduction(self):
        """Test if transform handles dimension reduction correctly"""
        # Create data with more features than qubits
        data_with_more_features = np.random.rand(5, 8)  # 8 features, 4 qubits
        transformed = self.encoder.fit_transform(data_with_more_features)
        
        # Should reduce to n_qubits dimensions
        assert transformed.shape == (5, self.n_qubits)
        
    def test_transform_dimension_padding(self):
        """Test if transform handles dimension padding correctly"""
        # Create data with fewer features than qubits
        data_with_fewer_features = np.random.rand(5, 2)  # 2 features, 4 qubits
        transformed = self.encoder.fit_transform(data_with_fewer_features)
        
        # Should pad to n_qubits dimensions
        assert transformed.shape == (5, self.n_qubits)
        
        # Check that padding is with zeros
        for i in range(5):
            assert transformed[i, 2] == 0
            assert transformed[i, 3] == 0
    
    def test_create_feature_map(self):
        """Test if feature map is created correctly"""
        feature_map = self.encoder.create_feature_map()
        
        # Check that the feature map circuit has the correct number of qubits
        assert feature_map.num_qubits == self.n_qubits


class TestQuantumKernelClassifier:
    """Test suite for QuantumKernelClassifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.n_qubits = 2  # Use a small number for faster tests
        self.classifier = QuantumKernelClassifier(n_qubits=self.n_qubits)
        
        # Create simple dataset - binary classification
        self.X = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.7, 0.8],
            [0.9, 1.0]
        ])
        self.y = np.array([0, 0, 1, 1])
    
    @pytest.mark.skip(reason="Full quantum simulation is resource-intensive")
    def test_fit_predict(self):
        """Test fitting and prediction (skip for CI, run manually)"""
        self.classifier.fit(self.X, self.y)
        predictions = self.classifier.predict(self.X)
        
        assert len(predictions) == len(self.y)
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_fit_with_mock(self):
        """Test fitting with mocked quantum execution"""
        with patch('trading_engine.ai_model_engine.quantum_models.QSVC') as mock_qsvc:
            mock_instance = MagicMock()
            mock_qsvc.return_value = mock_instance
            
            self.classifier.fit(self.X, self.y)
            
            # Verify that fit was called
            assert mock_instance.fit.call_count == 1
    
    def test_predict_without_fit(self):
        """Test that prediction raises error when not fitted"""
        with pytest.raises(ValueError):
            self.classifier.predict(self.X)
    
    def test_score_calculation(self):
        """Test score calculation with mocked predictions"""
        self.classifier.qsvc = MagicMock()
        self.classifier.qsvc.predict.return_value = np.array([0, 0, 1, 1])
        
        metrics = self.classifier.score(self.X, self.y)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert metrics['accuracy'] == 1.0  # Perfect predictions


class TestQuantumVariationalClassifier:
    """Test suite for QuantumVariationalClassifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.n_qubits = 2  # Use a small number for faster tests
        self.classifier = QuantumVariationalClassifier(
            n_qubits=self.n_qubits,
            shots=100  # Use fewer shots for faster tests
        )
        
        # Create simple dataset - binary classification
        self.X = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.7, 0.8],
            [0.9, 1.0]
        ])
        self.y = np.array([0, 0, 1, 1])
    
    def test_circuit_creation(self):
        """Test quantum circuit creation"""
        circuit = self.classifier._create_circuit(self.X[0])
        
        assert circuit.num_qubits == self.n_qubits
        # Check if measurements are added
        assert circuit.count_ops().get('measure', 0) == self.n_qubits
    
    @pytest.mark.skip(reason="Full quantum simulation is resource-intensive")
    def test_fit_predict(self):
        """Test fitting and prediction (skip for CI, run manually)"""
        self.classifier.fit(self.X, self.y)
        predictions = self.classifier.predict(self.X)
        
        assert len(predictions) == len(self.y)
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_predict_without_fit(self):
        """Test that prediction raises error when not fitted"""
        with pytest.raises(ValueError):
            self.classifier.predict(self.X)
    
    def test_fit_with_mock(self):
        """Test fitting with mocked execution"""
        # Set optimal_params directly to simulate training
        self.classifier.optimal_params = np.random.random(
            self.n_qubits * (self.classifier.variational_form_reps + 1)
        ) * 2 * np.pi
        
        # Now we should be able to predict
        with patch('trading_engine.ai_model_engine.quantum_models.execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.result.return_value.get_counts.return_value = {'0': 80, '1': 20}
            mock_execute.return_value = mock_result
            
            predictions = self.classifier.predict(self.X[:1])  # Just predict one sample
            assert len(predictions) == 1
            assert predictions[0] == 0  # Should predict class 0 based on counts


def test_quantum_range_prediction():
    """Test quantum range prediction function"""
    # Create a mock model
    mock_model = MagicMock()
    mock_model.predict.side_effect = [
        np.array([0, 1, 0, 1]),  # First call
        np.array([0, 0, 1, 1]),  # Second call
        np.array([0, 1, 1, 1])   # Third call
    ]
    
    # Test data
    X = np.array([
        [0.1, 0.2],
        [0.3, 0.4],
        [0.7, 0.8],
        [0.9, 1.0]
    ])
    
    # Run with fewer samples for testing
    result = quantum_range_prediction(mock_model, X, n_samples=3)
    
    # Check result structure
    assert 'mean' in result
    assert 'lower' in result
    assert 'upper' in result
    
    # Check dimensions
    assert len(result['mean']) == len(X)
    assert len(result['lower']) == len(X)
    assert len(result['upper']) == len(X)
    
    # Verify values are within expected ranges
    assert all(0 <= val <= 1 for val in result['mean'])
    assert all(result['lower'][i] <= result['mean'][i] <= result['upper'][i] 
               for i in range(len(X)))


def test_model_persistence(tmp_path):
    """Test model persistence using the ModelPersistence class"""
    from trading_engine.ai_model_engine.quantum_models import ModelPersistence, QuantumKernelClassifier, QuantumVariationalClassifier
    import os
    
    # Create a model instance
    model = QuantumKernelClassifier(n_qubits=2)
    
    # Create a mocked trained state
    model.qsvc = MagicMock()
    model.feature_map = MagicMock()
    model.kernel = MagicMock()
    model.training_metadata = {
        "training_date": "2025-02-28T12:00:00",
        "training_accuracy": 0.95
    }
    
    # Create temporary directory for model saving
    model_dir = os.path.join(tmp_path, "models")
    
    # Test saving model
    model_path = model.save(model_name="test_model", model_dir=model_dir)
    
    # Check that model file and metadata file exist
    assert os.path.exists(model_path)
    
    # Check that metadata file exists
    metadata_path = model_path.replace(".pkl", "_metadata.json")
    assert os.path.exists(metadata_path)
    
    # Verify metadata content
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        assert metadata["model_type"] == "QuantumKernelClassifier"
        assert metadata["model_name"] == "test_model"
        assert metadata["n_qubits"] == 2
        assert metadata["training_accuracy"] == 0.95
    
    # Test loading model
    loaded_model = QuantumKernelClassifier.load(model_path)
    
    # Check loaded model attributes
    assert loaded_model.n_qubits == 2
    assert loaded_model.training_metadata["training_accuracy"] == 0.95
    
    # Test listing models
    models = ModelPersistence.list_models(model_dir=model_dir)
    assert len(models) == 1
    assert models[0]["model_name"] == "test_model"
    
    # Test filtering by model type
    models = ModelPersistence.list_models(model_dir=model_dir, model_type="QuantumKernelClassifier")
    assert len(models) == 1
    
    models = ModelPersistence.list_models(model_dir=model_dir, model_type="NonExistentModel")
    assert len(models) == 0


if __name__ == '__main__':
    unittest.main()