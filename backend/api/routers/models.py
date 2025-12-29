from fastapi import APIRouter, HTTPException, status, Query, Response, Request
from typing import Dict, Optional, Any
import hashlib
from ..models.schemas import (
    JobListResponse, JobResponse, JobStatus, ProblemType, JobUpdateRequest,
    DeployRequest, DeployResponse, PreprocessingInfo, JobSummary
)
from ..services.dynamo_service import dynamodb_service
from ..services.s3_service import s3_service
from ..utils.helpers import get_settings

router = APIRouter(prefix="/jobs", tags=["jobs"])
settings = get_settings()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, response: Response, request: Request) -> JobResponse:
    """
    Get the status and results of a training job.
    Implements ETag-based caching with must-revalidate for accurate state after deploy/undeploy.
    """
    try:
        # Use consistent read to ensure we generate ETag from the absolute latest state
        job = dynamodb_service.get_job(job_id, consistent_read=True)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Build preprocessing_info if available
        preprocessing_info = None
        if job.get('preprocessing_info'):
            # Convert Decimal to float for numeric_stats (DynamoDB returns Decimal types)
            raw_numeric_stats = job['preprocessing_info'].get('numeric_stats')
            numeric_stats = None
            if raw_numeric_stats:
                numeric_stats = {
                    col: {
                        key: float(val) if val is not None else None
                        for key, val in stats.items()
                    }
                    for col, stats in raw_numeric_stats.items()
                }
            
            preprocessing_info = PreprocessingInfo(
                feature_columns=job['preprocessing_info'].get('feature_columns'),
                feature_count=job['preprocessing_info'].get('feature_count'),
                dropped_columns=job['preprocessing_info'].get('dropped_columns'),
                dropped_count=job['preprocessing_info'].get('dropped_count'),
                feature_types=job['preprocessing_info'].get('feature_types'),
                categorical_mappings=job['preprocessing_info'].get('categorical_mappings'),
                numeric_stats=numeric_stats,
                target_mapping=job['preprocessing_info'].get('target_mapping')
            )
        
        job_response = JobResponse(
            job_id=job['job_id'],
            dataset_id=job.get('dataset_id', ''),
            status=JobStatus(job['status']),
            target_column=job.get('target_column', ''),
            dataset_name=job.get('dataset_name'),
            problem_type=ProblemType(job['problem_type']) if job.get('problem_type') else None,
            created_at=job.get('created_at'),
            updated_at=job.get('updated_at'),
            started_at=job.get('started_at'),
            completed_at=job.get('completed_at'),
            metrics=job.get('metrics'),
            error_message=job.get('error_message'),
            tags=job.get('tags'),
            notes=job.get('notes'),
            deployed=job.get('deployed', False),
            deployed_at=job.get('deployed_at'),
            preprocessing_info=preprocessing_info
        )
        
        # Generate download URLs if job is completed
        if job['status'] == JobStatus.COMPLETED.value:
            if job.get('model_path'):
                # Extract bucket and key from s3:// path
                model_path = job['model_path'].replace('s3://', '')
                bucket, key = model_path.split('/', 1)
                job_response.model_download_url = s3_service.generate_presigned_download_url_cached(
                    bucket=bucket,
                    key=key
                )
            
            # ONNX Model download URL
            if job.get('onnx_model_path'):
                onnx_path = job['onnx_model_path'].replace('s3://', '')
                bucket, key = onnx_path.split('/', 1)
                job_response.onnx_model_download_url = s3_service.generate_presigned_download_url_cached(
                    bucket=bucket,
                    key=key
                )
            
            # EDA Report (also keep backward compatibility with report_path)
            eda_path = job.get('eda_report_path') or job.get('report_path')
            if eda_path:
                report_path = eda_path.replace('s3://', '')
                bucket, key = report_path.split('/', 1)
                url = s3_service.generate_presigned_download_url_cached(bucket=bucket, key=key)
                job_response.report_download_url = url  # Backward compatibility
                job_response.eda_report_download_url = url
            
            # Training Report
            if job.get('training_report_path'):
                training_path = job['training_report_path'].replace('s3://', '')
                bucket, key = training_path.split('/', 1)
                job_response.training_report_download_url = s3_service.generate_presigned_download_url_cached(
                    bucket=bucket,
                    key=key
                )
        
        # ============================================================================
        # HTTP Cache Strategy with ETag for accurate state after deploy/undeploy
        # ============================================================================
        
        # 1. Generate ETag based on mutable fields (updated_at, deployed, deployed_at)
        #    This changes whenever the job state changes (including deploy/undeploy)
        etag_source = f"{job.get('updated_at', '')}-{job.get('deployed', False)}-{job.get('deployed_at', '')}"
        etag = f'"{hashlib.md5(etag_source.encode()).hexdigest()}"'
        response.headers["ETag"] = etag
        
        # 2. Check If-None-Match header for conditional requests (304 Not Modified)
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match == etag:
            # Resource hasn't changed - return 304 (browser will use cached version)
            # IMPORTANT: 304 responses MUST NOT have a body
            return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "private, max-age=0, must-revalidate"})
        
        # 3. Always force revalidation
        #    We used to have adaptive TTLs, but deployment status changes need to be reflected immediately.
        #    max-age=0 + must-revalidate ensures the browser ALWAYS validates the ETag with the server.
        #    Server (consistent read) -> Calculates ETag -> 304 if same, 200 if changed.
        #    This is the most robust way to handle state changes like 'Deployed' vs 'Undeployed'.
        response.headers["Cache-Control"] = "private, max-age=0, must-revalidate"
        response.headers["Vary"] = "Authorization"  # Vary by auth header if auth is added later
        
        return job_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )


