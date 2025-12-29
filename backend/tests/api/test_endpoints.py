"""
API endpoint tests using FastAPI TestClient.

These tests verify that API endpoints respond correctly
without requiring actual AWS services.
"""
import pytest
from unittest.mock import patch
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
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-123',
            'dataset_id': 'dataset-456',
            'status': 'running',
            'target_column': 'price',
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:35:00Z'
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job):
            response = api_client.get("/jobs/job-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "running"
    
    @pytest.mark.api
    def test_get_job_not_found(self, api_client):
        """GET /jobs/{id} returns 404 when not found."""
        from api.routers import models
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=None):
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


class TestDatasetConfirmEndpoint:
    """Test dataset confirmation endpoint."""
    
    @pytest.mark.api
    def test_confirm_upload_success(self, api_client):
        """POST /datasets/{id}/confirm processes CSV and returns metadata."""
        from api.routers import datasets
        
        csv_content = b"id,name,price,category\n1,Product A,29.99,Electronics\n2,Product B,49.99,Books\n3,Product C,19.99,Electronics"
        
        with patch.object(datasets.s3_service, 'list_objects', return_value=['datasets/test-123/data.csv']), \
             patch.object(datasets.s3_service, 'download_file_content', return_value=csv_content), \
             patch.object(datasets.dynamodb_service, 'save_dataset_metadata', return_value=True):
            
            response = api_client.post("/datasets/test-123/confirm")
        
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == "test-123"
        assert data["filename"] == "data.csv"
        assert data["row_count"] == 3
        assert "id" in data["columns"]
        assert "price" in data["columns"]
        assert data["column_types"]["price"] == "numeric"
        assert data["column_types"]["category"] == "categorical"
    
    @pytest.mark.api
    def test_confirm_upload_not_found(self, api_client):
        """POST /datasets/{id}/confirm returns 404 when no files found."""
        from api.routers import datasets
        
        with patch.object(datasets.s3_service, 'list_objects', return_value=[]):
            response = api_client.post("/datasets/nonexistent/confirm")
        
        assert response.status_code == 404
        assert "No files found" in response.json()["detail"]
    
    @pytest.mark.api
    def test_confirm_upload_calculates_missing_stats(self, api_client):
        """POST /datasets/{id}/confirm calculates missing value statistics."""
        from api.routers import datasets
        
        # CSV with missing values
        csv_content = b"id,name,price\n1,Product A,29.99\n2,,49.99\n3,Product C,\n4,Product D,19.99"
        
        with patch.object(datasets.s3_service, 'list_objects', return_value=['datasets/test-456/data.csv']), \
             patch.object(datasets.s3_service, 'download_file_content', return_value=csv_content), \
             patch.object(datasets.dynamodb_service, 'save_dataset_metadata', return_value=True):
            
            response = api_client.post("/datasets/test-456/confirm")
        
        assert response.status_code == 200
        data = response.json()
        # name column has 1 missing value
        assert data["column_stats"]["name"]["missing"] == 1
        # price column has 1 missing value
        assert data["column_stats"]["price"]["missing"] == 1


