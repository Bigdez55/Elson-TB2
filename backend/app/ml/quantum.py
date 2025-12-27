"""
Quantum Machine Learning Module

Provides quantum-inspired and quantum computing-based ML models
with proper version compatibility handling for Qiskit.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)

# Qiskit availability flags
QISKIT_AVAILABLE = False
QISKIT_ML_AVAILABLE = False
QISKIT_VERSION = None

# Try to import Qiskit with version compatibility
try:
    import qiskit
    QISKIT_VERSION = qiskit.__version__
    QISKIT_AVAILABLE = True
    logger.info(f"Qiskit {QISKIT_VERSION} available")

    # Import based on version
    major_version = int(QISKIT_VERSION.split('.')[0])

    if major_version >= 1:
        # Qiskit 1.0+ imports
        from qiskit import QuantumCircuit
        from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes

        try:
            from qiskit_aer import AerSimulator
            BACKEND_CLASS = AerSimulator
        except ImportError:
            from qiskit.providers.aer import AerSimulator
            BACKEND_CLASS = AerSimulator

        try:
            from qiskit.primitives import Sampler
            SAMPLER_CLASS = Sampler
        except ImportError:
            SAMPLER_CLASS = None

    else:
        # Legacy Qiskit imports
        from qiskit import QuantumCircuit, execute
        from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes

        try:
            from qiskit import Aer
            BACKEND_CLASS = lambda: Aer.get_backend('statevector_simulator')
        except ImportError:
            BACKEND_CLASS = None

        SAMPLER_CLASS = None

    # Try qiskit-machine-learning
    try:
        from qiskit_machine_learning.algorithms import QSVC
        from qiskit_machine_learning.kernels import FidelityQuantumKernel
        QISKIT_ML_AVAILABLE = True
        logger.info("qiskit-machine-learning available")
    except ImportError:
        try:
            from qiskit_machine_learning.algorithms import QSVC
            from qiskit_machine_learning.kernels import QuantumKernel
            FidelityQuantumKernel = QuantumKernel  # Alias for older versions
            QISKIT_ML_AVAILABLE = True
            logger.info("qiskit-machine-learning (legacy) available")
        except ImportError:
            logger.warning("qiskit-machine-learning not available")

except ImportError as e:
    logger.info(f"Qiskit not available: {e}")


class QuantumFeatureMap:
    """
    Quantum feature map for encoding classical data into quantum states.
    """

    def __init__(self, n_qubits: int = 4, reps: int = 2):
        self.n_qubits = n_qubits
        self.reps = reps
        self.scaler = StandardScaler()
        self._fitted = False

    def fit(self, X: np.ndarray) -> "QuantumFeatureMap":
        """Fit the scaler on training data"""
        self.scaler.fit(X)
        self._fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform and reduce features to match qubit count"""
        if not self._fitted:
            raise ValueError("FeatureMap must be fitted before transform")

        X_scaled = self.scaler.transform(X)

        # Reduce dimensionality if needed
        if X_scaled.shape[1] > self.n_qubits:
            # Use PCA or simple averaging
            try:
                from sklearn.decomposition import PCA
                pca = PCA(n_components=self.n_qubits)
                return pca.fit_transform(X_scaled)
            except Exception:
                # Simple averaging fallback
                X_reduced = np.zeros((X_scaled.shape[0], self.n_qubits))
                chunk_size = X_scaled.shape[1] // self.n_qubits
                for i in range(self.n_qubits):
                    start = i * chunk_size
                    end = start + chunk_size if i < self.n_qubits - 1 else X_scaled.shape[1]
                    X_reduced[:, i] = np.mean(X_scaled[:, start:end], axis=1)
                return X_reduced
        elif X_scaled.shape[1] < self.n_qubits:
            # Pad with zeros
            X_padded = np.zeros((X_scaled.shape[0], self.n_qubits))
            X_padded[:, :X_scaled.shape[1]] = X_scaled
            return X_padded

        return X_scaled

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform in one step"""
        return self.fit(X).transform(X)

    def get_circuit(self) -> Optional["QuantumCircuit"]:
        """Get the quantum circuit for this feature map"""
        if not QISKIT_AVAILABLE:
            return None

        return ZZFeatureMap(
            feature_dimension=self.n_qubits,
            reps=self.reps,
            entanglement='full'
        )


class QuantumClassifier:
    """
    Quantum-inspired classifier with Qiskit backend.

    Falls back to classical SVM if Qiskit is not available.
    """

    def __init__(
        self,
        n_qubits: int = 4,
        reps: int = 2,
        backend: str = "aer_simulator",
        use_quantum: bool = True,
        regularization: float = 1.0
    ):
        self.n_qubits = n_qubits
        self.reps = reps
        self.backend_name = backend
        self.use_quantum = use_quantum and QISKIT_AVAILABLE and QISKIT_ML_AVAILABLE
        self.regularization = regularization

        self.feature_map = QuantumFeatureMap(n_qubits=n_qubits, reps=reps)
        self._classifier = None
        self._is_fitted = False

        # Initialize backend
        self._backend = None
        if self.use_quantum:
            try:
                self._backend = BACKEND_CLASS()
                logger.info(f"Quantum backend initialized: {self._backend}")
            except Exception as e:
                logger.warning(f"Could not initialize quantum backend: {e}")
                self.use_quantum = False

        if not self.use_quantum:
            logger.info("Using classical SVM classifier")
            self._classifier = SVC(
                kernel='rbf',
                C=regularization,
                probability=True,
                random_state=42
            )

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_split: float = 0.2
    ) -> "QuantumClassifier":
        """
        Train the classifier.

        Args:
            X: Training features
            y: Training labels
            validation_split: Fraction for validation

        Returns:
            Self
        """
        # Transform features
        X_transformed = self.feature_map.fit_transform(X)

        # Split for validation
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X_transformed, y,
            test_size=validation_split,
            random_state=42,
            stratify=y if len(np.unique(y)) > 1 else None
        )

        if self.use_quantum:
            try:
                self._fit_quantum(X_train, y_train)
            except Exception as e:
                logger.error(f"Quantum fitting failed: {e}, falling back to classical")
                self.use_quantum = False
                self._classifier = SVC(
                    kernel='rbf',
                    C=self.regularization,
                    probability=True,
                    random_state=42
                )
                self._classifier.fit(X_train, y_train)
        else:
            self._classifier.fit(X_train, y_train)

        # Validate
        y_val_pred = self.predict(X_val)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        logger.info(f"Validation accuracy: {val_accuracy:.4f}")

        self._is_fitted = True
        return self

    def _fit_quantum(self, X: np.ndarray, y: np.ndarray):
        """Fit using quantum kernel"""
        # Create quantum kernel
        feature_map_circuit = self.feature_map.get_circuit()

        if SAMPLER_CLASS is not None:
            # Modern Qiskit approach
            sampler = SAMPLER_CLASS()
            kernel = FidelityQuantumKernel(
                feature_map=feature_map_circuit,
                fidelity=sampler
            )
        else:
            # Legacy approach
            kernel = FidelityQuantumKernel(feature_map=feature_map_circuit)

        # Create and train QSVC
        self._classifier = QSVC(
            quantum_kernel=kernel,
            C=self.regularization
        )
        self._classifier.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels"""
        if not self._is_fitted:
            raise ValueError("Classifier must be fitted before prediction")

        X_transformed = self.feature_map.transform(X)
        return self._classifier.predict(X_transformed)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities"""
        if not self._is_fitted:
            raise ValueError("Classifier must be fitted before prediction")

        X_transformed = self.feature_map.transform(X)

        if hasattr(self._classifier, 'predict_proba'):
            return self._classifier.predict_proba(X_transformed)
        else:
            # For QSVC without probability support, use decision function
            decision = self._classifier.decision_function(X_transformed)
            # Convert to probabilities using sigmoid
            probs = 1 / (1 + np.exp(-decision))
            return np.vstack([1 - probs, probs]).T

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate accuracy score"""
        y_pred = self.predict(X)
        return accuracy_score(y, y_pred)

    def get_info(self) -> Dict[str, Any]:
        """Get classifier information"""
        return {
            "type": "quantum" if self.use_quantum else "classical",
            "n_qubits": self.n_qubits,
            "reps": self.reps,
            "backend": self.backend_name if self.use_quantum else "sklearn",
            "qiskit_version": QISKIT_VERSION,
            "is_fitted": self._is_fitted
        }


