"""
Tests for the QuantumModel class in the backend.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.models.quantum_model import QuantumModel


class TestQuantumModel:
    """Test suite for the QuantumModel class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.n_qubits = 2  # Use a small number of qubits for faster tests
        self.model = QuantumModel(n_qubits=self.n_qubits, shots=100)
        self.test_features = np.array([0.1, 0.2])

    def test_initialization(self):
        """Test if the model initializes with correct parameters"""
        assert self.model.n_qubits == self.n_qubits
        assert self.model.shots == 100

        # Feature map and variational form should be created
        assert self.model.feature_map is not None
        assert self.model.variational_form is not None
        assert self.model.optimizer is not None
        assert self.model.backend is not None

    def test_normalize_features(self):
        """Test feature normalization"""
        features = np.array([-1.0, 0.0, 1.0, 2.0])
        normalized = self.model._normalize_features(features)

        # Should be normalized to [0, 2π]
        assert np.isclose(normalized.min(), 0.0)
        assert np.isclose(normalized.max(), 2 * np.pi)

        # Edge case: constant features
        constant_features = np.array([1.0, 1.0, 1.0])
        normalized_constant = self.model._normalize_features(constant_features)
        assert np.allclose(normalized_constant, 0.0)

    def test_encode_data(self):
        """Test data encoding into quantum circuit"""
        # Test with correct dimensions
        circuit = self.model.encode_data(np.random.rand(self.n_qubits))
        assert circuit.num_qubits == self.n_qubits

        # Test with incorrect dimensions
        with pytest.raises(ValueError):
            self.model.encode_data(np.random.rand(self.n_qubits + 1))

    @patch("app.models.quantum_model.execute")
    def test_predict(self, mock_execute):
        """Test prediction with mocked execution"""
        # Mock the quantum execution
        mock_result = MagicMock()
        mock_counts = {"00": 60, "01": 10, "10": 20, "11": 10}
        mock_result.get_counts.return_value = mock_counts

        mock_job = MagicMock()
        mock_job.result.return_value = mock_result

        mock_execute.return_value = mock_job

        # Make prediction
        prediction = self.model.predict(self.test_features)

        # Check result structure
        assert isinstance(prediction, dict)
        assert "prediction" in prediction
        assert "confidence" in prediction
        assert "probabilities" in prediction

        # Validate probabilities sum to 1
        assert sum(prediction["probabilities"].values()) == pytest.approx(1.0)

        # Most frequent state should be the prediction
        assert prediction["prediction"] == "00"
        assert prediction["confidence"] == 0.6  # 60/100

    def test_process_counts(self):
        """Test processing of quantum measurement counts"""
        counts = {"00": 60, "01": 20, "10": 15, "11": 5}
        probabilities = self.model._process_counts(counts)

        assert probabilities["00"] == 0.6
        assert probabilities["01"] == 0.2
        assert probabilities["10"] == 0.15
        assert probabilities["11"] == 0.05
        assert sum(probabilities.values()) == pytest.approx(1.0)

    @patch("app.models.quantum_model.execute")
    def test_train(self, mock_execute):
        """Test training with mocked execution"""
        # Mock the optimizer to avoid actual optimization
        with patch("app.models.quantum_model.SPSA") as mock_spsa:
            mock_optimizer = MagicMock()
            # Return optimal parameters and final function value
            mock_optimizer.optimize.return_value = ([0.1, 0.2], 0.5)
            mock_spsa.return_value = mock_optimizer

            # Mock quantum execution for predictions during training
            mock_result = MagicMock()
            mock_counts = {"0": 70, "1": 30}
            mock_result.get_counts.return_value = mock_counts

            mock_job = MagicMock()
            mock_job.result.return_value = mock_result

            mock_execute.return_value = mock_job

            # Create simple training data
            X = np.array([[0.1, 0.2], [0.3, 0.4]])
            y = np.array([0, 1])

            # Train the model
            self.model.train(X, y, epochs=5)

            # Verify optimizer was called
            assert mock_optimizer.optimize.call_count == 1


if __name__ == "__main__":
    unittest.main()
