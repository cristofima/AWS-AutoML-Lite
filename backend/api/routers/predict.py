"""
Prediction router for serverless model inference using ONNX Runtime.

This module provides a cost-effective alternative to SageMaker endpoints
by loading ONNX models into Lambda memory and serving predictions.

Key features:
- Models are cached in Lambda memory for fast subsequent predictions
- Only deployed models can be used for inference
- Supports both classification and regression models
"""

from fastapi import APIRouter, HTTPException, status
import logging
import time
from typing import Dict, Any
import numpy as np
import tempfile
import os

from ..models.schemas import PredictionInput, PredictionResponse
from ..services.dynamo_service import dynamodb_service
from ..services.s3_service import s3_service
from ..utils.helpers import get_settings

router = APIRouter(prefix="/predict", tags=["predict"])
settings = get_settings()
logger = logging.getLogger(__name__)

# In-memory LRU cache for loaded ONNX models
# Limits cache to MAX_CACHED_MODELS to prevent unbounded memory growth
# in long-lived Lambda containers that may predict against many different models
MAX_CACHED_MODELS = 3
# Key: job_id, Value: (ort.InferenceSession, model_metadata)
_model_cache: Dict[str, tuple] = {}


def _get_onnx_runtime() -> Any:
    """Lazy load ONNX Runtime to avoid import errors at startup."""
    try:
        import onnxruntime as ort
        return ort
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ONNX Runtime not available: {str(e)}"
        )


def _get_cached_model(job_id: str, onnx_path: str) -> Any:
    """
    Get ONNX model from cache or load from S3.
    
    Args:
        job_id: The job ID to cache the model under
        onnx_path: S3 path to the ONNX model (s3://bucket/key)
    
    Returns:
        ONNX InferenceSession ready for predictions
    """
    if job_id in _model_cache:
        return _model_cache[job_id][0]
    
    ort = _get_onnx_runtime()
    
    # Download model from S3
    onnx_path_clean = onnx_path.replace('s3://', '')
    bucket, key = onnx_path_clean.split('/', 1)
    
    # Download to temp file
    with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        s3_service.download_file(bucket, key, tmp_path)
        
        # Load ONNX model
        session = ort.InferenceSession(
            tmp_path,
            providers=['CPUExecutionProvider']
        )
        
        # Cache the model
        _model_cache[job_id] = (session, {'path': onnx_path})
        
        return session
    finally:
        # Clean up temp file
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError as e:
            logger.warning(
                f"Failed to clean up temp file {tmp_path}: {e}. "
                "This may cause /tmp pollution in Lambda."
            )


def _encode_categorical_features(
    features: Dict[str, Any],
    categorical_mappings: Dict[str, Dict[str, int]]
) -> Dict[str, Any]:
    """
    Encode categorical features using the stored mappings from training.
    
    Args:
        features: Dictionary of feature name -> value (may be strings)
        categorical_mappings: Dict of column -> {original_value: encoded_int}
    
    Returns:
        Dictionary with categorical features encoded as integers
    """
    encoded = features.copy()
    
    for col, mapping in categorical_mappings.items():
        if col in encoded:
            original_value = str(encoded[col])
            if original_value in mapping:
                encoded[col] = mapping[original_value]
            else:
                # Unknown category - use -1 as fallback to avoid failing the entire prediction
                encoded[col] = -1
    
    return encoded


def _prepare_input(
    features: Dict[str, Any],
    feature_columns: list,
    session: Any,
    preprocessing_info: Dict[str, Any] | None = None
) -> np.ndarray:
    """
    Prepare input features for ONNX model inference.
    
    Args:
        features: Dictionary of feature name -> value
        feature_columns: Expected feature columns in order
        session: ONNX session (to get input type info)
        preprocessing_info: Contains categorical_mappings for encoding
    
    Returns:
        Numpy array ready for inference
    """
    # Encode categorical features if mappings are provided
    if preprocessing_info and preprocessing_info.get('categorical_mappings'):
        features = _encode_categorical_features(
            features,
            preprocessing_info['categorical_mappings']
        )
    
    # Get expected input shape and type
    input_info = session.get_inputs()[0]
    input_type = input_info.type
    
    # Build feature vector in correct order
    feature_vector = []
    for col in feature_columns:
        if col not in features:
            raise ValueError(f"Missing required feature: {col}")
        value = features[col]
        # Ensure numeric conversion for non-categorical columns
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{value}' to number for feature '{col}'")
        feature_vector.append(value)
    
    # Convert to numpy array with appropriate type
    if 'float' in input_type:
        return np.array([feature_vector], dtype=np.float32)
    else:
        return np.array([feature_vector], dtype=np.float64)


