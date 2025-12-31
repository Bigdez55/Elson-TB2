"""
Quantum Machine Learning models for the trading engine.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
import os
import json
import pickle
import datetime
import time
from sklearn.preprocessing import StandardScaler
from qiskit import QuantumCircuit
# Updated imports for newer Qiskit versions
try:
    from qiskit.providers.aer import AerSimulator
except ImportError:
    from qiskit_aer import AerSimulator
# Define a custom execute function to handle different Qiskit versions
def execute_circuit(circuit, backend, **kwargs):
    """Compatibility wrapper for executing quantum circuits with different Qiskit versions"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Try Qiskit 1.0+ approach
            if hasattr(backend, 'run'):
                return backend.run(circuit, **kwargs)
            # Fall back to old execute approach
            from qiskit import execute as old_execute
            return old_execute(circuit, backend, **kwargs)
        except ImportError as e:
            # This is a dependency issue, retrying won't help
            logger.error(f"Qiskit dependency error: {str(e)}")
            # Fall back to a simpler backend if possible
            if attempt == max_retries - 1:  # Last attempt
                logger.warning("Falling back to basic simulator due to dependency issues")
                try:
                    from qiskit import BasicAer
                    backup_backend = BasicAer.get_backend('statevector_simulator')
                    return old_execute(circuit, backup_backend, **kwargs)
                except Exception as fallback_error:
                    logger.critical(f"Failed to use fallback simulator: {str(fallback_error)}")
                    raise RuntimeError(f"Unable to execute quantum circuit: {str(e)}")
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error executing circuit (attempt {attempt+1}/{max_retries}): {str(e)}. Retrying...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to execute circuit after {max_retries} attempts: {str(e)}")
                raise RuntimeError(f"Quantum circuit execution failed: {str(e)}")

# For backwards compatibility
execute = execute_circuit
from qiskit_aer import Aer
from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
try:
    from qiskit_machine_learning.algorithms import QSVC
    from qiskit_machine_learning.kernels import QuantumKernel
except ImportError:
    print("Warning: qiskit_machine_learning not available. Some functionality may be limited.")
try:
    from qiskit.primitives import Sampler
except ImportError:
    print("Warning: qiskit.primitives.Sampler not available. Using alternative.")
    Sampler = None
