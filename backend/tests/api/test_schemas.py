"""
Unit tests for Pydantic schema validation.

These tests verify that API input validation works correctly,
catching invalid data at the API boundary before processing.
"""
import pytest
from pydantic import ValidationError
import sys
from pathlib import Path

# Add API module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from models.schemas import (
    TrainRequest,
    TrainResponse,
    TrainingConfig,
    DatasetMetadata,
    ColumnStats,
    JobStatus,
    PredictionInput,
    PredictionResponse,
    UploadResponse,
    ProblemType,
)


class TestTrainRequestValidation:
    """Test TrainRequest schema validation."""
    
    @pytest.mark.unit
    def test_valid_request_minimal(self):
        """Valid request with only required fields."""
        request = TrainRequest(
            dataset_id="abc123",
            target_column="price"
        )
        assert request.dataset_id == "abc123"
        assert request.target_column == "price"
        # Default config is created automatically
        assert request.config is not None
    
    @pytest.mark.unit
    def test_valid_request_with_config(self):
        """Valid request with custom config."""
        request = TrainRequest(
            dataset_id="dataset-xyz-789",
            target_column="target",
            config=TrainingConfig(time_budget=600, metric="accuracy")
        )
        assert request.dataset_id == "dataset-xyz-789"
        assert request.target_column == "target"
        assert request.config.time_budget == 600
        assert request.config.metric == "accuracy"
    
    @pytest.mark.unit
    def test_missing_dataset_id(self):
        """Missing dataset_id should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TrainRequest(target_column="price")
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('dataset_id',) for e in errors)
    
    @pytest.mark.unit
    def test_missing_target_column(self):
        """Missing target_column should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TrainRequest(dataset_id="abc123")
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('target_column',) for e in errors)
    
    @pytest.mark.unit
    def test_time_budget_minimum(self):
        """Time budget below minimum should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TrainRequest(
                dataset_id="abc123",
                target_column="price",
                config=TrainingConfig(time_budget=30)  # Below minimum of 60
            )
        
        errors = exc_info.value.errors()
        assert any('time_budget' in str(e) or 'greater_than_equal' in str(e) for e in errors)
    
    @pytest.mark.unit
    def test_time_budget_maximum(self):
        """Time budget above maximum should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TrainRequest(
                dataset_id="abc123",
                target_column="price",
                config=TrainingConfig(time_budget=7200)  # Above maximum of 3600
            )
        
        errors = exc_info.value.errors()
        assert any('time_budget' in str(e) or 'less_than_equal' in str(e) for e in errors)
    
    @pytest.mark.unit
    def test_time_budget_boundary_valid(self):
        """Time budget at boundaries should be valid."""
        # Minimum boundary
        request_min = TrainRequest(
            dataset_id="abc123",
            target_column="price",
            config=TrainingConfig(time_budget=60)
        )
        assert request_min.config.time_budget == 60
        
        # Maximum boundary
        request_max = TrainRequest(
            dataset_id="abc123",
            target_column="price",
            config=TrainingConfig(time_budget=3600)
        )
        assert request_max.config.time_budget == 3600


class TestTrainResponseValidation:
    """Test TrainResponse schema."""
    
    @pytest.mark.unit
    def test_valid_response(self):
        """Valid response creation."""
        response = TrainResponse(
            job_id="job-123",
            status=JobStatus.PENDING,
            estimated_time=300
        )
        assert response.job_id == "job-123"
        assert response.status == JobStatus.PENDING
        assert response.estimated_time == 300
    
    @pytest.mark.unit
    def test_response_with_running_status(self):
        """Response with running status."""
        response = TrainResponse(
            job_id="job-123",
            status=JobStatus.RUNNING,
            estimated_time=600
        )
        assert response.status == JobStatus.RUNNING


