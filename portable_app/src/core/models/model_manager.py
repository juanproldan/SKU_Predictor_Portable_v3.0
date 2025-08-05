"""
Model management system for SKU Predictor v2.0

This module provides centralized model loading, caching, and prediction
with proper error handling and lifecycle management.
"""

import os
import joblib
import torch
from typing import Dict, Any, Optional, Tuple, Union, List
from dataclasses import dataclass
from enum import Enum
import threading
from abc import ABC, abstractmethod

# Mock error handling classes (defined first to be available everywhere)
class ErrorCategory:
    MODEL_LOADING = "model_loading"
    PREDICTION = "prediction"
    DATABASE = "database"

class ErrorSeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

try:
    from config.settings import get_config
    from core.error_handler import get_error_handler, handle_exceptions
except ImportError:
    # Fallback for development
    def get_config():
        class MockConfig:
            paths = type('obj', (object,), {
                'vin_model_dir': 'models',
                'sku_nn_model_dir': 'models/sku_nn'
            })
        return MockConfig()

    def get_error_handler():
        class MockErrorHandler:
            def handle_error(self, *args, **kwargs):
                print(f"Error: {args}")
            def handle_model_error(self, *args, **kwargs):
                print(f"Model Error: {args}")
        return MockErrorHandler()

    def handle_exceptions(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class ModelType(Enum):
    """Types of models supported by the system."""
    VIN_MAKER = "vin_maker"
    VIN_YEAR = "vin_year"
    VIN_SERIES = "vin_series"
    SKU_NN = "sku_nn"


class ModelStatus(Enum):
    """Status of model loading."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class ModelInfo:
    """Information about a loaded model."""
    model_type: ModelType
    model_path: str
    status: ModelStatus
    model: Optional[Any] = None
    encoders: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class PredictionResult:
    """Result of a model prediction."""
    success: bool
    prediction: Optional[Any] = None
    confidence: Optional[float] = None
    error_message: Optional[str] = None
    model_type: Optional[ModelType] = None


class BaseModel(ABC):
    """Abstract base class for all models."""

    def __init__(self, model_type: ModelType, model_path: str):
        self.model_type = model_type
        self.model_path = model_path
        self.model = None
        self.encoders = {}
        self.is_loaded = False
        self.error_handler = get_error_handler()

    @abstractmethod
    def load(self) -> bool:
        """Load the model and its dependencies."""
        pass

    @abstractmethod
    def predict(self, inputs: Dict[str, Any]) -> PredictionResult:
        """Make a prediction using the model."""
        pass

    def unload(self) -> None:
        """Unload the model to free memory."""
        self.model = None
        self.encoders = {}
        self.is_loaded = False


class VINModel(BaseModel):
    """Model for VIN-related predictions (maker, year, series)."""

    @handle_exceptions(category=ErrorCategory.MODEL_LOADING, severity=ErrorSeverity.HIGH)
    def load(self) -> bool:
        """Load VIN prediction model and encoders."""
        try:
            # Load the main model - use correct file naming convention
            model_file = f"{self.model_type.value}_model.joblib"
            full_path = os.path.join(self.model_path, model_file)

            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Model file not found: {full_path}")

            self.model = joblib.load(full_path)

            # Load encoders - use correct file naming convention
            encoder_x_file = f"{self.model_type.value}_encoder_x.joblib"
            encoder_y_file = f"{self.model_type.value}_encoder_y.joblib"

            encoder_x_path = os.path.join(self.model_path, encoder_x_file)
            encoder_y_path = os.path.join(self.model_path, encoder_y_file)

            if os.path.exists(encoder_x_path):
                self.encoders['x'] = joblib.load(encoder_x_path)

            if os.path.exists(encoder_y_path):
                self.encoders['y'] = joblib.load(encoder_y_path)

            self.is_loaded = True
            return True

        except Exception as e:
            # Log the error but don't show popup during startup
            self.error_handler.handle_error(
                e,
                f"loading {self.model_type.value} model",
                ErrorCategory.MODEL_LOADING,
                ErrorSeverity.MEDIUM,
                show_user=False  # Don't show popup during model loading
            )
            return False

    def predict(self, inputs: Dict[str, Any]) -> PredictionResult:
        """Make a VIN prediction."""
        if not self.is_loaded:
            return PredictionResult(
                success=False,
                error_message="Model not loaded",
                model_type=self.model_type
            )

        try:
            features = inputs.get('features')
            if features is None:
                raise ValueError("Features not provided for VIN prediction")

            # Prepare features based on model type (matching original implementation)
            import numpy as np

            if self.model_type == ModelType.VIN_MAKER:
                # Maker uses only WMI
                feature_array = np.array([[features['wmi']]])
                encoded_features = self.encoders['x'].transform(feature_array)

                # Check for unknown category
                if -1 in encoded_features:
                    return PredictionResult(
                        success=True,
                        prediction="Unknown (WMI)",
                        model_type=self.model_type
                    )

            elif self.model_type == ModelType.VIN_YEAR:
                # Year uses only year_code
                feature_array = np.array([[features['year_code']]])
                encoded_features = self.encoders['x'].transform(feature_array)

                # Check for unknown category
                if -1 in encoded_features:
                    return PredictionResult(
                        success=True,
                        prediction="Unknown (Code)",
                        model_type=self.model_type
                    )

            elif self.model_type == ModelType.VIN_SERIES:
                # Series uses WMI and VDS_full
                feature_array = np.array([[features['wmi'], features['vds_full']]])
                encoded_features = self.encoders['x'].transform(feature_array)

                # Check for unknown category
                if -1 in encoded_features[0]:
                    return PredictionResult(
                        success=True,
                        prediction="Unknown (VDS/WMI)",
                        model_type=self.model_type
                    )
            else:
                raise ValueError(f"Unknown VIN model type: {self.model_type}")

            # Make prediction
            prediction_encoded = self.model.predict(encoded_features)

            # Check for unknown prediction
            if prediction_encoded[0] == -1:
                return PredictionResult(
                    success=True,
                    prediction="Unknown (Prediction)",
                    model_type=self.model_type
                )

            # Decode prediction
            if 'y' in self.encoders:
                decoded_prediction = self.encoders['y'].inverse_transform(
                    prediction_encoded.reshape(-1, 1)
                )[0]
            else:
                decoded_prediction = prediction_encoded[0]

            return PredictionResult(
                success=True,
                prediction=decoded_prediction,
                model_type=self.model_type
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                f"making {self.model_type.value} prediction",
                ErrorCategory.PREDICTION,
                ErrorSeverity.MEDIUM,
                show_user=False  # Don't show popup for prediction errors
            )
            return PredictionResult(
                success=False,
                error_message=str(e),
                model_type=self.model_type
            )


class SKUNNModel(BaseModel):
    """PyTorch neural network model for SKU prediction."""

    @handle_exceptions(category=ErrorCategory.MODEL_LOADING, severity=ErrorSeverity.HIGH)
    def load(self) -> bool:
        """Load SKU NN model and all its components."""
        try:
            # Import PyTorch model functions
            try:
                from models.sku_nn_pytorch import load_model
            except ImportError:
                from ..models.sku_nn_pytorch import load_model

            # Load the model and encoders
            model_data = load_model(self.model_path)

            if model_data is None or model_data[0] is None:
                raise RuntimeError("Failed to load SKU NN model")

            # The load_model function returns (model, encoders) tuple
            self.model, encoders_dict = model_data

            if encoders_dict is None:
                raise RuntimeError("Failed to load SKU NN encoders")

            # Map the encoders to the expected format
            self.encoders = {
                'Make': encoders_dict['Make'],
                'Model Year': encoders_dict['Model Year'],
                'Series': encoders_dict['Series'],
                'tokenizer': encoders_dict['tokenizer'],
                'sku': encoders_dict['sku']
            }

            self.is_loaded = True
            return True

        except Exception as e:
            self.error_handler.handle_model_error(
                "SKU NN",
                "loading",
                e
            )
            return False

    def predict(self, inputs: Dict[str, Any]) -> PredictionResult:
        """Make SKU prediction using neural network."""
        if not self.is_loaded:
            return PredictionResult(
                success=False,
                error_message="SKU NN model not loaded",
                model_type=self.model_type
            )

        try:
            # Import prediction function
            try:
                from models.sku_nn_pytorch import predict_sku
            except ImportError:
                from ..models.sku_nn_pytorch import predict_sku

            # Extract inputs
            make = inputs.get('make', '')
            model_year = inputs.get('model_year', '')
            series = inputs.get('series', '')
            description = inputs.get('description', '')

            # Make prediction
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            predicted_sku, confidence = predict_sku(
                model=self.model,
                encoders=self.encoders,
                make=make,
                model_year=model_year,
                series=series,
                description=description,
                device=device
            )

            return PredictionResult(
                success=True,
                prediction=predicted_sku,
                confidence=confidence,
                model_type=self.model_type
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                "making SKU NN prediction",
                ErrorCategory.PREDICTION,
                ErrorSeverity.MEDIUM
            )
            return PredictionResult(
                success=False,
                error_message=str(e),
                model_type=self.model_type
            )


class ModelManager:
    """Centralized model management with lazy loading and caching."""

    def __init__(self):
        self.config = get_config()
        self.error_handler = get_error_handler()
        self.models: Dict[ModelType, BaseModel] = {}
        self.model_info: Dict[ModelType, ModelInfo] = {}
        self._loading_locks: Dict[ModelType, threading.Lock] = {}

        # Initialize locks for thread-safe loading
        for model_type in ModelType:
            self._loading_locks[model_type] = threading.Lock()

    def _create_model(self, model_type: ModelType) -> BaseModel:
        """Create a model instance based on type."""
        if model_type in [ModelType.VIN_MAKER, ModelType.VIN_YEAR, ModelType.VIN_SERIES]:
            return VINModel(model_type, self.config.paths.vin_model_dir)
        elif model_type == ModelType.SKU_NN:
            return SKUNNModel(model_type, self.config.paths.sku_nn_model_dir)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def load_model(self, model_type: ModelType, force_reload: bool = False) -> bool:
        """Load a model with thread-safe lazy loading."""
        with self._loading_locks[model_type]:
            # Check if already loaded
            if model_type in self.models and not force_reload:
                return self.models[model_type].is_loaded

            # Update status
            self.model_info[model_type] = ModelInfo(
                model_type=model_type,
                model_path="",
                status=ModelStatus.LOADING
            )

            try:
                # Create and load model
                model = self._create_model(model_type)
                success = model.load()

                if success:
                    self.models[model_type] = model
                    self.model_info[model_type].status = ModelStatus.LOADED
                    self.model_info[model_type].model_path = model.model_path
                    return True
                else:
                    self.model_info[model_type].status = ModelStatus.ERROR
                    self.model_info[model_type].error_message = "Failed to load model"
                    return False

            except Exception as e:
                self.model_info[model_type].status = ModelStatus.ERROR
                self.model_info[model_type].error_message = str(e)
                self.error_handler.handle_model_error(
                    model_type.value,
                    "loading",
                    e
                )
                return False

    def predict(self, model_type: ModelType, inputs: Dict[str, Any]) -> PredictionResult:
        """Make a prediction using the specified model."""
        # Ensure model is loaded
        if model_type not in self.models or not self.models[model_type].is_loaded:
            if not self.load_model(model_type):
                return PredictionResult(
                    success=False,
                    error_message=f"Failed to load {model_type.value} model",
                    model_type=model_type
                )

        return self.models[model_type].predict(inputs)

    def unload_model(self, model_type: ModelType) -> None:
        """Unload a specific model to free memory."""
        if model_type in self.models:
            self.models[model_type].unload()
            del self.models[model_type]
            self.model_info[model_type].status = ModelStatus.NOT_LOADED

    def unload_all_models(self) -> None:
        """Unload all models to free memory."""
        for model_type in list(self.models.keys()):
            self.unload_model(model_type)

    def get_model_status(self, model_type: ModelType) -> ModelStatus:
        """Get the current status of a model."""
        if model_type in self.model_info:
            return self.model_info[model_type].status
        return ModelStatus.NOT_LOADED

    def get_loaded_models(self) -> List[ModelType]:
        """Get list of currently loaded models."""
        return [
            model_type for model_type, model in self.models.items()
            if model.is_loaded
        ]

    def get_model_info(self) -> Dict[ModelType, ModelInfo]:
        """Get information about all models."""
        return self.model_info.copy()


# Global model manager instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
