from fastapi import APIRouter, HTTPException, status, Query
from datetime import datetime, timezone
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
        
        # Determine problem type based on column type and unique values
        problem_type = None
        if dataset.get('column_types'):
            col_type = dataset['column_types'].get(request.target_column, 'categorical')
            
            # For numeric columns, check if it looks like classification (few unique values)
            # This is a heuristic - the actual detection happens in the training container
            if col_type == 'numeric':
                # If we have column stats, check unique values
                column_stats = dataset.get('column_stats', {}).get(request.target_column, {})
                unique_count = column_stats.get('unique', 0)
                total_count = dataset.get('row_count', 1)
                
                # If less than 20 unique values or less than 5% unique ratio, likely classification
                if unique_count > 0 and (unique_count < 20 or unique_count / total_count < 0.05):
                    problem_type = ProblemType.CLASSIFICATION
                else:
                    problem_type = ProblemType.REGRESSION
            else:
                # Non-numeric is always classification
                problem_type = ProblemType.CLASSIFICATION
        
        # Create job record
        job_id = str(uuid.uuid4())
        job = JobDetails(
            job_id=job_id,
            dataset_id=request.dataset_id,
            user_id="default",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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
