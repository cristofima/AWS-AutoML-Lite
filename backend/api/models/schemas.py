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


# Dataset metadata for confirm endpoint (matches frontend)
class DatasetMetadata(BaseModel):
    dataset_id: str
    filename: str
    file_size: int
    uploaded_at: str
    columns: List[str]
    row_count: int
    column_types: Dict[str, str]
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
    time_budget: int = Field(default=300, ge=60, le=3600)
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
    
    model_config = {"protected_namespaces": ()}


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
    report_download_url: Optional[str] = None  # Backward compatibility (EDA report)
    eda_report_download_url: Optional[str] = None
    training_report_download_url: Optional[str] = None
    error_message: Optional[str] = None
    
    model_config = {"protected_namespaces": ()}


class JobListResponse(BaseModel):
    jobs: List[JobDetails]
    next_token: Optional[str] = None