@router.post("/{job_id}", response_model=PredictionResponse)
async def make_prediction(job_id: str, request: PredictionInput) -> PredictionResponse:
    """
    Make a prediction using a deployed ONNX model.
    
    The model must be deployed first using POST /jobs/{job_id}/deploy.
    Input features must match the model's expected features.
    
    Returns prediction, probabilities (for classification), and inference time.
    """
    start_time = time.time()
    
    try:
        # Get job details
        job = dynamodb_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if model is deployed
        if not job.get('deployed', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not deployed. Deploy the model first using POST /jobs/{job_id}/deploy"
            )
        
        # Check if ONNX model exists
        if not job.get('onnx_model_path'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ONNX model available for this job"
            )
        
        # Get preprocessing info for feature order
        preprocessing_info = job.get('preprocessing_info', {})
        feature_columns = preprocessing_info.get('feature_columns', [])
        
        if not feature_columns:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model metadata missing feature columns information"
            )
        
        # Validate input features
        missing_features = [col for col in feature_columns if col not in request.features]
        if missing_features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required features: {missing_features}"
            )
        
        # Load model (from cache or S3)
        session = _get_cached_model(job_id, job['onnx_model_path'])
        
        # Prepare input (with categorical encoding)
        try:
            input_data = _prepare_input(
                request.features,
                feature_columns,
                session,
                preprocessing_info
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Get input name
        input_name = session.get_inputs()[0].name
        output_names = [o.name for o in session.get_outputs()]
        
        # Run inference
        outputs = session.run(output_names, {input_name: input_data})
        
        # Parse results based on problem type
        problem_type = job.get('problem_type', 'classification')
        
        if problem_type == 'regression':
            prediction = float(outputs[0][0])
            probability = None
            probabilities = None
        else:
            # Classification
            prediction = outputs[0][0]
            
            # Handle different output formats
            if isinstance(prediction, (np.integer, int)):
                prediction = int(prediction)
            elif isinstance(prediction, (np.floating, float)):
                prediction = float(prediction)
            else:
                prediction = str(prediction)
            
            # Get probabilities if available (usually second output)
            probability = None
            probabilities = None
            if len(outputs) > 1:
                probs = outputs[1][0]
                if isinstance(probs, dict):
                    # ONNX returns dict for LightGBM
                    probabilities = {str(k): float(v) for k, v in probs.items()}
                    probability = max(probabilities.values()) if probabilities else None
                elif hasattr(probs, '__iter__'):
                    # Array of probabilities
                    prob_list = [float(p) for p in probs]
                    probability = max(prob_list)
                    probabilities = {str(i): p for i, p in enumerate(prob_list)}
        
        inference_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return PredictionResponse(
            job_id=job_id,
            prediction=prediction,
            probability=probability,
            probabilities=probabilities,
            inference_time_ms=round(inference_time, 2),
            model_type=job.get('metrics', {}).get('best_estimator', 'unknown')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@router.get("/{job_id}/info")
async def get_prediction_info(job_id: str) -> dict:
    """
    Get information about a deployed model for making predictions.
    
    Returns the required input features, their types, and example values.
    Useful for building prediction forms or understanding model inputs.
    """
    try:
        # Get job details
        job = dynamodb_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if model is deployed
        if not job.get('deployed', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not deployed"
            )
        
        preprocessing_info = job.get('preprocessing_info', {})
        feature_columns = preprocessing_info.get('feature_columns', [])
        feature_types = preprocessing_info.get('feature_types', {})
        categorical_mappings = preprocessing_info.get('categorical_mappings', {})
        
        # Build feature info with type and allowed values
        feature_info = {}
        for col in feature_columns:
            col_type = feature_types.get(col, 'numeric')
            info = {
                "type": col_type,
                "input_type": "select" if col_type == "categorical" else "number"
            }
            if col_type == "categorical" and col in categorical_mappings:
                info["allowed_values"] = list(categorical_mappings[col].keys())
            feature_info[col] = info
        
        return {
            "job_id": job_id,
            "problem_type": job.get('problem_type'),
            "target_column": job.get('target_column'),
            "dataset_name": job.get('dataset_name'),
            "feature_columns": feature_columns,
            "feature_count": len(feature_columns),
            "feature_info": feature_info,
            "model_type": job.get('metrics', {}).get('best_estimator', 'unknown'),
            "deployed": True,
            "example_request": {
                "features": {
                    col: (
                        list(categorical_mappings[col].keys())[0] 
                        if col in categorical_mappings 
                        else 0
                    )
                    for col in feature_columns
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prediction info: {str(e)}"
        )
