"""ONNX model exporter for trained sklearn/FLAML models.

Converts trained models to ONNX format for cross-platform inference.
Supports: sklearn models (Random Forest, Extra Trees) and LightGBM.
"""

import numpy as np
import pandas as pd
from typing import Any

# ONNX imports
try:
    from skl2onnx import to_onnx
    from skl2onnx.common.data_types import FloatTensorType
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

# LightGBM ONNX converter
try:
    from onnxmltools import convert_lightgbm
    from onnxmltools.convert.common.data_types import FloatTensorType as LGBMFloatTensorType
    ONNXMLTOOLS_AVAILABLE = True
except ImportError:
    ONNXMLTOOLS_AVAILABLE = False


def _is_lightgbm_model(model: Any) -> bool:
    """Check if the model is a LightGBM model."""
    model_type = type(model).__name__
    return model_type in ('LGBMClassifier', 'LGBMRegressor', 'LGBMRanker')


def _convert_lightgbm_to_onnx(
    model: Any,
    n_features: int,
    output_path: str
) -> bool:
    """Convert LightGBM model to ONNX using onnxmltools.
    
    Args:
        model: LightGBM model (LGBMClassifier or LGBMRegressor)
        n_features: Number of input features
        output_path: Path to save the .onnx file
    
    Returns:
        True if conversion successful, False otherwise
    """
    if not ONNXMLTOOLS_AVAILABLE:
        print("Warning: onnxmltools not available. LightGBM ONNX export skipped.")
        return False
    
    try:
        # Define initial types for LightGBM
        initial_types = [('input', LGBMFloatTensorType([None, n_features]))]
        
        # Convert to ONNX
        onnx_model = convert_lightgbm(
            model,
            initial_types=initial_types,
            target_opset=15
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        
        return True
        
    except Exception as e:
        print(f"Warning: LightGBM ONNX conversion failed: {e}")
        return False


def _extract_sklearn_model(model: Any) -> Any:
    """Extract the underlying sklearn/lightgbm model from FLAML wrappers.
    
    FLAML wraps models in its own estimator classes (RandomForestEstimator, 
    LGBMEstimator, etc.). This function extracts the actual sklearn/lightgbm
    model that skl2onnx can convert.
    
    Args:
        model: FLAML AutoML instance or any sklearn-compatible model
        
    Returns:
        The underlying sklearn/lightgbm model
    """
    # If it's a FLAML AutoML instance, get the best model
    if hasattr(model, 'model'):
        inner_model = model.model
    else:
        inner_model = model
    
    # FLAML's estimator wrappers have an 'estimator' attribute
    # that contains the actual sklearn/lightgbm model
    if hasattr(inner_model, 'estimator'):
        return inner_model.estimator
    
    # For some FLAML models, the underlying estimator is in '_model'
    if hasattr(inner_model, '_model'):
        return inner_model._model
    
    # If it's already a sklearn model, return as-is
    return inner_model


def export_model_to_onnx(
    model: Any,
    X_sample: pd.DataFrame,
    output_path: str,
    model_name: str = "automl_model"
) -> bool:
    """Export a trained sklearn model to ONNX format.
    
    Args:
        model: Trained sklearn-compatible model (e.g., from FLAML)
        X_sample: Sample input data for shape inference (1 row is enough)
        output_path: Path to save the .onnx file
        model_name: Name for the ONNX model
    
    Returns:
        True if export successful, False otherwise
    
    Note:
        The model must be sklearn-compatible. FLAML's AutoML.model property
        returns the underlying sklearn estimator which can be converted.
        For LightGBM models, we use the onnxmltools converter.
    """
    if not ONNX_AVAILABLE:
        print("Warning: skl2onnx not available. ONNX export skipped.")
        return False
    
    try:
        # Extract the underlying sklearn/lightgbm model from FLAML wrappers
        sklearn_model = _extract_sklearn_model(model)
        
        # Prepare sample data for type inference
        # Need at least 1 row, convert to float32 for ONNX compatibility
        if isinstance(X_sample, pd.DataFrame):
            X_array = X_sample.values.astype(np.float32)
        else:
            X_array = np.array(X_sample).astype(np.float32)
        
        # Take only first row for shape inference
        if len(X_array) > 1:
            X_array = X_array[:1]
        
        n_features = X_array.shape[1]
        
        print(f"Converting model to ONNX format...")
        print(f"  - Model type: {type(sklearn_model).__name__}")
        print(f"  - Input features: {n_features}")
        
        # Check if it's a LightGBM model (requires onnxmltools)
        if _is_lightgbm_model(sklearn_model):
            print("  - Using onnxmltools for LightGBM conversion")
            success = _convert_lightgbm_to_onnx(sklearn_model, n_features, output_path)
            if success:
                print(f"ONNX model saved to: {output_path}")
                _verify_onnx_model(output_path, X_array)
            return success
        
        # For sklearn models, use skl2onnx
        # Define initial types for the input
        # Use None for batch dimension (dynamic batch size)
        initial_types = [("input", FloatTensorType([None, n_features]))]
        
        # Convert to ONNX
        # Options for classifiers: disable zipmap for simpler output structure
        options = None
        if hasattr(sklearn_model, 'predict_proba'):
            # For classifiers, output raw arrays instead of zip maps
            options = {type(sklearn_model): {'zipmap': False}}
        
        onnx_model = to_onnx(
            sklearn_model,
            X_array,
            initial_types=initial_types,
            target_opset=15,  # ONNX opset 15 for broad compatibility
            options=options
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        
        print(f"ONNX model saved to: {output_path}")
        
        # Verify the model can be loaded
        _verify_onnx_model(output_path, X_array)
        
        return True
        
    except Exception as e:
        print(f"Warning: ONNX export failed: {e}")
        print("The model will still be available in PKL format.")
        return False


def _verify_onnx_model(model_path: str, X_sample: np.ndarray) -> None:
    """Verify the ONNX model can be loaded and run inference.
    
    Args:
        model_path: Path to the saved .onnx file
        X_sample: Sample input to test inference
    """
    try:
        import onnxruntime as rt
        
        # Create inference session
        sess = rt.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )
        
        # Get input name
        input_name = sess.get_inputs()[0].name
        
        # Run inference
        outputs = sess.run(None, {input_name: X_sample})
        
        print(f"ONNX model verification passed!")
        print(f"  - Input name: {input_name}")
        print(f"  - Output shapes: {[o.shape for o in outputs]}")
        
    except Exception as e:
        print(f"Warning: ONNX verification failed: {e}")
        print("The ONNX file was saved but may have compatibility issues.")
