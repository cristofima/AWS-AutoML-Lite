import boto3
from typing import Dict, Any
from botocore.exceptions import ClientError
from ..utils.helpers import get_settings

settings = get_settings()


class BatchService:
    def __init__(self):
        self.batch_client = boto3.client('batch', region_name=settings.aws_region)
    
    def submit_training_job(
        self,
        job_name: str,
        dataset_id: str,
        target_column: str,
        job_id: str,
        config: Dict[str, Any]
    ) -> str:
        """Submit a training job to AWS Batch"""
        try:
            response = self.batch_client.submit_job(
                jobName=job_name,
                jobQueue=settings.batch_job_queue,
                jobDefinition=settings.batch_job_definition,
                parameters={
                    'dataset_id': dataset_id,
                    'target_column': target_column,
                    'job_id': job_id,
                    'time_budget': str(config.get('time_budget', 300)),
                    'metric': config.get('metric', 'auto')
                },
                containerOverrides={
                    'environment': [
                        {'name': 'DATASET_ID', 'value': dataset_id},
                        {'name': 'TARGET_COLUMN', 'value': target_column},
                        {'name': 'JOB_ID', 'value': job_id},
                        {'name': 'TIME_BUDGET', 'value': str(config.get('time_budget', 300))},
                        {'name': 'S3_BUCKET_DATASETS', 'value': settings.s3_bucket_datasets},
                        {'name': 'S3_BUCKET_MODELS', 'value': settings.s3_bucket_models},
                        {'name': 'S3_BUCKET_REPORTS', 'value': settings.s3_bucket_reports},
                        {'name': 'DYNAMODB_JOBS_TABLE', 'value': settings.dynamodb_jobs_table},
                        {'name': 'REGION', 'value': settings.aws_region}
                    ]
                }
            )
            return response['jobId']
        except ClientError as e:
            raise Exception(f"Error submitting batch job: {str(e)}")
    
    def get_job_status(self, batch_job_id: str) -> Dict[str, Any] | None:
        """Get the status of a batch job"""
        try:
            response = self.batch_client.describe_jobs(jobs=[batch_job_id])
            if response['jobs']:
                job = response['jobs'][0]
                return {
                    'status': job['status'],
                    'statusReason': job.get('statusReason'),
                    'createdAt': job.get('createdAt'),
                    'startedAt': job.get('startedAt'),
                    'stoppedAt': job.get('stoppedAt')
                }
            return None
        except ClientError as e:
            raise Exception(f"Error getting batch job status: {str(e)}")


# Singleton instance
batch_service = BatchService()