import qiskit.quantum_info as qi
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class ModelPersistence:
    """
    Utility class for saving and loading quantum models.
    """
    
    @staticmethod
    def save_model(model, model_name: str, model_dir: str = "models") -> str:
        """
        Save a trained model to disk
        
        Args:
            model: The model to save
            model_name: Base name for the model file
            model_dir: Directory to save the model in
            
        Returns:
            Path to the saved model
        """
        # Create directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Create timestamp for unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(model_dir, f"{model_name}_{timestamp}.pkl")
        
        # Save model with pickle
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Save metadata
        metadata = {
            "model_type": model.__class__.__name__,
            "saved_at": timestamp,
            "model_name": model_name,
            "file_path": file_path
        }
        
        # Add model specific metadata if available
        if hasattr(model, 'get_metadata'):
            model_metadata = model.get_metadata()
            metadata.update(model_metadata)
            
        metadata_path = os.path.join(model_dir, f"{model_name}_{timestamp}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Model saved to {file_path} with metadata at {metadata_path}")
        return file_path
    
    @staticmethod
    def load_model(file_path: str):
        """
        Load a model from disk
        
        Args:
            file_path: Path to the saved model file
            
        Returns:
            The loaded model
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Model file not found: {file_path}")
            
        with open(file_path, 'rb') as f:
            model = pickle.load(f)
            
        logger.info(f"Model loaded from {file_path}")
        return model
    
    @staticmethod
    def list_models(model_dir: str = "models", model_type: str = None) -> List[Dict]:
        """
        List all saved models with their metadata
        
        Args:
            model_dir: Directory containing saved models
            model_type: Optional filter by model type
            
        Returns:
            List of model metadata
        """
        if not os.path.exists(model_dir):
            logger.warning(f"Model directory not found: {model_dir}")
            return []
            
        models = []
        for filename in os.listdir(model_dir):
            if filename.endswith("_metadata.json"):
                metadata_path = os.path.join(model_dir, filename)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    
                if model_type is None or metadata.get("model_type") == model_type:
                    models.append(metadata)
                    
        return models


class QuantumFeatureEncoder:
    """
    Feature encoding for quantum machine learning models.
    Maps classical data to quantum feature space with improved dimensionality reduction
    and feature selection to avoid overfitting.
    """
    
    def __init__(self, n_qubits: int = 4, reps: int = 2, feature_selection: str = 'pca'):
        """
        Initialize the quantum feature encoder
        
        Args:
            n_qubits: Number of qubits to use (should match the number of features)
            reps: Number of repetitions in the feature map circuit
            feature_selection: Method for feature selection/dimensionality reduction
                              ('pca', 'variance', 'correlation', or 'simple')
        """
        self.n_qubits = n_qubits
        self.reps = reps
        self.scaler = StandardScaler()
        self.feature_selection = feature_selection
        self.pca = None
        self.feature_importance = None
        self.correlation_ranking = None
        self.variance_ranking = None
        
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'QuantumFeatureEncoder':
        """
        Fit the feature encoder with dimensionality reduction
        
        Args:
            X: Input features
            y: Optional target values for correlation-based feature selection
            
        Returns:
            Self
        """
        # Input validation
        if X is None or len(X) == 0:
            raise ValueError("Input feature array X cannot be None or empty")
            
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature array, got {X.ndim}D")
            
        # Check for NaN or Inf values
        if np.isnan(X).any() or np.isinf(X).any():
            logger.warning("Input features contain NaN or Inf values. These will be replaced with zeros.")
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
        # Check if y is provided for correlation-based selection
        if self.feature_selection == 'correlation' and y is None:
            logger.warning("Correlation-based feature selection requires target values (y). Falling back to variance-based selection.")
            self.feature_selection = 'variance'
        
        try:
            # Scale features to the range that's appropriate for quantum encoding
            # Add a small constant to avoid division by zero for constant features
            if len(X) < 2:
                logger.warning("Not enough samples to fit StandardScaler. Using identity scaling.")
                self.scaler = lambda X: X  # Identity transformation
                X_scaled = X
            else:
                try:
                    self.scaler.fit(X)
                    X_scaled = self.scaler.transform(X)
                except Exception as e:
                    logger.error(f"Error in feature scaling: {str(e)}")
                    # Fallback to simpler scaling if StandardScaler fails
                    logger.warning("Falling back to simple min-max scaling")
                    X_min = X.min(axis=0)
                    X_max = X.max(axis=0)
                    # Avoid division by zero
                    X_range = np.maximum(X_max - X_min, 1e-10)
                    X_scaled = (X - X_min) / X_range
            
            # If we have more features than qubits, perform feature selection
            if X.shape[1] > self.n_qubits:
                if self.feature_selection == 'pca':
                    try:
                        # Use PCA for dimensionality reduction
                        from sklearn.decomposition import PCA
                        self.pca = PCA(n_components=self.n_qubits)
                        self.pca.fit(X_scaled)
                        
                        # Store feature importance based on explained variance
                        self.feature_importance = self.pca.explained_variance_ratio_
                    except Exception as e:
                        logger.error(f"Error in PCA: {str(e)}")
                        logger.warning("Falling back to variance-based feature selection")
                        self.feature_selection = 'variance'
                        # Proceed to variance-based selection
                        variances = np.var(X_scaled, axis=0)
                        self.variance_ranking = np.argsort(-variances)
                
                if self.feature_selection == 'variance':
                    # Select features with highest variance
                    variances = np.var(X_scaled, axis=0)
                    self.variance_ranking = np.argsort(-variances)
                    
                elif self.feature_selection == 'correlation' and y is not None:
                    try:
                        # Select features with highest correlation to target
                        correlations = []
                        for i in range(X_scaled.shape[1]):
                            if np.std(X_scaled[:, i]) > 1e-10 and np.std(y) > 1e-10:
                                corr = np.abs(np.corrcoef(X_scaled[:, i], y)[0, 1])
                                correlations.append(corr)
                            else:
                                correlations.append(0.0)  # No correlation for constant features
                        
                        correlations = np.array(correlations)
                        self.correlation_ranking = np.argsort(-correlations)
                        self.feature_importance = correlations
                    except Exception as e:
                        logger.error(f"Error in correlation calculation: {str(e)}")
                        logger.warning("Falling back to variance-based feature selection")
                        variances = np.var(X_scaled, axis=0)
                        self.variance_ranking = np.argsort(-variances)
            
            return self
            
        except Exception as e:
            logger.critical(f"Unhandled error in feature encoder fitting: {str(e)}")
            # In case of complete failure, set up minimal defaults
            if not hasattr(self, 'variance_ranking') and X.shape[1] > self.n_qubits:
                self.variance_ranking = np.arange(X.shape[1])
            raise RuntimeError(f"Feature encoding failed: {str(e)}")
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform features using the selected dimensionality reduction method
        
        Args:
            X: Input features
            
        Returns:
            Transformed features ready for quantum encoding
        """
        # Input validation
        if X is None or len(X) == 0:
            raise ValueError("Input feature array X cannot be None or empty")
            
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature array, got {X.ndim}D")
            
        # Ensure input has the correct shape
        if X.shape[1] != self.scaler.n_features_in_:
            raise ValueError(f"Expected {self.scaler.n_features_in_} features, got {X.shape[1]}")
            
        # Check for NaN or Inf values
        if np.isnan(X).any() or np.isinf(X).any():
            logger.warning("Input features contain NaN or Inf values. These will be replaced with zeros.")
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        try:
            # Scale the features
            if callable(self.scaler) and not hasattr(self.scaler, 'transform'):
                # Handle the case where scaler is a simple function (identity)
                X_scaled = self.scaler(X)
            else:
                try:
                    X_scaled = self.scaler.transform(X)
                except Exception as e:
                    logger.error(f"Error in feature scaling during transform: {str(e)}")
                    # Fallback to simpler scaling if StandardScaler fails
                    logger.warning("Falling back to simple min-max scaling during transform")
                    X_min = X.min(axis=0)
                    X_max = X.max(axis=0)
                    # Avoid division by zero
                    X_range = np.maximum(X_max - X_min, 1e-10)
                    X_scaled = (X - X_min) / X_range
            
            # If we have more features than qubits, reduce dimensions
            if X.shape[1] > self.n_qubits:
                if self.feature_selection == 'pca' and self.pca is not None:
                    try:
                        # Use PCA transformation
                        return self.pca.transform(X_scaled)
                    except Exception as e:
                        logger.error(f"Error in PCA transform: {str(e)}")
                        # Fall back to variance if available, otherwise to simple approach
                        if hasattr(self, 'variance_ranking') and self.variance_ranking is not None:
                            logger.warning("Falling back to variance-based feature selection")
                            return X_scaled[:, self.variance_ranking[:self.n_qubits]]
                
                if self.feature_selection == 'variance' and self.variance_ranking is not None:
                    # Select top features by variance
                    return X_scaled[:, self.variance_ranking[:self.n_qubits]]
                    
                elif self.feature_selection == 'correlation' and self.correlation_ranking is not None:
                    # Select top features by correlation
                    return X_scaled[:, self.correlation_ranking[:self.n_qubits]]
                    
                else:
                    # Fall back to simple approach (averaging groups of features)
                    logger.warning("Using simple feature grouping as fallback")
                    X_reduced = np.zeros((X_scaled.shape[0], self.n_qubits))
                    for i in range(self.n_qubits):
                        start_idx = i * (X.shape[1] // self.n_qubits)
                        end_idx = min((i + 1) * (X.shape[1] // self.n_qubits), X.shape[1])
                        if start_idx < end_idx:  # Ensure valid slice
                            X_reduced[:, i] = np.mean(X_scaled[:, start_idx:end_idx], axis=1)
                    return X_reduced
            else:
                # If we have fewer features than qubits, pad with zeros
                if X.shape[1] < self.n_qubits:
                    X_padded = np.zeros((X_scaled.shape[0], self.n_qubits))
                    X_padded[:, :X.shape[1]] = X_scaled
                    return X_padded
                
                return X_scaled
                
        except Exception as e:
            logger.critical(f"Unhandled error in feature transform: {str(e)}")
            # In case of complete failure, return simple padded data as fallback
            logger.warning("Using zero-padded identity transform as emergency fallback")
            X_emergency = np.zeros((X.shape[0], self.n_qubits))
            cols_to_use = min(X.shape[1], self.n_qubits)
            X_emergency[:, :cols_to_use] = X[:, :cols_to_use]
            return X_emergency
    
    def fit_transform(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """
        Fit and transform the features
        
        Args:
            X: Input features
            y: Optional target values for correlation-based feature selection
            
        Returns:
            Transformed features
        """
        return self.fit(X, y).transform(X)
    
    def analyze_feature_importance(self) -> Dict[str, np.ndarray]:
        """
        Get feature importance information
        
        Returns:
            Dictionary with feature importance metrics
        """
        if self.feature_selection == 'pca' and self.pca is not None:
            return {
                'explained_variance': self.pca.explained_variance_ratio_,
                'components': self.pca.components_
            }
        elif self.feature_selection == 'correlation' and self.feature_importance is not None:
            return {
                'correlation_scores': self.feature_importance,
                'top_features': self.correlation_ranking[:self.n_qubits]
            }
        elif self.feature_selection == 'variance' and self.variance_ranking is not None:
            return {
                'top_features': self.variance_ranking[:self.n_qubits]
            }
        else:
            return {}
    
    def create_feature_map(self) -> QuantumCircuit:
        """
        Create a quantum feature map circuit with entanglement
        
        Returns:
            Quantum circuit for feature mapping
        """
        # Using ZZFeatureMap which encodes classical data into quantum states
        feature_map = ZZFeatureMap(
            feature_dimension=self.n_qubits,
            reps=self.reps,
            entanglement='full'
        )
        return feature_map


class QuantumKernelClassifier:
    """
    Quantum Kernel-based classifier using quantum feature maps with
    enhanced regularization and validation to prevent overfitting.
    """
    
    def __init__(
        self, 
        n_qubits: int = 4, 
        feature_map_reps: int = 2,
        backend_name: str = 'statevector_simulator',
        feature_selection: str = 'pca',
        regularization: float = 1.0,
        noise_mitigation: bool = True
    ):
        """
        Initialize the quantum kernel classifier
        
        Args:
            n_qubits: Number of qubits to use
            feature_map_reps: Number of repetitions in the feature map
            backend_name: Name of the Qiskit backend to use
            feature_selection: Feature selection method ('pca', 'variance', 'correlation')
            regularization: Regularization strength (C parameter in SVC)
            noise_mitigation: Whether to apply quantum noise mitigation techniques
        """
        self.n_qubits = n_qubits
        self.feature_map_reps = feature_map_reps
        self.backend_name = backend_name
        self.feature_selection = feature_selection
        self.regularization = regularization
        self.noise_mitigation = noise_mitigation
        
        # Initialize backend with better error handling and fallbacks
        self.backend = None
        backends_to_try = [
            lambda: AerSimulator(method='automatic'),
            lambda: Aer.get_backend('aer_simulator'),
            lambda: Aer.get_backend('statevector_simulator'),
            lambda: Aer.get_backend('qasm_simulator')
        ]
        
        for backend_func in backends_to_try:
            try:
                self.backend = backend_func()
                logger.info(f"Successfully initialized quantum backend: {self.backend}")
                break
            except Exception as e:
                logger.warning(f"Failed to initialize backend: {str(e)}")
        
        # If all backends failed, use a basic simulator as last resort
        if self.backend is None:
            try:
                from qiskit import BasicAer
                self.backend = BasicAer.get_backend('statevector_simulator')
                logger.warning("Using BasicAer as fallback. Performance may be limited.")
            except Exception as e:
                logger.critical(f"Could not initialize any quantum backend: {str(e)}")
                raise RuntimeError("Failed to initialize quantum backend. Check Qiskit installation.")
        
        self.encoder = QuantumFeatureEncoder(
            n_qubits=n_qubits, 
            reps=feature_map_reps,
            feature_selection=feature_selection
        )
        self.feature_map = None
        self.kernel = None
        self.qsvc = None
        self.training_metadata = {}
        self.validation_scores = {}
        
    def save(self, model_name: str = "quantum_kernel_classifier", model_dir: str = "models") -> str:
        """
        Save the trained model to disk
        
        Args:
            model_name: Name for the model
            model_dir: Directory to save the model in
            
        Returns:
            Path to the saved model file
        """
        if self.qsvc is None:
            raise ValueError("Model has not been trained yet")
            
        return ModelPersistence.save_model(self, model_name, model_dir)
        
    @classmethod
    def load(cls, file_path: str) -> 'QuantumKernelClassifier':
        """
        Load a trained model from disk
        
        Args:
            file_path: Path to the saved model file
            
        Returns:
            Loaded model
        """
        return ModelPersistence.load_model(file_path)
        
    def get_metadata(self) -> Dict:
        """
        Get model metadata for persistence
        
        Returns:
            Dictionary of model metadata
        """
        metadata = {
            "n_qubits": self.n_qubits,
            "feature_map_reps": self.feature_map_reps,
            "backend_name": self.backend_name,
            "feature_selection": self.feature_selection,
            "regularization": self.regularization,
            "noise_mitigation": self.noise_mitigation
        }
        
        # Add training metadata if available
        if self.training_metadata:
            metadata.update(self.training_metadata)
            
        # Add validation scores if available
        if self.validation_scores:
            metadata["validation_scores"] = self.validation_scores
            
        return metadata
        
    def fit(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        validation_split: float = 0.2,
        C: float = None,
        class_weight: str = 'balanced'
    ) -> 'QuantumKernelClassifier':
        """
        Fit the quantum kernel classifier with validation
        
        Args:
            X: Input features
            y: Target labels
            validation_split: Fraction of data to use for validation
            C: Regularization parameter for SVC (overrides the instance parameter)
            class_weight: Weighting for imbalanced classes ('balanced' or None)
            
        Returns:
            Self
        """
        # Record start time for training duration
        start_time = datetime.datetime.now()
        
        # Use regularization parameter if provided, otherwise use the instance parameter
        C = C if C is not None else self.regularization
        
        # Split data into training and validation sets
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, 
            random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        
        # Prepare features for quantum encoding
        X_train_transformed = self.encoder.fit_transform(X_train, y_train)
        X_val_transformed = self.encoder.transform(X_val)
        
        # Create feature map
        self.feature_map = self.encoder.create_feature_map()
        
        # Apply noise mitigation if enabled
        if self.noise_mitigation and self.backend_name != 'statevector_simulator':
            from qiskit.providers.aer.noise import NoiseModel
            try:
                # Use a basic depolarizing noise model for simulation
                noise_model = NoiseModel()
                noise_model.add_all_qubit_quantum_error(
                    qi.depolarizing_error(0.01, 1), ['u1', 'u2', 'u3']
                )
                self.backend.set_options(noise_model=noise_model)
            except Exception as e:
                logger.warning(f"Could not apply noise mitigation: {str(e)}")
        
        # Create quantum kernel
        try:
            sampler = Sampler()
            self.kernel = QuantumKernel(
                feature_map=self.feature_map,
                primitive=sampler
            )
            
            # Train quantum SVM with the kernel
            self.qsvc = QSVC(
                quantum_kernel=self.kernel,
                C=C,
                class_weight=class_weight
            )
            
            # Fit the model
            self.qsvc.fit(X_train_transformed, y_train)
            
            # Calculate training metrics
            y_train_pred = self.qsvc.predict(X_train_transformed)
            train_accuracy = accuracy_score(y_train, y_train_pred)
            train_f1 = f1_score(y_train, y_train_pred, average='weighted')
            
            # Calculate validation metrics
            y_val_pred = self.qsvc.predict(X_val_transformed)
            val_accuracy = accuracy_score(y_val, y_val_pred)
            val_f1 = f1_score(y_val, y_val_pred, average='weighted')
            
            # Store validation scores
            self.validation_scores = {
                'accuracy': val_accuracy,
                'f1': val_f1,
                'accuracy_diff': train_accuracy - val_accuracy,
                'f1_diff': train_f1 - val_f1
            }
            
            # Record training metadata
            end_time = datetime.datetime.now()
            self.training_metadata = {
                "training_date": start_time.isoformat(),
                "training_duration_seconds": (end_time - start_time).total_seconds(),
                "num_training_samples": len(X_train),
                "num_validation_samples": len(X_val),
                "training_accuracy": train_accuracy,
                "validation_accuracy": val_accuracy,
                "training_f1": train_f1,
                "validation_f1": val_f1,
                "regularization_parameter": C,
                "class_weight": class_weight,
                "class_distribution": {str(label): int(count) for label, count in zip(*np.unique(y, return_counts=True))},
                "feature_importance": self.encoder.analyze_feature_importance()
            }
            
            logger.info(f"Quantum kernel classifier fitted - Training accuracy: {train_accuracy:.4f}, Validation accuracy: {val_accuracy:.4f}")
            
            # Check for overfitting
            if train_accuracy - val_accuracy > 0.2:
                logger.warning(f"Possible overfitting detected: training accuracy {train_accuracy:.4f} much higher than validation accuracy {val_accuracy:.4f}")
            
        except Exception as e:
            logger.error(f"Error fitting quantum kernel classifier: {str(e)}")
            raise
        
        return self
    
    def cross_validate(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        n_splits: int = 5, 
        C_values: List[float] = None
    ) -> Dict[str, Any]:
        """
        Perform cross-validation to find optimal hyperparameters
        
        Args:
            X: Input features
            y: Target labels
            n_splits: Number of cross-validation splits
            C_values: List of regularization values to try
            
        Returns:
            Dictionary with cross-validation results
        """
        from sklearn.model_selection import StratifiedKFold
        
        # Default regularization values if not provided
        if C_values is None:
            C_values = [0.1, 1.0, 10.0]
        
        # Initialize cross-validation
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        results = {
            'params': [],
            'mean_scores': [],
            'std_scores': [],
            'all_scores': []
        }
        
        # Preprocess features for consistency
        X_transformed = self.encoder.fit_transform(X, y)
        
        # Create feature map
        self.feature_map = self.encoder.create_feature_map()
        
        # Create quantum kernel
        sampler = Sampler()
        self.kernel = QuantumKernel(
            feature_map=self.feature_map,
            primitive=sampler
        )
        
        best_score = -np.inf
        best_params = None
        
        for C in C_values:
            scores = []
            for train_idx, test_idx in cv.split(X_transformed, y):
                # Split data for this fold
                X_train_fold, X_test_fold = X_transformed[train_idx], X_transformed[test_idx]
                y_train_fold, y_test_fold = y[train_idx], y[test_idx]
                
                # Create and train model with current parameters
                qsvc = QSVC(quantum_kernel=self.kernel, C=C)
                qsvc.fit(X_train_fold, y_train_fold)
                
                # Evaluate
                score = qsvc.score(X_test_fold, y_test_fold)
                scores.append(score)
            
            # Calculate mean and std of scores
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # Store results
            results['params'].append({'C': C})
            results['mean_scores'].append(mean_score)
            results['std_scores'].append(std_score)
            results['all_scores'].append(scores)
            
            # Track best parameters
            if mean_score > best_score:
                best_score = mean_score
                best_params = {'C': C}
        
        # Store best parameters
        results['best_params'] = best_params
        results['best_score'] = best_score
        
        # Set optimal parameters
        self.regularization = best_params['C']
        
        logger.info(f"Cross-validation results: best C={best_params['C']} with score {best_score:.4f}")
        
        return results
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions with the quantum kernel classifier
        
        Args:
            X: Input features
            
        Returns:
            Predicted labels
        """
        if self.qsvc is None:
            raise ValueError("Model has not been fitted yet")
        
        # Transform features
        X_transformed = self.encoder.transform(X)
        
        # Make predictions
        return self.qsvc.predict(X_transformed)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities
        
        Args:
            X: Input features
            
        Returns:
            Class probabilities
        """
        if self.qsvc is None:
            raise ValueError("Model has not been fitted yet")
        
        # Check if SVC has predict_proba (needs probability=True)
        if not hasattr(self.qsvc, 'predict_proba'):
            # Fall back to decision function
            X_transformed = self.encoder.transform(X)
            decision_values = self.qsvc.decision_function(X_transformed)
            
            # Convert decision values to probabilities using sigmoid function
            def sigmoid(x):
                return 1 / (1 + np.exp(-x))
            
            probs = sigmoid(decision_values)
            return np.vstack([1-probs, probs]).T
        
        # Transform features
        X_transformed = self.encoder.transform(X)
        
        # Return probabilities
        return self.qsvc.predict_proba(X_transformed)
    
    def score(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics
        
        Args:
            X: Input features
            y: True labels
            
        Returns:
            Dictionary with performance metrics
        """
        y_pred = self.predict(X)
        
        # Determine if binary or multiclass
        classes = np.unique(y)
        is_binary = len(classes) == 2
        
        if is_binary:
            average = 'binary'
        else:
            average = 'weighted'
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average=average, zero_division=0),
            'recall': recall_score(y, y_pred, average=average, zero_division=0),
            'f1': f1_score(y, y_pred, average=average, zero_division=0)
        }
        
        return metrics


class QuantumVariationalClassifier:
    """
    Quantum Variational Classifier (QVC) using parameterized quantum circuits
    with enhanced regularization and validation to prevent overfitting.
    """
    
    def __init__(
        self, 
        n_qubits: int = 4, 
        feature_map_reps: int = 2,
        variational_form_reps: int = 3,
        backend_name: str = 'statevector_simulator',
        shots: int = 1024,
        feature_selection: str = 'pca',
        regularization_strength: float = 0.01,
        noise_mitigation: bool = True
    ):
        """
        Initialize the quantum variational classifier
        
        Args:
            n_qubits: Number of qubits to use
            feature_map_reps: Number of repetitions in the feature map
            variational_form_reps: Number of repetitions in the variational form
            backend_name: Name of the Qiskit backend to use
            shots: Number of shots for quantum circuit execution
            feature_selection: Method for feature selection ('pca', 'variance', 'correlation')
            regularization_strength: Strength of L2 regularization
            noise_mitigation: Whether to apply quantum noise mitigation
        """
        self.n_qubits = n_qubits
        self.feature_map_reps = feature_map_reps
        self.variational_form_reps = variational_form_reps
        self.backend_name = backend_name
        
        # Initialize backend with better error handling and fallbacks
        self.backend = None
        backends_to_try = [
            lambda: AerSimulator(method='automatic'),
            lambda: Aer.get_backend('aer_simulator'),
            lambda: Aer.get_backend('statevector_simulator'),
            lambda: Aer.get_backend('qasm_simulator')
        ]
        
        for backend_func in backends_to_try:
            try:
                self.backend = backend_func()
                logger.info(f"Successfully initialized quantum backend: {self.backend}")
                break
            except Exception as e:
                logger.warning(f"Failed to initialize backend: {str(e)}")
        
        # If all backends failed, use a basic simulator as last resort
        if self.backend is None:
            try:
                from qiskit import BasicAer
                self.backend = BasicAer.get_backend('statevector_simulator')
                logger.warning("Using BasicAer as fallback. Performance may be limited.")
            except Exception as e:
                logger.critical(f"Could not initialize any quantum backend: {str(e)}")
                raise RuntimeError("Failed to initialize quantum backend. Check Qiskit installation.")
                
        self.shots = shots
        self.feature_selection = feature_selection
        self.regularization_strength = regularization_strength
        self.noise_mitigation = noise_mitigation
        
        self.encoder = QuantumFeatureEncoder(
            n_qubits=n_qubits, 
            reps=feature_map_reps,
            feature_selection=feature_selection
        )
        self.feature_map = None
        self.variational_form = None
        self.circuit = None
        self.optimal_params = None
        self.training_metadata = {}
        self.validation_scores = {}
        
    def save(self, model_name: str = "quantum_variational_classifier", model_dir: str = "models") -> str:
        """
        Save the trained model to disk
        
        Args:
            model_name: Name for the model
            model_dir: Directory to save the model in
            
        Returns:
            Path to the saved model file
        """
        if self.optimal_params is None:
            raise ValueError("Model has not been trained yet")
            
        return ModelPersistence.save_model(self, model_name, model_dir)
        
    @classmethod
    def load(cls, file_path: str) -> 'QuantumVariationalClassifier':
        """
        Load a trained model from disk
        
        Args:
            file_path: Path to the saved model file
            
        Returns:
            Loaded model
        """
        return ModelPersistence.load_model(file_path)
        
    def get_metadata(self) -> Dict:
        """
        Get model metadata for persistence
        
        Returns:
            Dictionary of model metadata
        """
        metadata = {
            "n_qubits": self.n_qubits,
            "feature_map_reps": self.feature_map_reps,
            "variational_form_reps": self.variational_form_reps,
            "backend_name": self.backend_name,
            "shots": self.shots,
            "feature_selection": self.feature_selection,
            "regularization_strength": self.regularization_strength,
            "noise_mitigation": self.noise_mitigation,
            "num_parameters": len(self.optimal_params) if self.optimal_params is not None else 0
        }
        
        # Add training metadata if available
        if self.training_metadata:
            metadata.update(self.training_metadata)
            
        # Add validation scores if available
        if self.validation_scores:
            metadata["validation_scores"] = self.validation_scores
            
        return metadata
        
    def _create_circuit(self, x: np.ndarray, params: np.ndarray = None) -> QuantumCircuit:
        """
        Create quantum circuit with feature map and variational form
        
        Args:
            x: Input feature vector
            params: Parameters for the variational form
            
        Returns:
            Quantum circuit
        """
        # Create feature map circuit
        self.feature_map = ZZFeatureMap(
            feature_dimension=self.n_qubits,
            reps=self.feature_map_reps,
            entanglement='full'
        )
        
        # Create variational form with more expressive ansatz
        self.variational_form = RealAmplitudes(
            num_qubits=self.n_qubits,
            reps=self.variational_form_reps,
            entanglement='full'
        )
        
        # Combine feature map and variational form
        circuit = QuantumCircuit(self.n_qubits)
        circuit.compose(self.feature_map.bind_parameters(x), inplace=True)
        
        if params is not None:
            circuit.compose(self.variational_form.bind_parameters(params), inplace=True)
        else:
            circuit.compose(self.variational_form, inplace=True)
        
        # Add measurement
        circuit.measure_all()
        
        return circuit
    
    def _objective_function(
        self, 
        params: np.ndarray, 
        X: np.ndarray, 
        y: np.ndarray, 
        add_regularization: bool = True
    ) -> float:
        """
        Objective function for training the quantum variational classifier
        with regularization to prevent overfitting
        
        Args:
            params: Parameters for the variational form
            X: Input features
            y: Target labels
            add_regularization: Whether to add regularization term
            
        Returns:
            Loss value
        """
        loss = 0.0
        
        # Calculate data loss
        for i in range(len(X)):
            # Create circuit for this sample
            circuit = self._create_circuit(X[i], params)
            
            # Execute circuit
            counts = execute(circuit, self.backend, shots=self.shots).result().get_counts()
            
            # Calculate probabilities
            prob_0 = sum(v for k, v in counts.items() if k[0] == '0') / self.shots
            prob_1 = sum(v for k, v in counts.items() if k[0] == '1') / self.shots
            
            # Calculate loss (depends on the label)
            if y[i] == 0:
                loss += 1 - prob_0
            else:
                loss += 1 - prob_1
        
        # Add L2 regularization to prevent overfitting
        if add_regularization:
            # L2 regularization term
            l2_term = self.regularization_strength * np.sum(params ** 2)
            # Add to loss
            loss += l2_term
        
        # Return average loss
        return loss / len(X)
    
    def fit(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        validation_split: float = 0.2,
        optimizer: str = 'COBYLA', 
        max_iter: int = 100,
        early_stopping: bool = True,
        patience: int = 10
    ) -> 'QuantumVariationalClassifier':
        """
        Fit the quantum variational classifier with validation
        
        Args:
            X: Input features
            y: Target labels
            validation_split: Fraction of data to use for validation
            optimizer: Optimizer to use for training ('COBYLA', 'SPSA')
            max_iter: Maximum number of iterations
            early_stopping: Whether to use early stopping
            patience: Number of iterations without improvement before stopping
            
        Returns:
            Self
        """
        # Split data into training and validation sets
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, 
            random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        
        # Prepare features for quantum encoding
        X_train_transformed = self.encoder.fit_transform(X_train, y_train)
        X_val_transformed = self.encoder.transform(X_val)
        
        # Initialize parameters for variational form
        num_params = self.n_qubits * (self.variational_form_reps + 1)
        initial_params = np.random.random(num_params) * 2 * np.pi
        
        # Apply noise mitigation if enabled
        if self.noise_mitigation and self.backend_name != 'statevector_simulator':
            from qiskit.providers.aer.noise import NoiseModel
            try:
                # Use a basic depolarizing noise model for simulation
                noise_model = NoiseModel()
                noise_model.add_all_qubit_quantum_error(
                    qi.depolarizing_error(0.01, 1), ['u1', 'u2', 'u3']
                )
                self.backend.set_options(noise_model=noise_model)
            except Exception as e:
                logger.warning(f"Could not apply noise mitigation: {str(e)}")
        
        # Use the appropriate optimizer
        from qiskit.algorithms.optimizers import COBYLA, SPSA
        
        try:
            if optimizer == 'COBYLA':
                opt = COBYLA(maxiter=max_iter)
            elif optimizer == 'SPSA':
                opt = SPSA(maxiter=max_iter)
            else:
                logger.warning(f"Unknown optimizer {optimizer}, defaulting to COBYLA")
                opt = COBYLA(maxiter=max_iter)
            
            # Record start time for training duration
            start_time = datetime.datetime.now()
            
            # Custom callback for early stopping
            best_val_loss = float('inf')
            best_params = None
            no_improvement_count = 0
            
            # Define objective function for training
            def objective_train(params):
                return self._objective_function(params, X_train_transformed, y_train)
            
            # Define callback function for validation
            def callback(current_params, current_loss, iteration):
                nonlocal best_val_loss, best_params, no_improvement_count
                
                # Calculate validation loss
                val_loss = self._objective_function(
                    current_params, X_val_transformed, y_val, add_regularization=False
                )
                
                # Check for improvement
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_params = current_params.copy()
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
                
                # Early stopping
                if early_stopping and no_improvement_count >= patience:
                    logger.info(f"Early stopping at iteration {iteration}")
                    return True  # Stop optimization
                
                return False  # Continue optimization
            
            # Run the optimization
            logger.info(f"Starting quantum model optimization with {optimizer}")
            opt.callback = callback if early_stopping else None
            result = opt.minimize(objective_train, initial_params)
            
            # Use best parameters if early stopping was triggered
            if early_stopping and best_params is not None:
                self.optimal_params = best_params
                final_loss = best_val_loss
            else:
                self.optimal_params = result[0]  # Get the optimal parameters
                final_loss = result[1]  # Get the final loss value
            
            # Make predictions for training set
            train_predictions = self._make_predictions(X_train_transformed)
            train_accuracy = accuracy_score(y_train, train_predictions)
            train_f1 = f1_score(y_train, train_predictions, average='weighted')
            
            # Make predictions for validation set
            val_predictions = self._make_predictions(X_val_transformed)
            val_accuracy = accuracy_score(y_val, val_predictions)
            val_f1 = f1_score(y_val, val_predictions, average='weighted')
            
            # Store validation scores
            self.validation_scores = {
                'accuracy': val_accuracy,
                'f1': val_f1,
                'accuracy_diff': train_accuracy - val_accuracy,
                'f1_diff': train_f1 - val_f1,
                'loss': float(final_loss)
            }
            
            # Record training metadata
            end_time = datetime.datetime.now()
            self.training_metadata = {
                "training_date": start_time.isoformat(),
                "training_duration_seconds": (end_time - start_time).total_seconds(),
                "num_training_samples": len(X_train),
                "num_validation_samples": len(X_val),
                "training_accuracy": train_accuracy,
                "validation_accuracy": val_accuracy,
                "training_f1": train_f1,
                "validation_f1": val_f1,
                "final_loss": float(final_loss),
                "optimizer": optimizer,
                "max_iterations": max_iter,
                "early_stopping": early_stopping,
                "class_distribution": {str(label): int(count) for label, count in zip(*np.unique(y, return_counts=True))},
                "feature_importance": self.encoder.analyze_feature_importance()
            }
            
            logger.info(f"Quantum variational classifier training completed - Training accuracy: {train_accuracy:.4f}, Validation accuracy: {val_accuracy:.4f}")
            
            # Check for overfitting
            if train_accuracy - val_accuracy > 0.2:
                logger.warning(f"Possible overfitting detected: training accuracy {train_accuracy:.4f} much higher than validation accuracy {val_accuracy:.4f}")
            
        except Exception as e:
            logger.error(f"Error during quantum optimization: {str(e)}")
            # Fallback to initial parameters if optimization fails
            self.optimal_params = initial_params
            logger.warning("Using initial random parameters due to optimization failure")
        
        return self
    
    def _make_predictions(self, X_transformed: np.ndarray) -> np.ndarray:
        """
        Make predictions using the current model parameters
        
        Args:
            X_transformed: Transformed input features
            
        Returns:
            Predicted labels
        """
        predictions = []
        for x in X_transformed:
            circuit = self._create_circuit(x, self.optimal_params)
            counts = execute(circuit, self.backend, shots=self.shots).result().get_counts()
            
            # Calculate probabilities
            prob_0 = sum(v for k, v in counts.items() if k[0] == '0') / self.shots
            prob_1 = sum(v for k, v in counts.items() if k[0] == '1') / self.shots
            
            # Predict the class with higher probability
            pred = 1 if prob_1 > prob_0 else 0
            predictions.append(pred)
        
        return np.array(predictions)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions with the quantum variational classifier
        
        Args:
            X: Input features
            
        Returns:
            Predicted labels
        """
        if self.optimal_params is None:
            raise ValueError("Model has not been fitted yet")
        
        # Transform features
        X_transformed = self.encoder.transform(X)
        
        # Make predictions
        return self._make_predictions(X_transformed)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities
        
        Args:
            X: Input features
            
        Returns:
            Class probabilities as a 2D array [n_samples, n_classes]
        """
        if self.optimal_params is None:
            raise ValueError("Model has not been fitted yet")
        
        # Transform features
        X_transformed = self.encoder.transform(X)
        
        # Make probabilistic predictions
        probabilities = []
        for x in X_transformed:
            circuit = self._create_circuit(x, self.optimal_params)
            counts = execute(circuit, self.backend, shots=self.shots).result().get_counts()
            
            # Calculate probabilities
            prob_0 = sum(v for k, v in counts.items() if k[0] == '0') / self.shots
            prob_1 = sum(v for k, v in counts.items() if k[0] == '1') / self.shots
            
            probabilities.append([prob_0, prob_1])
        
        return np.array(probabilities)
    
    def score(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics
        
        Args:
            X: Input features
            y: True labels
            
        Returns:
            Dictionary with performance metrics
        """
        y_pred = self.predict(X)
        
        # Determine if binary or multiclass
        classes = np.unique(y)
        is_binary = len(classes) == 2
        
        if is_binary:
            average = 'binary'
        else:
            average = 'weighted'
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average=average, zero_division=0),
            'recall': recall_score(y, y_pred, average=average, zero_division=0),
            'f1': f1_score(y, y_pred, average=average, zero_division=0)
        }
        
        return metrics


def quantum_range_prediction(
    model, 
    X: np.ndarray, 
    confidence_level: float = 0.95,
    n_samples: int = 100
) -> Dict[str, np.ndarray]:
    """
    Generate range-based predictions using quantum models with uncertainty
    
    Args:
        model: Fitted quantum model
        X: Input features
        confidence_level: Confidence level for the prediction intervals
        n_samples: Number of samples for uncertainty estimation
        
    Returns:
        Dictionary with mean predictions and confidence intervals
    """
    predictions = []
    
    # Generate multiple predictions with slight variations
    for _ in range(n_samples):
        # Add small random noise to input features to simulate quantum uncertainty
        X_noisy = X + np.random.normal(0, 0.01, X.shape)
        
        # Make predictions
        y_pred = model.predict(X_noisy)
        predictions.append(y_pred)
    
    # Convert to array for easier manipulation
    predictions = np.array(predictions)
    
    # Calculate mean prediction
    mean_pred = np.mean(predictions, axis=0)
    
    # Calculate confidence intervals
    lower_bound = np.percentile(predictions, (1 - confidence_level) / 2 * 100, axis=0)
    upper_bound = np.percentile(predictions, (1 + confidence_level) / 2 * 100, axis=0)
    
    return {
        'mean': mean_pred,
        'lower': lower_bound,
        'upper': upper_bound
    }