class QuantumInspiredClassifier:
    """
    Quantum-inspired classifier that works without Qiskit.

    Uses quantum-inspired feature transformations with classical ML.
    """

    def __init__(
        self,
        n_components: int = 8,
        entanglement_depth: int = 2,
        regularization: float = 1.0
    ):
        self.n_components = n_components
        self.entanglement_depth = entanglement_depth
        self.regularization = regularization

        self.scaler = StandardScaler()
        self._classifier = SVC(
            kernel='rbf',
            C=regularization,
            probability=True,
            random_state=42
        )
        self._is_fitted = False

    def _quantum_inspired_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply quantum-inspired feature transformation.

        This simulates quantum superposition and entanglement effects
        using classical operations.
        """
        n_samples, n_features = X.shape

        # Simulate superposition: create weighted combinations
        superposition = np.zeros((n_samples, self.n_components))

        for i in range(self.n_components):
            # Random phase rotation
            phase = 2 * np.pi * i / self.n_components
            weights = np.cos(np.linspace(0, phase, n_features))

            # Weighted sum (simulating superposition)
            superposition[:, i] = np.dot(X, weights)

        # Simulate entanglement: pairwise interactions
        entangled = superposition.copy()

        for depth in range(self.entanglement_depth):
            for i in range(0, self.n_components - 1, 2):
                # Simulated CNOT-like interaction
                temp = entangled[:, i].copy()
                entangled[:, i] = entangled[:, i] * np.cos(entangled[:, i+1])
                entangled[:, i+1] = temp * np.sin(entangled[:, i+1]) + entangled[:, i+1]

        # Apply quantum-inspired non-linearity
        transformed = np.sin(entangled) ** 2  # Probability amplitude

        return transformed

    def fit(self, X: np.ndarray, y: np.ndarray) -> "QuantumInspiredClassifier":
        """Train the classifier"""
        X_scaled = self.scaler.fit_transform(X)
        X_transformed = self._quantum_inspired_transform(X_scaled)
        self._classifier.fit(X_transformed, y)
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels"""
        if not self._is_fitted:
            raise ValueError("Classifier must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        X_transformed = self._quantum_inspired_transform(X_scaled)
        return self._classifier.predict(X_transformed)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities"""
        if not self._is_fitted:
            raise ValueError("Classifier must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        X_transformed = self._quantum_inspired_transform(X_scaled)
        return self._classifier.predict_proba(X_transformed)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate accuracy score"""
        y_pred = self.predict(X)
        return accuracy_score(y, y_pred)


def get_quantum_classifier(
    n_qubits: int = 4,
    use_quantum: bool = True,
    fallback_to_inspired: bool = True
) -> Union[QuantumClassifier, QuantumInspiredClassifier]:
    """
    Get the best available quantum classifier.

    Args:
        n_qubits: Number of qubits (for true quantum)
        use_quantum: Whether to try true quantum first
        fallback_to_inspired: Use quantum-inspired if quantum unavailable

    Returns:
        A quantum or quantum-inspired classifier
    """
    if use_quantum and QISKIT_AVAILABLE and QISKIT_ML_AVAILABLE:
        try:
            classifier = QuantumClassifier(n_qubits=n_qubits)
            logger.info("Using true quantum classifier")
            return classifier
        except Exception as e:
            logger.warning(f"Quantum classifier failed: {e}")

    if fallback_to_inspired:
        logger.info("Using quantum-inspired classifier")
        return QuantumInspiredClassifier(n_components=n_qubits * 2)

    raise RuntimeError("No quantum classifier available")