@router.delete("/{job_id}")
async def delete_job(job_id: str, response: Response, delete_data: bool = True) -> Dict[str, Any]:
    """
    Delete a training job and optionally all associated data (model, report, dataset)
    """
    try:
        # Get job details first
        job = dynamodb_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        deleted_resources = []
        
        if delete_data:
            # Delete model from S3
            if job.get('model_path'):
                try:
                    model_path = job['model_path'].replace('s3://', '')
                    bucket, key = model_path.split('/', 1)
                    s3_service.delete_object(bucket, key)
                    deleted_resources.append(f"model: {key}")
                except Exception:
                    pass  # Model might not exist
            
            # Delete EDA report from S3
            eda_path = job.get('eda_report_path') or job.get('report_path')
            if eda_path:
                try:
                    report_path = eda_path.replace('s3://', '')
                    bucket, key = report_path.split('/', 1)
                    s3_service.delete_object(bucket, key)
                    deleted_resources.append(f"eda_report: {key}")
                except Exception:
                    pass  # Report might not exist
            
            # Delete training report from S3
            if job.get('training_report_path'):
                try:
                    training_path = job['training_report_path'].replace('s3://', '')
                    bucket, key = training_path.split('/', 1)
                    s3_service.delete_object(bucket, key)
                    deleted_resources.append(f"training_report: {key}")
                except Exception:
                    pass  # Report might not exist
            
            # Delete dataset from S3 and DynamoDB
            dataset_id = job.get('dataset_id')
            if dataset_id:
                try:
                    # Delete dataset files from S3
                    deleted_count = s3_service.delete_folder(
                        bucket=settings.s3_bucket_datasets,
                        prefix=f"datasets/{dataset_id}/"
                    )
                    if deleted_count > 0:
                        deleted_resources.append(f"dataset files: {deleted_count}")
                    
                    # Delete dataset metadata from DynamoDB
                    dynamodb_service.delete_dataset(dataset_id)
                    deleted_resources.append(f"dataset metadata: {dataset_id}")
                except Exception:
                    pass  # Dataset might not exist
        
        # Delete job record from DynamoDB
        dynamodb_service.delete_job(job_id)
        
        # Ensure client caches are invalidated immediately
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        
        return {
            "message": "Job deleted successfully",
            "job_id": job_id,
            "deleted_resources": deleted_resources
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job: {str(e)}"
        )


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job_metadata(job_id: str, update_request: JobUpdateRequest, response: Response, request: Request) -> JobResponse:
    """
    Update job metadata (tags and notes) for experiment tracking.
    Tags can be used to categorize jobs (e.g., "experiment-1", "baseline", "production").
    Notes can store observations or comments about the training run.
    """
    try:
        # Verify job exists
        # Use consistent read to ensure we have the absolute latest state before validating and updating
        job = dynamodb_service.get_job(job_id, consistent_read=True)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Validate tags if provided
        if update_request.tags is not None:
            if len(update_request.tags) > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 10 tags allowed per job"
                )
            # Validate individual tag length
            for tag in update_request.tags:
                if not tag.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Tags cannot be empty or whitespace"
                    )
                if len(tag) > 50:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Each tag must be 50 characters or less"
                    )
        
        # Validate notes length if provided (defense-in-depth, Pydantic also validates)
        if update_request.notes is not None and len(update_request.notes) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notes must be 1000 characters or less"
            )
        
        # Update job metadata in DynamoDB
        dynamodb_service.update_job_metadata(
            job_id=job_id,
            tags=update_request.tags,
            notes=update_request.notes
        )
        
        # Return updated job (pass response and request for HTTP headers + ETag)
        return await get_job_status(job_id, response, request)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job metadata: {str(e)}"
        )


