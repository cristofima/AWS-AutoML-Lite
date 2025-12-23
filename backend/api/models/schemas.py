from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ProblemType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ColumnInfo(BaseModel):
    name: str
    dtype: str
    missing_pct: float
    unique_values: Optional[int] = None


class UploadRequest(BaseModel):
    filename: str
    content_type: str = "text/csv"


class UploadResponse(BaseModel):
    dataset_id: str
    upload_url: str
    expires_in: int = 3600


class ColumnStats(BaseModel):
    unique: int
    missing: int = 0
    missing_pct: float = 0.0


# Dataset metadata for confirm endpoint (matches frontend)
class DatasetMetadata(BaseModel):
    dataset_id: str
    filename: str
    file_size: int
    uploaded_at: str
    columns: List[str]
    row_count: int
    column_types: Dict[str, str]
    column_stats: Optional[Dict[str, ColumnStats]] = None
    problem_type: Optional[ProblemType] = None
    
    model_config = {"protected_namespaces": ()}


# Extended dataset metadata for internal use
class DatasetMetadataExtended(BaseModel):
    dataset_id: str
    user_id: str = "default"
    uploaded_at: datetime
    filename: str
    s3_path: str
    size_bytes: int
    num_rows: Optional[int] = None
    num_columns: Optional[int] = None
    columns: Optional[List[ColumnInfo]] = None


class TrainingConfig(BaseModel):
    time_budget: Optional[int] = Field(default=None, ge=60, le=3600)
    metric: str = "auto"


class TrainRequest(BaseModel):
    dataset_id: str
    target_column: str
    config: Optional[TrainingConfig] = TrainingConfig()


class TrainResponse(BaseModel):
    job_id: str
    status: JobStatus
    estimated_time: int


class TrainingMetrics(BaseModel):
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    r2_score: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    training_time: float


class JobDetails(BaseModel):
    job_id: str
    dataset_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    status: JobStatus
    dataset_name: str
    target_column: str
    problem_type: Optional[ProblemType] = None
    model_path: Optional[str] = None
    report_path: Optional[str] = None  # Backward compatibility (EDA report)
    eda_report_path: Optional[str] = None
    training_report_path: Optional[str] = None
    metrics: Optional[TrainingMetrics] = None
    feature_importance: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None
    tags: Optional[List[str]] = None  # Custom labels for filtering
    notes: Optional[str] = None  # User notes for experiment tracking
    
    model_config = {"protected_namespaces": ()}


class NumericStats(BaseModel):
    """Statistics for a numeric column"""
    min: float
    max: float
    is_integer: bool


class PreprocessingInfo(BaseModel):
    """Preprocessing information for inference"""
    feature_columns: Optional[List[str]] = None
    feature_count: Optional[int] = None
    dropped_columns: Optional[List[str]] = None
    dropped_count: Optional[int] = None
    feature_types: Optional[Dict[str, str]] = None  # column -> 'numeric' | 'categorical'
    categorical_mappings: Optional[Dict[str, Dict[str, int]]] = None  # column -> {value: code}
    numeric_stats: Optional[Dict[str, NumericStats]] = None  # column -> {min, max, is_integer}
    target_mapping: Optional[Dict[str, str]] = None  # encoded_value -> original_label


class JobResponse(BaseModel):
    job_id: str
    dataset_id: str
    status: JobStatus
    target_column: str
    dataset_name: Optional[str] = None
    problem_type: Optional[ProblemType] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metrics: Optional[TrainingMetrics] = None
    model_download_url: Optional[str] = None
    onnx_model_download_url: Optional[str] = None
    report_download_url: Optional[str] = None  # Backward compatibility (EDA report)
    eda_report_download_url: Optional[str] = None
    training_report_download_url: Optional[str] = None
    error_message: Optional[str] = None
    tags: Optional[List[str]] = None  # Custom labels for filtering
    notes: Optional[str] = None  # User notes for experiment tracking
    deployed: bool = False  # Whether the model is deployed for inference
    preprocessing_info: Optional[PreprocessingInfo] = None  # Feature info for inference
    
    model_config = {"protected_namespaces": ()}


class JobUpdateRequest(BaseModel):
    """Request schema for updating job metadata (tags, notes)"""
    tags: Optional[List[str]] = Field(default=None, max_items=10, description="Custom labels for filtering (max 10)")
    notes: Optional[str] = Field(default=None, max_length=1000, description="User notes for experiment tracking")


class DeployRequest(BaseModel):
    """Request schema for deploying/undeploying a model"""
    deploy: bool = Field(..., description="True to deploy, False to undeploy")


class DeployResponse(BaseModel):
    """Response schema for deploy/undeploy operations"""
    job_id: str
    deployed: bool
    message: str


class PredictionInput(BaseModel):
    """Request schema for making predictions"""
    features: Dict[str, float | int | str] = Field(..., description="Input features for prediction")


class PredictionResponse(BaseModel):
    """Response schema for predictions"""
    job_id: str
    prediction: float | int | str
    probability: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    inference_time_ms: float
    model_type: str
    
    model_config = {"protected_namespaces": ()}


class JobListResponse(BaseModel):
    jobs: List[JobDetails]
    next_token: Optional[str] = None
