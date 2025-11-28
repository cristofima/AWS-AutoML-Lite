import boto3
from datetime import datetime
from typing import Optional, List
from botocore.exceptions import ClientError
from ..utils.helpers import get_settings

settings = get_settings()


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.aws_region)
    
    def generate_presigned_upload_url(
        self, 
        bucket: str, 
        key: str, 
        expiration: int = 3600
    ) -> str:
        """Generate a presigned URL for uploading to S3"""
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket,
                    'Key': key,
                    'ContentType': 'text/csv'
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    def generate_presigned_download_url(
        self, 
        bucket: str, 
        key: str, 
        expiration: int = 3600
    ) -> str:
        """Generate a presigned URL for downloading from S3"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    def check_object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in S3"""
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def get_object_size(self, bucket: str, key: str) -> int:
        """Get the size of an object in S3"""
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            return response['ContentLength']
        except ClientError as e:
            raise Exception(f"Error getting object size: {str(e)}")
    
    def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from S3"""
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            raise Exception(f"Error deleting object: {str(e)}")


# Singleton instance
s3_service = S3Service()
