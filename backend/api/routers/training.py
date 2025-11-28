from fastapi import APIRouter, HTTPException, status, Query
from datetime import datetime
from typing import Optional
import uuid
from ..models.schemas import (
    TrainRequest, TrainResponse, JobResponse, 
    JobStatus, ProblemType, JobDetails
)
from ..services.dynamo_service import dynamodb_service
from ..services.batch_service import batch_service
from ..services.s3_service import s3_service
from ..utils.helpers import get_settings

router = APIRouter(prefix="/train", tags=["training"])
settings = get_settings()


@router.post("", response_model=TrainResponse)
async def start_training(request: TrainRequest):
    """
    Start a training job for a dataset
    """
    try:
        # Verify dataset exists
        dataset = dynamodb_service.get_dataset(request.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Verify target column exists
        if dataset.get('columns'):
            column_names = [col['name'] for col in dataset['columns']]
            if request.target_column not in column_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target column '{request.target_column}' not found in dataset"
                )
        
        # Create job record
        job_id = str(uuid.uuid4())
        job = JobDetails(
            job_id=job_id,
            dataset_id=request.dataset_id,
            user_id="default",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            dataset_name=dataset['filename'],
            target_column=request.target_column
        )
        
        dynamodb_service.create_job(job)
        
        # Submit batch job
        batch_job_id = batch_service.submit_training_job(
            job_name=f"training-{job_id[:8]}",
            dataset_id=request.dataset_id,
            target_column=request.target_column,
            job_id=job_id,
            config=request.config.model_dump()
        )
        
        # Update job with batch job ID
        dynamodb_service.update_job_status(
            job_id=job_id,
            status=JobStatus.PENDING,
            updates={'batch_job_id': batch_job_id}
        )
        
        return TrainResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            estimated_time=request.config.time_budget
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting training: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get the status and results of a training job
    """
    try:
        job = dynamodb_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        response = JobResponse(
            job_id=job['job_id'],
            status=JobStatus(job['status']),
            problem_type=ProblemType(job['problem_type']) if job.get('problem_type') else None,
            metrics=job.get('metrics'),
            error_message=job.get('error_message')
        )
        
        # Generate download URLs if job is completed
        if job['status'] == JobStatus.COMPLETED.value:
            if job.get('model_path'):
                # Extract bucket and key from s3:// path
                model_path = job['model_path'].replace('s3://', '')
                bucket, key = model_path.split('/', 1)
                response.model_download_url = s3_service.generate_presigned_download_url(
                    bucket=bucket,
                    key=key
                )
            
            if job.get('report_path'):
                report_path = job['report_path'].replace('s3://', '')
                bucket, key = report_path.split('/', 1)
                response.report_download_url = s3_service.generate_presigned_download_url(
                    bucket=bucket,
                    key=key
                )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )
