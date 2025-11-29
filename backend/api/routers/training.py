from fastapi import APIRouter, HTTPException, status, Query
from datetime import datetime
from typing import Optional
import uuid
from ..models.schemas import (
    TrainRequest, TrainResponse,
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
        # Verify dataset exists (use get_dataset_metadata)
        dataset = dynamodb_service.get_dataset_metadata(request.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Verify target column exists (columns is now a list of strings)
        if dataset.get('columns'):
            if request.target_column not in dataset['columns']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target column '{request.target_column}' not found in dataset"
                )
        
        # Determine problem type based on column type
        problem_type = None
        if dataset.get('column_types'):
            col_type = dataset['column_types'].get(request.target_column, 'categorical')
            problem_type = ProblemType.REGRESSION if col_type == 'numeric' else ProblemType.CLASSIFICATION
        
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
            target_column=request.target_column,
            problem_type=problem_type
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