class TestJobsListEndpoint:
    """Test jobs listing endpoint."""
    
    @pytest.mark.api
    def test_list_jobs_success(self, api_client):
        """GET /jobs returns paginated list of jobs."""
        from api.routers import models
        
        # Mock jobs must include all required JobDetails fields
        mock_jobs = [
            {
                'job_id': 'job-001',
                'dataset_id': 'ds-001',
                'user_id': 'default',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:30:00Z',
                'status': 'completed',
                'dataset_name': 'data1.csv',
                'target_column': 'price',
            },
            {
                'job_id': 'job-002',
                'dataset_id': 'ds-002',
                'user_id': 'default',
                'created_at': '2024-01-15T11:00:00Z',
                'updated_at': '2024-01-15T11:30:00Z',
                'status': 'running',
                'dataset_name': 'data2.csv',
                'target_column': 'category',
            }
        ]
        
        with patch.object(models.dynamodb_service, 'list_jobs', return_value=(mock_jobs, None)):
            response = api_client.get("/jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2
        assert data["jobs"][0]["job_id"] == "job-001"
        assert data["next_token"] is None
    
    @pytest.mark.api
    def test_list_jobs_with_limit(self, api_client):
        """GET /jobs?limit=N respects limit parameter."""
        from api.routers import models
        
        # Mock jobs with all required fields
        mock_jobs = [
            {
                'job_id': f'job-{i}',
                'dataset_id': 'ds',
                'user_id': 'default',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:30:00Z',
                'status': 'completed',
                'dataset_name': f'data{i}.csv',
                'target_column': 'x',
            }
            for i in range(5)
        ]
        next_key = {'job_id': 'job-5'}
        
        with patch.object(models.dynamodb_service, 'list_jobs', return_value=(mock_jobs, next_key)):
            response = api_client.get("/jobs?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 5
        assert data["next_token"] is not None


class TestJobDeleteEndpoint:
    """Test job deletion endpoint."""
    
    @pytest.mark.api
    def test_delete_job_success(self, api_client):
        """DELETE /jobs/{id} removes job and associated resources."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-del-001',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'model_path': 's3://test-bucket/models/job-del-001/model.pkl',
            'eda_report_path': 's3://test-bucket/reports/job-del-001/eda.html',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job), \
             patch.object(models.s3_service, 'delete_object', return_value=True), \
             patch.object(models.s3_service, 'delete_folder', return_value=1), \
             patch.object(models.dynamodb_service, 'delete_dataset', return_value=True), \
             patch.object(models.dynamodb_service, 'delete_job', return_value=True):
            
            response = api_client.delete("/jobs/job-del-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-del-001"
        assert "deleted_resources" in data
    
    @pytest.mark.api
    def test_delete_job_not_found(self, api_client):
        """DELETE /jobs/{id} returns 404 for non-existent job."""
        from api.routers import models
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=None):
            response = api_client.delete("/jobs/nonexistent")
        
        assert response.status_code == 404
    
    @pytest.mark.api
    def test_delete_job_without_data(self, api_client):
        """DELETE /jobs/{id}?delete_data=false only removes job record."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-del-002',
            'status': 'completed',
            'dataset_id': 'ds-001',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job), \
             patch.object(models.dynamodb_service, 'delete_job', return_value=True) as mock_delete:
            
            response = api_client.delete("/jobs/job-del-002?delete_data=false")
        
        assert response.status_code == 200
        mock_delete.assert_called_once_with("job-del-002")


class TestJobUpdateEndpoint:
    """Test job metadata update endpoint."""
    
    @pytest.mark.api
    def test_update_job_tags(self, api_client):
        """PATCH /jobs/{id} updates job tags."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-upd-001',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job), \
             patch.object(models.dynamodb_service, 'update_job_metadata', return_value=True):
            
            response = api_client.patch(
                "/jobs/job-upd-001",
                json={"tags": ["experiment-1", "baseline"]}
            )
        
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_update_job_notes(self, api_client):
        """PATCH /jobs/{id} updates job notes."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-upd-002',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job), \
             patch.object(models.dynamodb_service, 'update_job_metadata', return_value=True):
            
            response = api_client.patch(
                "/jobs/job-upd-002",
                json={"notes": "This is a baseline model with default parameters"}
            )
        
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_update_job_too_many_tags(self, api_client):
        """PATCH /jobs/{id} rejects more than 10 tags via Pydantic validation."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-upd-003',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job):
            response = api_client.patch(
                "/jobs/job-upd-003",
                json={"tags": [f"tag-{i}" for i in range(15)]}  # 15 tags > max 10
            )
        
        # Pydantic validates max_items=10, returns 422 Unprocessable Entity
        assert response.status_code == 422


class TestDeployEndpoint:
    """Test model deployment endpoint."""
    
    @pytest.mark.api
    def test_deploy_model_success(self, api_client):
        """POST /jobs/{id}/deploy successfully deploys a completed job."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-deploy-001',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'onnx_model_path': 's3://test-bucket/models/job-deploy-001/model.onnx',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job), \
             patch.object(models.dynamodb_service, 'update_job_deployed', return_value=True):
            
            response = api_client.post(
                "/jobs/job-deploy-001/deploy",
                json={"deploy": True}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deployed"] is True
        assert "successfully deployed" in data["message"]
    
    @pytest.mark.api
    def test_deploy_incomplete_job_fails(self, api_client):
        """POST /jobs/{id}/deploy fails for non-completed jobs."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-deploy-002',
            'status': 'running',
            'dataset_id': 'ds-001',
            'target_column': 'price',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job):
            response = api_client.post(
                "/jobs/job-deploy-002/deploy",
                json={"deploy": True}
            )
        
        assert response.status_code == 400
        assert "Only completed jobs" in response.json()["detail"]
    
    @pytest.mark.api
    def test_deploy_without_onnx_fails(self, api_client):
        """POST /jobs/{id}/deploy fails when no ONNX model available."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-deploy-003',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            # No onnx_model_path
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job):
            response = api_client.post(
                "/jobs/job-deploy-003/deploy",
                json={"deploy": True}
            )
        
        assert response.status_code == 400
        assert "No ONNX model" in response.json()["detail"]
    
    @pytest.mark.api
    def test_undeploy_model_success(self, api_client):
        """POST /jobs/{id}/deploy with deploy=false undeploys model."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-deploy-004',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'deployed': True,
            'onnx_model_path': 's3://test-bucket/models/job-deploy-004/model.onnx',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job), \
             patch.object(models.dynamodb_service, 'update_job_deployed', return_value=True):
            
            response = api_client.post(
                "/jobs/job-deploy-004/deploy",
                json={"deploy": False}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["deployed"] is False
        assert "undeployed" in data["message"]


class TestTrainingEdgeCases:
    """Test training endpoint edge cases and problem type detection."""
    
    @pytest.mark.api
    def test_training_detects_classification_for_categorical(self, api_client):
        """POST /train detects classification for categorical target."""
        from api.routers import training
        
        mock_dataset = {
            'dataset_id': 'dataset-class-001',
            'filename': 'classification.csv',
            'columns': ['id', 'feature1', 'category'],
            'row_count': 1000,
            'column_types': {'id': 'numeric', 'feature1': 'numeric', 'category': 'categorical'},
        }
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=mock_dataset), \
             patch.object(training.dynamodb_service, 'create_job', return_value=None), \
             patch.object(training.dynamodb_service, 'update_job_status', return_value=None), \
             patch.object(training.batch_service, 'submit_training_job', return_value="arn:aws:batch:job/12345"):
            
            response = api_client.post(
                "/train",
                json={"dataset_id": "dataset-class-001", "target_column": "category"}
            )
        
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_training_detects_regression_for_many_unique_values(self, api_client):
        """POST /train detects regression for numeric target with many unique values."""
        from api.routers import training
        
        mock_dataset = {
            'dataset_id': 'dataset-reg-001',
            'filename': 'regression.csv',
            'columns': ['id', 'feature1', 'price'],
            'row_count': 1000,
            'column_types': {'id': 'numeric', 'feature1': 'numeric', 'price': 'numeric'},
            'column_stats': {'price': {'unique': 500}},  # Many unique values
        }
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=mock_dataset), \
             patch.object(training.dynamodb_service, 'create_job', return_value=None), \
             patch.object(training.dynamodb_service, 'update_job_status', return_value=None), \
             patch.object(training.batch_service, 'submit_training_job', return_value="arn:aws:batch:job/12345"):
            
            response = api_client.post(
                "/train",
                json={"dataset_id": "dataset-reg-001", "target_column": "price"}
            )
        
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_training_dataset_not_found(self, api_client):
        """POST /train returns 404 when dataset doesn't exist."""
        from api.routers import training
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=None):
            response = api_client.post(
                "/train",
                json={"dataset_id": "nonexistent", "target_column": "price"}
            )
        
        assert response.status_code == 404
        assert "Dataset not found" in response.json()["detail"]
    
    @pytest.mark.api
    def test_training_target_column_not_found(self, api_client):
        """POST /train returns 400 when target column doesn't exist."""
        from api.routers import training
        
        mock_dataset = {
            'dataset_id': 'dataset-err-001',
            'filename': 'data.csv',
            'columns': ['id', 'feature1', 'feature2'],
            'row_count': 100,
        }
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=mock_dataset):
            response = api_client.post(
                "/train",
                json={"dataset_id": "dataset-err-001", "target_column": "nonexistent_column"}
            )
        
        assert response.status_code == 400
        assert "not found in dataset" in response.json()["detail"]
    
    @pytest.mark.api
    def test_training_auto_time_budget_small_dataset(self, api_client):
        """POST /train auto-calculates 120s time budget for small datasets."""
        from api.routers import training
        
        mock_dataset = {
            'dataset_id': 'dataset-small',
            'filename': 'small.csv',
            'columns': ['id', 'target'],
            'row_count': 500,  # Small dataset
            'column_types': {'target': 'categorical'},
        }
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=mock_dataset), \
             patch.object(training.dynamodb_service, 'create_job', return_value=None), \
             patch.object(training.dynamodb_service, 'update_job_status', return_value=None), \
             patch.object(training.batch_service, 'submit_training_job', return_value="arn:aws:batch:job/12345"):
            
            response = api_client.post(
                "/train",
                json={"dataset_id": "dataset-small", "target_column": "target"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["estimated_time"] == 120  # Auto-calculated for small dataset
    
    @pytest.mark.api
    def test_training_auto_time_budget_large_dataset(self, api_client):
        """POST /train auto-calculates larger time budget for large datasets."""
        from api.routers import training
        
        mock_dataset = {
            'dataset_id': 'dataset-large',
            'filename': 'large.csv',
            'columns': ['id', 'target'],
            'row_count': 100000,  # Very large dataset
            'column_types': {'target': 'categorical'},
        }
        
        with patch.object(training.dynamodb_service, 'get_dataset_metadata', return_value=mock_dataset), \
             patch.object(training.dynamodb_service, 'create_job', return_value=None), \
             patch.object(training.dynamodb_service, 'update_job_status', return_value=None), \
             patch.object(training.batch_service, 'submit_training_job', return_value="arn:aws:batch:job/12345"):
            
            response = api_client.post(
                "/train",
                json={"dataset_id": "dataset-large", "target_column": "target"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["estimated_time"] == 1200  # Auto-calculated for very large dataset



class TestJobCaching:
    """Test ETag caching behavior for jobs"""
    
    def test_get_job_etag_headers(self, api_client):
        """GET /jobs/{id} returns ETag and Cache-Control headers."""
        from api.routers import models
        
        # Mock job with explicit updated_at for ETag generation
        mock_job = {
            'job_id': 'job-cache-001',
            'dataset_id': 'ds-123',
            'status': 'completed',
            'target_column': 'target',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T12:00:00Z', # Used for ETag
            'deployed': False
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job):
            # 2. Get job status
            response = api_client.get("/jobs/job-cache-001")
            
        assert response.status_code == 200
        
        # 3. Verify headers
        assert "ETag" in response.headers
        assert response.headers["Cache-Control"] == "private, max-age=0, must-revalidate"
        assert response.headers["Vary"] == "Authorization"

    def test_get_job_304_not_modified(self, api_client):
        """GET /jobs/{id} with matching If-None-Match returns 304."""
        from api.routers import models
        
        mock_job = {
            'job_id': 'job-cache-002',
            'dataset_id': 'ds-123',
            'status': 'completed',
            'target_column': 'target',
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T12:00:00Z',
            'deployed': False
        }
        
        with patch.object(models.dynamodb_service, 'get_job', return_value=mock_job):
            # 2. Get initial response to get ETag
            response1 = api_client.get("/jobs/job-cache-002")
            etag = response1.headers["ETag"]
            
            # 3. Request again with If-None-Match
            headers = {"If-None-Match": etag}
            response2 = api_client.get("/jobs/job-cache-002", headers=headers)
        
        # 4. Verify 304 Not Modified
        assert response2.status_code == 304
        assert not response2.content  # Body should be empty
        assert response2.headers["ETag"] == etag


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
