"""
API-specific pytest fixtures.

This module contains fixtures used only by API tests.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Add backend/api to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "api"))


# =============================================================================
# Environment Setup Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_api_test_environment():
    """Set up environment variables for API tests."""
    test_env = {
        'AWS_REGION': 'us-east-1',
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'S3_BUCKET_DATASETS': 'test-datasets-bucket',
        'S3_BUCKET_MODELS': 'test-models-bucket',
        'S3_BUCKET_REPORTS': 'test-reports-bucket',
        'DYNAMODB_DATASETS_TABLE': 'test-datasets-table',
        'DYNAMODB_JOBS_TABLE': 'test-jobs-table',
        'CORS_ORIGINS': '["http://localhost:3000"]',  # JSON format for list
        'BATCH_JOB_DEFINITION': 'test-job-def',
        'BATCH_JOB_QUEUE': 'test-job-queue',
    }
    
    # Store original values for cleanup
    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value  # Force set (overwrite any existing)
    
    yield
    
    # Restore original values
    for key, original in original_values.items():
        if original is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original


# =============================================================================
# API Test Fixtures
# =============================================================================

@pytest.fixture
def api_client(setup_api_test_environment):
    """Create FastAPI test client with mocked dependencies."""
    # Clear the settings cache before importing app
    from api.utils.helpers import get_settings
    get_settings.cache_clear()
    
    from fastapi.testclient import TestClient
    from api.main import app
    
    return TestClient(app)


@pytest.fixture
def mock_dynamo_service():
    """Mock DynamoDB service for API tests."""
    mock_service = MagicMock()
    mock_service.get_dataset.return_value = {
        'dataset_id': 'test-dataset-123',
        'filename': 'test.csv',
        'status': 'confirmed',
        'row_count': 100,
        'column_count': 5,
        'columns': ['id', 'feature1', 'feature2', 'target'],
    }
    mock_service.get_job.return_value = {
        'job_id': 'test-job-123',
        'status': 'SUCCEEDED',
        'dataset_id': 'test-dataset-123',
        'target_column': 'target',
        'metrics': {'accuracy': 0.95, 'f1_score': 0.94},
    }
    return mock_service


@pytest.fixture
def mock_s3_service():
    """Mock S3 service for API tests."""
    mock_service = MagicMock()
    mock_service.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
    mock_service.generate_presigned_download_url.return_value = 'https://s3.amazonaws.com/presigned-download-url'
    mock_service.generate_presigned_download_url_cached.return_value = 'https://s3.amazonaws.com/presigned-download-url'
    mock_service.get_object.return_value = b'id,feature,target\n1,a,0\n2,b,1'
    return mock_service