class TestJobStatusEnum:
    """Test JobStatus enum values."""
    
    @pytest.mark.unit
    def test_all_status_values(self):
        """Verify all expected status values exist."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
    
    @pytest.mark.unit
    def test_status_from_string(self):
        """Status can be created from string."""
        status = JobStatus("running")
        assert status == JobStatus.RUNNING


class TestProblemTypeEnum:
    """Test ProblemType enum values."""
    
    @pytest.mark.unit
    def test_problem_type_values(self):
        """Verify problem type values."""
        assert ProblemType.CLASSIFICATION.value == "classification"
        assert ProblemType.REGRESSION.value == "regression"
    
    @pytest.mark.unit
    def test_problem_type_from_string(self):
        """ProblemType can be created from string."""
        pt = ProblemType("classification")
        assert pt == ProblemType.CLASSIFICATION


class TestDatasetMetadata:
    """Test DatasetMetadata schema."""
    
    @pytest.mark.unit
    def test_valid_dataset_metadata(self):
        """Valid dataset metadata creation."""
        metadata = DatasetMetadata(
            dataset_id="dataset-123",
            filename="data.csv",
            file_size=1024,
            uploaded_at="2024-01-15T10:30:00Z",
            columns=["id", "name", "price"],
            row_count=100,
            column_types={"id": "int64", "name": "object", "price": "float64"}
        )
        assert metadata.dataset_id == "dataset-123"
        assert metadata.filename == "data.csv"
        assert len(metadata.columns) == 3
    
    @pytest.mark.unit
    def test_dataset_with_optional_fields(self):
        """Dataset metadata with optional fields."""
        metadata = DatasetMetadata(
            dataset_id="dataset-456",
            filename="sales.csv",
            file_size=1024000,
            uploaded_at="2024-01-15T10:30:00Z",
            columns=["id", "name", "price", "quantity"],
            row_count=10000,
            column_types={"id": "int64", "name": "object", "price": "float64", "quantity": "int64"},
            problem_type=ProblemType.REGRESSION,
            column_stats={
                "id": ColumnStats(unique=10000, missing=0, missing_pct=0.0),
                "price": ColumnStats(unique=500, missing=10, missing_pct=0.1)
            }
        )
        assert metadata.file_size == 1024000
        assert metadata.row_count == 10000
        assert metadata.problem_type == ProblemType.REGRESSION
        assert metadata.column_stats["id"].unique == 10000


class TestPredictionInput:
    """Test PredictionInput schema validation."""
    
    @pytest.mark.unit
    def test_valid_predict_request(self):
        """Valid prediction request."""
        request = PredictionInput(
            features={"age": 25, "income": 50000, "category": "A"}
        )
        assert request.features["age"] == 25
        assert request.features["income"] == 50000
    
    @pytest.mark.unit
    def test_predict_request_missing_features(self):
        """Missing features should raise ValidationError."""
        with pytest.raises(ValidationError):
            PredictionInput()
    
    @pytest.mark.unit
    def test_predict_request_empty_features(self):
        """Empty features dictionary should be valid (validation happens later)."""
        request = PredictionInput(
            features={}
        )
        assert request.features == {}
    
    @pytest.mark.unit
    def test_predict_request_mixed_types(self):
        """Features can have mixed types (float, int, str)."""
        request = PredictionInput(
            features={"numeric_int": 25, "numeric_float": 50000.50, "categorical": "A"}
        )
        assert isinstance(request.features["numeric_int"], int)
        assert isinstance(request.features["numeric_float"], float)
        assert isinstance(request.features["categorical"], str)


class TestPredictionResponse:
    """Test PredictionResponse schema."""
    
    @pytest.mark.unit
    def test_classification_response(self):
        """Valid classification prediction response."""
        response = PredictionResponse(
            job_id="job-123",
            prediction=1,
            probability=0.8,
            probabilities={"0": 0.2, "1": 0.8},
            inference_time_ms=15.5,
            model_type="lgbm"
        )
        assert response.prediction == 1
        assert response.probability == 0.8
        assert response.probabilities["1"] == 0.8
        assert response.inference_time_ms == 15.5
    
    @pytest.mark.unit
    def test_regression_response(self):
        """Valid regression prediction response."""
        response = PredictionResponse(
            job_id="job-456",
            prediction=42.5,
            inference_time_ms=10.2,
            model_type="rf"
        )
        assert response.prediction == 42.5
        assert response.probability is None
        assert response.probabilities is None
    
    @pytest.mark.unit
    def test_response_with_string_prediction(self):
        """Response can have string prediction (class label)."""
        response = PredictionResponse(
            job_id="job-789",
            prediction="Class_A",
            probability=0.95,
            inference_time_ms=12.0,
            model_type="extra_tree"
        )
        assert response.prediction == "Class_A"


class TestUploadResponse:
    """Test UploadResponse schema."""
    
    @pytest.mark.unit
    def test_valid_upload_response(self):
        """Valid upload response."""
        response = UploadResponse(
            dataset_id="dataset-789",
            upload_url="https://s3.amazonaws.com/bucket/key?signed=xyz",
            expires_in=3600
        )
        assert response.dataset_id == "dataset-789"
        assert "s3.amazonaws.com" in response.upload_url
        assert response.expires_in == 3600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
