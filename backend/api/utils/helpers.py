from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AWS Settings
    aws_region: str = "us-east-1"
    aws_endpoint_url: Optional[str] = None  # For LocalStack: http://localstack:4566
    
    # S3 Buckets
    s3_bucket_datasets: str = "automl-lite-dev-datasets-835503570883"
    s3_bucket_models: str = "automl-lite-dev-models-835503570883"
    s3_bucket_reports: str = "automl-lite-dev-reports-835503570883"
    
    # DynamoDB Tables
    dynamodb_datasets_table: str = "automl-lite-dev-datasets"
    dynamodb_jobs_table: str = "automl-lite-dev-training-jobs"
    
    # Batch Configuration
    batch_job_queue: str = "automl-lite-dev-training-queue"
    batch_job_definition: str = "automl-lite-dev-training-job"
    
    # Local development
    local_training: bool = False  # If True, run training locally instead of AWS Batch
    
    # API Configuration
    cors_origins: list = ["*"]
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    presigned_url_expiration: int = 3600
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    return Settings()
