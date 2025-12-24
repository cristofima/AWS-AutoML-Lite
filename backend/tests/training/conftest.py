"""
Training-specific pytest fixtures.

This module contains fixtures used only by training tests.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add backend/training to path for imports
# Path: tests/training/conftest.py -> backend/training
backend_path = Path(__file__).parent.parent.parent
training_path = backend_path / "training"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(training_path))


# =============================================================================
# Environment Setup Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_training_test_environment():
    """Set up environment variables for training tests."""
    test_env = {
        'AWS_REGION': 'us-east-1',
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'S3_BUCKET_DATASETS': 'test-datasets-bucket',
        'S3_BUCKET_MODELS': 'test-models-bucket',
        'S3_BUCKET_REPORTS': 'test-reports-bucket',
        'DYNAMODB_JOBS_TABLE': 'test-jobs-table',
    }
    
    # Store original values for cleanup
    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original in original_values.items():
        if original is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original


# =============================================================================
# DataFrame Fixtures
# =============================================================================

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Sample DataFrame for testing preprocessing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005', 
                        'C006', 'C007', 'C008', 'C009', 'C010'],
        'age': [25, 30, 35, 40, 45, 28, 33, 38, 42, 50],
        'income': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0,
                   55000.0, 65000.0, 75000.0, 85000.0, 95000.0],
        'category': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C'],
        'constant_col': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'target': [0, 1, 0, 1, 1, 0, 1, 0, 1, 0]
    })


@pytest.fixture
def classification_binary_target() -> pd.Series:
    """Binary classification target (0/1)."""
    return pd.Series([0, 1, 0, 1, 1, 0, 1, 0, 0, 1], name='target')


@pytest.fixture
def classification_multiclass_target() -> pd.Series:
    """Multi-class classification target."""
    return pd.Series([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], name='target')


@pytest.fixture
def classification_string_target() -> pd.Series:
    """String classification target."""
    return pd.Series(['cat', 'dog', 'bird', 'cat', 'dog', 
                      'bird', 'cat', 'dog', 'cat', 'bird'], name='target')


@pytest.fixture
def regression_target() -> pd.Series:
    """Continuous regression target."""
    return pd.Series([35.5, 42.1, 38.7, 41.2, 50.8, 
                      33.4, 45.6, 39.2, 44.1, 37.8], name='target')


@pytest.fixture
def regression_price_target() -> pd.Series:
    """Price-like regression target."""
    return pd.Series([199.99, 249.50, 89.99, 349.00, 129.95,
                      179.99, 299.00, 99.50, 449.00, 159.95], name='price')


# =============================================================================
# Column Detection Fixtures
# =============================================================================

@pytest.fixture
def id_column_samples() -> dict[str, pd.Series]:
    """Sample ID columns with various patterns."""
    return {
        'id': pd.Series([1, 2, 3, 4, 5]),
        'customer_id': pd.Series([101, 102, 103, 104, 105]),
        'user_id': pd.Series(['U001', 'U002', 'U003', 'U004', 'U005']),
        'order_id': pd.Series([1001, 1002, 1003, 1004, 1005]),
        'uuid': pd.Series(['abc-123', 'def-456', 'ghi-789', 'jkl-012', 'mno-345']),
        'transaction_id': pd.Series(range(1, 6)),
    }


@pytest.fixture
def non_id_column_samples() -> dict[str, pd.Series]:
    """Sample non-ID columns."""
    return {
        'age': pd.Series([25, 30, 35, 40, 45]),
        'income': pd.Series([50000.0, 60000.0, 70000.0, 80000.0, 90000.0]),
        'price': pd.Series([10.5, 20.5, 30.5, 40.5, 50.5]),
        'category': pd.Series(['A', 'B', 'C', 'A', 'B']),
        'is_active': pd.Series([True, False, True, False, True]),
    }


# =============================================================================
# Training Fixtures
# =============================================================================

@pytest.fixture
def training_dataframe() -> pd.DataFrame:
    """DataFrame suitable for model training tests."""
    np.random.seed(42)
    n_samples = 100
    
    return pd.DataFrame({
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.choice(['A', 'B', 'C'], n_samples),
        'feature4': np.random.randint(0, 100, n_samples),
        'target': np.random.choice([0, 1], n_samples)
    })


@pytest.fixture
def regression_dataframe() -> pd.DataFrame:
    """DataFrame for regression model training."""
    np.random.seed(42)
    n_samples = 100
    
    X1 = np.random.randn(n_samples)
    X2 = np.random.randn(n_samples)
    # Target with some relationship to features
    y = 3 * X1 + 2 * X2 + np.random.randn(n_samples) * 0.5
    
    return pd.DataFrame({
        'feature1': X1,
        'feature2': X2,
        'feature3': np.random.choice(['Low', 'Medium', 'High'], n_samples),
        'target': y
    })
