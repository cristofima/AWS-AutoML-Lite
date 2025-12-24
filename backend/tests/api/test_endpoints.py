"""
API endpoint tests using FastAPI TestClient.

These tests verify that API endpoints respond correctly
without requiring actual AWS services.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add API module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.api
    def test_root_endpoint(self, api_client):
        """GET / returns healthy status."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "message" in data
    
    @pytest.mark.api
    def test_health_check(self, api_client):
        """GET /health returns detailed health info."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "automl-api"
        assert "region" in data


class TestDocsEndpoints:
    """Test API documentation endpoints."""
    
    @pytest.mark.api
    def test_openapi_schema(self, api_client):
        """OpenAPI schema is accessible."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "AWS AutoML Lite API"
    
    @pytest.mark.api
    def test_docs_endpoint(self, api_client):
        """Swagger UI docs endpoint is accessible."""
        response = api_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_redoc_endpoint(self, api_client):
        """ReDoc endpoint is accessible."""
        response = api_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestUploadEndpoint:
    """Test upload endpoint."""
    
    @pytest.mark.api
    @patch('api.routers.upload.s3_service')
    def test_upload_valid_csv(self, mock_s3_service, api_client):
        """POST /upload with valid CSV filename returns presigned URL."""
        # Configure mock
        mock_s3_service.generate_presigned_upload_url.return_value = "https://s3.amazonaws.com/presigned"
        
        response = api_client.post(
            "/upload",
            json={"filename": "data.csv", "content_type": "text/csv"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
        assert "upload_url" in data
        assert data["upload_url"] == "https://s3.amazonaws.com/presigned"
    
    @pytest.mark.api
    def test_upload_missing_filename(self, api_client):
        """POST /upload without filename returns 422."""
        response = api_client.post("/upload", json={})
        assert response.status_code == 422
    
    @pytest.mark.api
    @patch('api.routers.upload.s3_service')
    def test_upload_with_content_type(self, mock_s3_service, api_client):
        """POST /upload with content_type is accepted."""
        mock_s3_service.generate_presigned_upload_url.return_value = "https://s3.amazonaws.com/presigned"
        
        response = api_client.post(
            "/upload",
            json={"filename": "data.csv", "content_type": "text/csv"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "expires_in" in data
        assert data["expires_in"] > 0


class TestDatasetsEndpoint:
    """Test datasets endpoint."""
    
    @pytest.mark.api
    def test_get_dataset_found(self, api_client):
        """GET /datasets/{id} returns dataset when found."""
        from api.routers import datasets
        
        mock_data = {
            'dataset_id': 'test-123',
            'filename': 'test.csv',
            'file_size': 1024,
            'uploaded_at': '2024-01-15T10:30:00Z',
            'columns': ['id', 'name', 'price'],
            'row_count': 100,
            'column_types': {'id': 'int64', 'name': 'object', 'price': 'float64'}
        }
        
        with patch.object(datasets.dynamodb_service, 'get_dataset_metadata', return_value=mock_data):
            response = api_client.get("/datasets/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == "test-123"
        assert data["filename"] == "test.csv"
    
    @pytest.mark.api
    def test_get_dataset_not_found(self, api_client):
        """GET /datasets/{id} returns 404 when not found."""
        from api.routers import datasets
        
        with patch.object(datasets.dynamodb_service, 'get_dataset_metadata', return_value=None):
            response = api_client.get("/datasets/nonexistent")
        
        assert response.status_code == 404


class TestTrainingEndpoint:
    """Test training endpoint."""
    
    @pytest.mark.api
    def test_start_training_valid(self, api_client):
        """POST /train with valid data starts training job."""
        from api.routers import training
        
        # Mock dataset exists
        mock_dataset = {
            'dataset_id': 'dataset-123',
            'filename': 'test.csv',
            'status': 'confirmed',
            'columns': ['id', 'feature', 'price'],
            'row_count': 100,
        }
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=mock_dataset), \
             patch.object(training.dynamodb_service, 'create_job', return_value=None), \
             patch.object(training.dynamodb_service, 'update_job_status', return_value=None), \
             patch.object(training.batch_service, 'submit_training_job', return_value="arn:aws:batch:job/12345"):
            
            response = api_client.post(
                "/train",
                json={
                    "dataset_id": "dataset-123",
                    "target_column": "price"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
    
    @pytest.mark.api
    def test_start_training_missing_fields(self, api_client):
        """POST /train without required fields returns 422."""
        response = api_client.post(
            "/train",
            json={"dataset_id": "abc"}  # Missing target_column
        )
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_start_training_invalid_time_budget(self, api_client):
        """POST /train with invalid time_budget returns 422."""
        response = api_client.post(
            "/train",
            json={
                "dataset_id": "dataset-123",
                "target_column": "price",
                "config": {"time_budget": 10}  # Too low (min is 60)
            }
        )
        assert response.status_code == 422


class TestJobsEndpoint:
    """Test jobs endpoint."""
    
    @pytest.mark.api
    def test_get_job_found(self, api_client):
        """GET /jobs/{id} returns job when found."""
        from api.routers import training
        
        mock_job = {
            'job_id': 'job-123',
            'dataset_id': 'dataset-456',
            'status': 'running',
            'target_column': 'price',
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:35:00Z'
        }
        
        with patch.object(training.dynamodb_service, 'get_job', return_value=mock_job):
            response = api_client.get("/jobs/job-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "running"
    
    @pytest.mark.api
    def test_get_job_not_found(self, api_client):
        """GET /jobs/{id} returns 404 when not found."""
        from api.routers import training
        
        with patch.object(training.dynamodb_service, 'get_job', return_value=None):
            response = api_client.get("/jobs/nonexistent")
        
        assert response.status_code == 404


class TestPredictEndpoint:
    """Test prediction endpoint."""
    
    @pytest.mark.api
    @patch('api.routers.predict.dynamodb_service')
    @patch('api.routers.predict.s3_service')
    def test_predict_requires_deployed_model(self, mock_s3, mock_dynamo, api_client):
        """POST /predict/{job_id} requires model to be deployed."""
        mock_dynamo.get_job.return_value = {
            'job_id': 'job-123',
            'status': 'completed',
            'deployed': False  # Not deployed
        }
        
        response = api_client.post(
            "/predict/job-123",
            json={"features": {"age": 25, "income": 50000}}
        )
        
        # Should return error because model not deployed
        assert response.status_code in [400, 404]
    
    @pytest.mark.api
    def test_predict_missing_features(self, api_client):
        """POST /predict without features returns 422."""
        response = api_client.post(
            "/predict/job-123",
            json={}
        )
        assert response.status_code == 422
    
    @pytest.mark.api
    @patch('api.routers.predict.dynamodb_service')
    def test_predict_job_not_found(self, mock_dynamo, api_client):
        """POST /predict for non-existent job returns 404."""
        mock_dynamo.get_job.return_value = None
        
        response = api_client.post(
            "/predict/nonexistent",
            json={"features": {"age": 25}}
        )
        
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
