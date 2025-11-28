from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from ..models.schemas import JobListResponse
from ..services.dynamo_service import dynamodb_service

router = APIRouter(prefix="/jobs", tags=["models"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    next_token: Optional[str] = None,
    user_id: str = "default"
):
    """
    List all training jobs with pagination
    """
    try:
        last_key = None
        if next_token:
            # In production, you'd want to encrypt/encode this
            import json
            last_key = json.loads(next_token)
        
        jobs, last_evaluated_key = dynamodb_service.list_jobs(
            user_id=user_id,
            limit=limit,
            last_evaluated_key=last_key
        )
        
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
