import boto3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
from botocore.exceptions import ClientError
from ..utils.helpers import get_settings
from ..models.schemas import DatasetMetadata, JobDetails, JobStatus

settings = get_settings()


class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        self.datasets_table = self.dynamodb.Table(settings.dynamodb_datasets_table)
        self.jobs_table = self.dynamodb.Table(settings.dynamodb_jobs_table)
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, list):
            return [self._convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert float objects to Decimal for DynamoDB storage"""
        if isinstance(obj, list):
            return [self._convert_floats_to_decimal(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, float):
            return Decimal(str(obj))
        return obj
    
    # Dataset operations
    def create_dataset(self, dataset: DatasetMetadata) -> bool:
        """Create a new dataset record"""
        try:
            item = dataset.model_dump()
            item['uploaded_at'] = item['uploaded_at'].isoformat()
            self.datasets_table.put_item(Item=item)
            return True
        except ClientError as e:
            raise Exception(f"Error creating dataset: {str(e)}")
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """Get a dataset by ID"""
        try:
            response = self.datasets_table.get_item(Key={'dataset_id': dataset_id})
            return self._convert_decimals(response.get('Item'))
        except ClientError as e:
            raise Exception(f"Error getting dataset: {str(e)}")
    
    def update_dataset(self, dataset_id: str, updates: Dict) -> bool:
        """Update a dataset record"""
        try:
            update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
            expr_attr_names = {f"#{k}": k for k in updates.keys()}
            expr_attr_values = {f":{k}": v for k, v in updates.items()}
            
            self.datasets_table.update_item(
                Key={'dataset_id': dataset_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )
            return True
        except ClientError as e:
            raise Exception(f"Error updating dataset: {str(e)}")
    
    # Job operations
    def create_job(self, job: JobDetails) -> bool:
        """Create a new training job record"""
        try:
            item = job.model_dump()
            item['created_at'] = item['created_at'].isoformat()
            item['updated_at'] = item['updated_at'].isoformat()
            if item.get('metrics'):
                item['metrics'] = {k: Decimal(str(v)) if v is not None else None 
                                  for k, v in item['metrics'].items()}
            self.jobs_table.put_item(Item=item)
            return True
        except ClientError as e:
            raise Exception(f"Error creating job: {str(e)}")
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get a training job by ID"""
        try:
            response = self.jobs_table.get_item(Key={'job_id': job_id})
            return self._convert_decimals(response.get('Item'))
        except ClientError as e:
            raise Exception(f"Error getting job: {str(e)}")
    
    def update_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        updates: Optional[Dict] = None
    ) -> bool:
        """Update job status and optional additional fields"""
        try:
            update_data = {
                'status': status.value,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            if updates:
                update_data.update(updates)
            
            update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
            expr_attr_names = {f"#{k}": k for k in update_data.keys()}
            expr_attr_values = {f":{k}": v for k, v in update_data.items()}
            
            self.jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )
            return True
        except ClientError as e:
            raise Exception(f"Error updating job status: {str(e)}")
    
    def list_jobs(
        self, 
        user_id: str = "default", 
        limit: int = 20,
        last_evaluated_key: Optional[Dict] = None
    ) -> tuple[List[Dict], Optional[Dict]]:
        """List training jobs for a user with pagination"""
        try:
            scan_kwargs = {
                'Limit': limit,
                'FilterExpression': 'user_id = :uid',
                'ExpressionAttributeValues': {':uid': user_id}
            }
            
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
            
            response = self.jobs_table.scan(**scan_kwargs)
            items = self._convert_decimals(response.get('Items', []))
            next_key = response.get('LastEvaluatedKey')
            
            return items, next_key
        except ClientError as e:
            raise Exception(f"Error listing jobs: {str(e)}")
    
    def save_dataset_metadata(self, metadata: Dict) -> bool:
        """Save dataset metadata to DynamoDB"""
        try:
            # Convert floats to Decimal for DynamoDB compatibility
            item = self._convert_floats_to_decimal(metadata)
            self.datasets_table.put_item(Item=item)
            return True
        except ClientError as e:
            raise Exception(f"Error saving dataset metadata: {str(e)}")
    
    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict]:
        """Get dataset metadata by ID"""
        try:
            response = self.datasets_table.get_item(Key={'dataset_id': dataset_id})
            return self._convert_decimals(response.get('Item'))
        except ClientError as e:
            raise Exception(f"Error getting dataset metadata: {str(e)}")
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a training job record"""
        try:
            self.jobs_table.delete_item(Key={'job_id': job_id})
            return True
        except ClientError as e:
            raise Exception(f"Error deleting job: {str(e)}")
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset record"""
        try:
            self.datasets_table.delete_item(Key={'dataset_id': dataset_id})
            return True
        except ClientError as e:
            raise Exception(f"Error deleting dataset: {str(e)}")


# Singleton instance
dynamodb_service = DynamoDBService()
