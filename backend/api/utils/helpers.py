import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Settings
    aws_region: str = os.getenv("REGION", "us-east-1")
    s3_bucket_datasets: str = os.getenv("S3_BUCKET_DATASETS", "automl-lite-dev-datasets-835503570883")
    s3_bucket_models: str = os.getenv("S3_BUCKET_MODELS", "automl-lite-dev-models-835503570883")
    s3_bucket_reports: str = os.getenv("S3_BUCKET_REPORTS", "automl-lite-dev-reports-835503570883")
    
    # DynamoDB Tables
    dynamodb_datasets_table: str = os.getenv("DYNAMODB_DATASETS_TABLE", "automl-lite-dev-datasets")
    dynamodb_jobs_table: str = os.getenv("DYNAMODB_JOBS_TABLE", "automl-lite-dev-training-jobs")
    
    # Batch Configuration
    batch_job_queue: str = os.getenv("BATCH_JOB_QUEUE", "automl-lite-dev-training-queue")
    batch_job_definition: str = os.getenv("BATCH_JOB_DEFINITION", "arn:aws:batch:us-east-1:835503570883:job-definition/automl-lite-dev-training-job:1")
    
    # API Configuration
    cors_origins: list = ["*"]
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    presigned_url_expiration: int = 3600
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
