"""AutoML model training using FLAML."""

import pandas as pd
import numpy as np
from flaml import AutoML
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    r2_score, mean_squared_error, mean_absolute_error
)
from typing import Dict, Tuple
import time


def train_automl_model(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    problem_type: str,
    time_budget: int = 300
) -> Tuple[AutoML, Dict, Dict]:
    """
    Train AutoML model using FLAML
    
    Args:
        X_train: Training features
        X_test: Test features
        y_train: Training target
        y_test: Test target
        problem_type: 'classification' or 'regression'
        time_budget: Time budget in seconds
    
    Returns:
        model: Trained FLAML model
        metrics: Dictionary of evaluation metrics
        feature_importance: Dictionary of feature importances
    """
    print(f"Training {problem_type} model with FLAML...")
    print(f"Time budget: {time_budget} seconds")
    
    # Initialize AutoML
    automl = AutoML()
    
    # Detect if multiclass classification
    n_classes = y_train.nunique()
    is_multiclass = problem_type == 'classification' and n_classes > 2
    
    print(f"Number of classes: {n_classes}")
    if is_multiclass:
        print(f"Detected multiclass classification ({n_classes} classes)")
    
    # Configure settings based on problem type
    if problem_type == 'classification':
        task = 'classification'
        # Use 'accuracy' for multiclass to avoid binary average issues
        # Alternatively, 'log_loss' or 'micro_f1' work well for multiclass
        metric = 'accuracy' if is_multiclass else 'f1'
    else:
        task = 'regression'
        metric = 'r2'
    
    print(f"Using metric: {metric}")
    
    # Start training
    start_time = time.time()
    
    automl.fit(
        X_train=X_train,
        y_train=y_train,
        task=task,
        metric=metric,
        time_budget=time_budget,
        # XGBoost re-enabled: bug fixed in FLAML v2.1.1+ (Oct 2023)
        # Previous issue: AttributeError 'best_iteration' without early stopping
        estimator_list=['lgbm', 'xgb', 'rf', 'extra_tree'],
        verbose=1,
        log_file_name='flaml_training.log',
        early_stop=True,  # Stop early if search converges (saves time/compute)
        retrain_full=True  # Retrain best model on full training data after search
    )
    
    training_time = time.time() - start_time
    print(f"Training completed in {training_time:.2f} seconds")
    print(f"Best model: {automl.best_estimator}")
    print(f"Best config: {automl.best_config}")
    
    # Make predictions
    y_pred = automl.predict(X_test)
    
    # Calculate metrics
    if problem_type == 'classification':
        metrics = calculate_classification_metrics(y_test, y_pred)
    else:
        metrics = calculate_regression_metrics(y_test, y_pred)
    
    metrics['training_time'] = training_time
    metrics['best_estimator'] = automl.best_estimator
    
    # Get feature importance
    feature_importance = get_feature_importance(automl, X_train.columns)
    
    return automl, metrics, feature_importance


def calculate_classification_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate classification metrics"""
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'f1_score': f1_score(y_true, y_pred, average='weighted'),
        'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0)
    }
    
    print("\nClassification Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    return metrics


def calculate_regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate regression metrics"""
    mse = mean_squared_error(y_true, y_pred)
    metrics = {
        'r2_score': r2_score(y_true, y_pred),
        'rmse': np.sqrt(mse),
        'mae': mean_absolute_error(y_true, y_pred)
    }
    
    print("\nRegression Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    return metrics


def get_feature_importance(model: AutoML, feature_names: pd.Index) -> Dict[str, float]:
    """Extract feature importance from the model"""
    try:
        # Try to get feature importances from the underlying model
        best_model = model.model
        
        # For tree-based models, try to get feature_importances_
        if hasattr(best_model, 'feature_importances_'):
            try:
                importances = best_model.feature_importances_
                feature_importance = dict(zip(feature_names, importances.tolist()))
                
                # Sort by importance
                feature_importance = dict(
                    sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
                )
                
                print("\nTop 10 Feature Importances:")
                for i, (feature, importance) in enumerate(list(feature_importance.items())[:10]):
                    print(f"  {i+1}. {feature}: {importance:.4f}")
                
                return feature_importance
            except AttributeError as e:
                # Handle 'best_iteration' error from LightGBM without early stopping
                print(f"Could not extract feature importances directly: {str(e)}")
        
        # Fallback: Try to get feature importance from FLAML's feature_importances_ method
        if hasattr(model, 'feature_importances_'):
            try:
                importances = model.feature_importances_
                if importances is not None:
                    feature_importance = dict(zip(feature_names, importances.tolist()))
                    feature_importance = dict(
                        sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
                    )
                    
                    print("\nTop 10 Feature Importances (from FLAML):")
                    for i, (feature, importance) in enumerate(list(feature_importance.items())[:10]):
                        print(f"  {i+1}. {feature}: {importance:.4f}")
                    
                    return feature_importance
            except (AttributeError, TypeError) as e:
                print(f"Could not extract feature importances from model: {e}")
        
        # Fallback: Create equal importance for all features
        print("\nCould not extract feature importances, using equal weights")
        equal_importance = 1.0 / len(feature_names)
        return {name: equal_importance for name in feature_names}
        
    except Exception as e:
        print(f"Error extracting feature importance: {str(e)}")
        # Return equal importance as fallback
        equal_importance = 1.0 / len(feature_names) if len(feature_names) > 0 else 0
        return {name: equal_importance for name in feature_names}
