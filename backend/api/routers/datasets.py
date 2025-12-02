from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
import pandas as pd
import io
from ..models.schemas import DatasetMetadata
from ..services.s3_service import s3_service
from ..services.dynamo_service import dynamodb_service
from ..utils.helpers import get_settings

router = APIRouter(prefix="/datasets", tags=["datasets"])
settings = get_settings()


@router.post("/{dataset_id}/confirm", response_model=DatasetMetadata)
async def confirm_upload(dataset_id: str):
    """
    Confirm upload and analyze the dataset.
    Reads the CSV from S3, extracts metadata, and saves to DynamoDB.
    """
    try:
        # List objects in the dataset folder to find the CSV
        prefix = f"datasets/{dataset_id}/"
        objects = s3_service.list_objects(
            bucket=settings.s3_bucket_datasets,
            prefix=prefix
        )
        
        if not objects:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No files found for dataset {dataset_id}"
            )
        
        # Get the first CSV file
        csv_key = objects[0]
        filename = csv_key.split("/")[-1]
        
        # Download and analyze the CSV
        csv_content = s3_service.download_file_content(
            bucket=settings.s3_bucket_datasets,
            key=csv_key
        )
        
        # Parse CSV with pandas
        df = pd.read_csv(io.BytesIO(csv_content))
        
        # Extract metadata
        columns = df.columns.tolist()
        row_count = len(df)
        file_size = len(csv_content)
        
        # Determine column types and stats
        column_types = {}
        column_stats = {}
        for col in columns:
            dtype = str(df[col].dtype)
            if 'int' in dtype or 'float' in dtype:
                column_types[col] = 'numeric'
            elif 'datetime' in dtype:
                column_types[col] = 'datetime'
            else:
                column_types[col] = 'categorical'
            
            # Calculate column stats
            missing_count = int(df[col].isna().sum())
            column_stats[col] = {
                'unique': int(df[col].nunique()),
                'missing': missing_count,
                'missing_pct': round(missing_count / row_count * 100, 2) if row_count > 0 else 0
            }
        
        # Create metadata object
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            filename=filename,
            file_size=file_size,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            columns=columns,
            row_count=row_count,
            column_types=column_types,
            column_stats=column_stats
        )
        
        # Save metadata to DynamoDB
        dynamodb_service.save_dataset_metadata(metadata.model_dump())
        
        return metadata
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming upload: {str(e)}"
        )


@router.get("/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(dataset_id: str):
    """
    Get dataset metadata by ID
    """
    try:
        metadata = dynamodb_service.get_dataset_metadata(dataset_id)
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )
        
        return DatasetMetadata(**metadata)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dataset: {str(e)}"
        )
