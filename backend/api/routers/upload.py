from fastapi import APIRouter, HTTPException, status
import uuid
from ..models.schemas import UploadRequest, UploadResponse
from ..services.s3_service import s3_service
from ..utils.helpers import get_settings

router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()


@router.post("", response_model=UploadResponse)
async def request_upload_url(request: UploadRequest) -> UploadResponse:
    """
    Request a presigned URL for uploading a CSV file to S3
    """
    try:
        # Generate unique dataset ID
        dataset_id = str(uuid.uuid4())
        
        # Create S3 key
        s3_key = f"datasets/{dataset_id}/{request.filename}"
        
        # Generate presigned URL
        upload_url = s3_service.generate_presigned_upload_url(
            bucket=settings.s3_bucket_datasets,
            key=s3_key,
            expiration=settings.presigned_url_expiration
        )
        
        return UploadResponse(
            dataset_id=dataset_id,
            upload_url=upload_url,
            expires_in=settings.presigned_url_expiration
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating upload URL: {str(e)}"
        )