@router.post("/{job_id}/deploy", response_model=DeployResponse)
async def deploy_model(job_id: str, request: DeployRequest) -> DeployResponse:
    """
    Deploy or undeploy a trained model for inference.
    Only completed jobs with ONNX models can be deployed.
    """
    try:
        # Verify job exists
        # Use consistent read to ensure we have the absolute latest state before deploying
        job = dynamodb_service.get_job(job_id, consistent_read=True)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if job is completed
        if job['status'] != JobStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deploy job with status '{job['status']}'. Only completed jobs can be deployed."
            )
        
        # Check if ONNX model exists
        if request.deploy and not job.get('onnx_model_path'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ONNX model available for this job. Only jobs with ONNX export can be deployed."
            )
        
        # Update deployed status
        dynamodb_service.update_job_deployed(job_id, request.deploy)
        
        # IMPORTANT: Invalidate HTTP cache for this job
        # Force clients to fetch fresh data with updated deployed/deployed_at fields
        # Note: This does NOT invalidate S3 presigned URL cache (those remain valid)
        from fastapi import Response
        response = Response()
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["X-Cache-Invalidated"] = "deploy-status-changed"
        
        action = "deployed" if request.deploy else "undeployed"
        return DeployResponse(
            job_id=job_id,
            deployed=request.deploy,
            message=f"Model successfully {action}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deploying model: {str(e)}"
        )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    next_token: Optional[str] = None,
    user_id: str = "default"
) -> JobListResponse:
    """
    List all training jobs with pagination (lightweight response)
    Returns JobSummary objects optimized for list view - no URLs, no preprocessing_info
    """
    try:
        last_key = None
        if next_token:
            # In production, you'd want to encrypt/encode this
            import json
            last_key = json.loads(next_token)
        
        raw_jobs, last_evaluated_key = dynamodb_service.list_jobs(
            user_id=user_id,
            limit=limit,
            last_evaluated_key=last_key
        )
        
        # Convert to JobSummary (lightweight) instead of full JobResponse
        jobs = []
        for job in raw_jobs:
            # Safely handle None/null metrics (happens when jobs fail before completion)
            metrics = job.get('metrics') or {}
            
            # Extract primary metric (accuracy for classification, r2_score for regression)
            problem_type = job.get('problem_type')
            primary_metric = None
            if problem_type == 'classification' and metrics.get('accuracy'):
                primary_metric = float(metrics['accuracy'])
            elif problem_type == 'regression' and metrics.get('r2_score'):
                primary_metric = float(metrics['r2_score'])
            
            # Extract training time and best estimator (safely handle None)
            training_time = float(metrics['training_time']) if metrics.get('training_time') else None
            best_estimator = str(metrics['best_estimator']) if metrics.get('best_estimator') else None
            
            summary = JobSummary(
                job_id=job['job_id'],
                dataset_id=job.get('dataset_id', ''),
                status=JobStatus(job['status']),
                target_column=job.get('target_column', ''),
                problem_type=ProblemType(problem_type) if problem_type else None,
                dataset_name=job.get('dataset_name'),
                created_at=job.get('created_at'),
                updated_at=job.get('updated_at'),
                started_at=job.get('started_at'),
                completed_at=job.get('completed_at'),
                tags=job.get('tags'),
                primary_metric=primary_metric,
                training_time=training_time,
                best_estimator=best_estimator
            )
            jobs.append(summary)
        
        next_token_response = None
        if last_evaluated_key:
            import json
            next_token_response = json.dumps(last_evaluated_key)
        
        return JobListResponse(
            jobs=jobs,
            next_token=next_token_response
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )
