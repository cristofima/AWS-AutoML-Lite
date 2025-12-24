"""
Integration tests for API services using moto.

These tests verify that S3Service and DynamoDBService classes
work correctly with mocked AWS environments.
"""
import pytest
import boto3
import os
from moto import mock_aws
from datetime import datetime, timezone
from decimal import Decimal
import sys
from pathlib import Path

# Add API module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_REGION'] = 'us-east-1'


@pytest.fixture
def s3_setup(aws_credentials):
    """Create mocked S3 environment with buckets."""
    with mock_aws():
        # Set env vars for service
        os.environ['S3_BUCKET_DATASETS'] = 'test-datasets-bucket'
        os.environ['S3_BUCKET_MODELS'] = 'test-models-bucket'
        os.environ['S3_BUCKET_REPORTS'] = 'test-reports-bucket'
        
        # Create buckets
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-datasets-bucket')
        s3.create_bucket(Bucket='test-models-bucket')
        s3.create_bucket(Bucket='test-reports-bucket')
        
        # Clear settings cache and import fresh
        from api.utils.helpers import get_settings
        get_settings.cache_clear()
        
        # Create fresh S3Service instance
        from api.services.s3_service import S3Service
        service = S3Service()
        
        yield {
            'service': service,
            'client': s3,
            'buckets': {
                'datasets': 'test-datasets-bucket',
                'models': 'test-models-bucket',
                'reports': 'test-reports-bucket'
            }
        }


@pytest.fixture
def dynamodb_setup(aws_credentials):
    """Create mocked DynamoDB environment with tables."""
    with mock_aws():
        # Set env vars for service
        os.environ['DYNAMODB_DATASETS_TABLE'] = 'test-datasets-table'
        os.environ['DYNAMODB_JOBS_TABLE'] = 'test-jobs-table'
        
        # Create tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        datasets_table = dynamodb.create_table(
            TableName='test-datasets-table',
            KeySchema=[{'AttributeName': 'dataset_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'dataset_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        jobs_table = dynamodb.create_table(
            TableName='test-jobs-table',
            KeySchema=[{'AttributeName': 'job_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'job_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for tables
        datasets_table.meta.client.get_waiter('table_exists').wait(TableName='test-datasets-table')
        jobs_table.meta.client.get_waiter('table_exists').wait(TableName='test-jobs-table')
        
        # Clear settings cache and import fresh
        from api.utils.helpers import get_settings
        get_settings.cache_clear()
        
        # Create fresh DynamoDBService instance
        from api.services.dynamo_service import DynamoDBService
        service = DynamoDBService()
        
        yield {
            'service': service,
            'resource': dynamodb,
            'tables': {
                'datasets': datasets_table,
                'jobs': jobs_table
            }
        }


# =============================================================================
# S3Service Integration Tests
# =============================================================================

class TestS3ServicePresignedUrls:
    """Test S3Service presigned URL generation."""
    
    @pytest.mark.integration
    def test_generate_presigned_upload_url(self, s3_setup):
        """S3Service generates valid presigned upload URL."""
        service = s3_setup['service']
        bucket = s3_setup['buckets']['datasets']
        
        url = service.generate_presigned_upload_url(
            bucket=bucket,
            key='datasets/test-123/data.csv',
            expiration=3600
        )
        
        assert url is not None
        assert bucket in url
        assert 'X-Amz-Signature' in url or 'Signature' in url
    
    @pytest.mark.integration
    def test_generate_presigned_download_url(self, s3_setup):
        """S3Service generates valid presigned download URL."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['models']
        key = 'models/job-001/model.pkl'
        
        # Upload a file first
        client.put_object(Bucket=bucket, Key=key, Body=b'model content')
        
        url = service.generate_presigned_download_url(
            bucket=bucket,
            key=key,
            expiration=3600
        )
        
        assert url is not None
        assert bucket in url


class TestS3ServiceObjectOperations:
    """Test S3Service object operations."""
    
    @pytest.mark.integration
    def test_check_object_exists_true(self, s3_setup):
        """S3Service.check_object_exists returns True for existing objects."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['datasets']
        key = 'datasets/exists-test/file.csv'
        
        client.put_object(Bucket=bucket, Key=key, Body=b'content')
        
        assert service.check_object_exists(bucket, key) is True
    
    @pytest.mark.integration
    def test_check_object_exists_false(self, s3_setup):
        """S3Service.check_object_exists returns False for non-existing objects."""
        service = s3_setup['service']
        bucket = s3_setup['buckets']['datasets']
        
        assert service.check_object_exists(bucket, 'nonexistent/file.csv') is False
    
    @pytest.mark.integration
    def test_get_object_size(self, s3_setup):
        """S3Service.get_object_size returns correct file size."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['datasets']
        key = 'datasets/size-test/data.csv'
        content = b'id,name,value\n1,Alice,100\n2,Bob,200'
        
        client.put_object(Bucket=bucket, Key=key, Body=content)
        
        size = service.get_object_size(bucket, key)
        assert size == len(content)
    
    @pytest.mark.integration
    def test_list_objects(self, s3_setup):
        """S3Service.list_objects returns correct object keys."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['datasets']
        
        # Upload multiple files
        files = [
            'datasets/list-test/file1.csv',
            'datasets/list-test/file2.csv',
            'datasets/list-test/subdir/file3.csv',
            'datasets/other/file.csv',
        ]
        for key in files:
            client.put_object(Bucket=bucket, Key=key, Body=b'content')
        
        result = service.list_objects(bucket, 'datasets/list-test/')
        
        assert len(result) == 3
        assert 'datasets/list-test/file1.csv' in result
        assert 'datasets/list-test/file2.csv' in result
        assert 'datasets/list-test/subdir/file3.csv' in result
    
    @pytest.mark.integration
    def test_list_objects_empty_prefix(self, s3_setup):
        """S3Service.list_objects returns empty list for non-existing prefix."""
        service = s3_setup['service']
        bucket = s3_setup['buckets']['datasets']
        
        result = service.list_objects(bucket, 'nonexistent/prefix/')
        
        assert result == []
    
    @pytest.mark.integration
    def test_download_file_content(self, s3_setup):
        """S3Service.download_file_content returns file bytes."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['datasets']
        key = 'datasets/download-test/data.csv'
        original_content = b'id,name,price\n1,Product A,29.99\n2,Product B,49.99'
        
        client.put_object(Bucket=bucket, Key=key, Body=original_content)
        
        downloaded = service.download_file_content(bucket, key)
        
        assert downloaded == original_content
    
    @pytest.mark.integration
    def test_delete_object(self, s3_setup):
        """S3Service.delete_object removes object from bucket."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['datasets']
        key = 'datasets/delete-test/file.csv'
        
        client.put_object(Bucket=bucket, Key=key, Body=b'content')
        
        result = service.delete_object(bucket, key)
        
        assert result is True
        assert service.check_object_exists(bucket, key) is False
    
    @pytest.mark.integration
    def test_delete_folder(self, s3_setup):
        """S3Service.delete_folder removes all objects with prefix."""
        service = s3_setup['service']
        client = s3_setup['client']
        bucket = s3_setup['buckets']['datasets']
        prefix = 'datasets/folder-delete/'
        
        # Upload multiple files
        files = [
            f'{prefix}file1.csv',
            f'{prefix}file2.csv',
            f'{prefix}subdir/file3.csv',
        ]
        for key in files:
            client.put_object(Bucket=bucket, Key=key, Body=b'content')
        
        deleted_count = service.delete_folder(bucket, prefix)
        
        assert deleted_count == 3
        assert service.list_objects(bucket, prefix) == []


# =============================================================================
# DynamoDBService Integration Tests
# =============================================================================

class TestDynamoDBServiceDatasetOperations:
    """Test DynamoDBService dataset operations."""
    
    @pytest.mark.integration
    def test_save_and_get_dataset_metadata(self, dynamodb_setup):
        """DynamoDBService saves and retrieves dataset metadata."""
        service = dynamodb_setup['service']
        
        metadata = {
            'dataset_id': 'ds-001',
            'filename': 'sales_data.csv',
            'file_size': 1024,
            'uploaded_at': '2024-01-15T10:00:00Z',
            'columns': ['id', 'product', 'price', 'quantity'],
            'row_count': 1000,
            'column_types': {'id': 'numeric', 'product': 'categorical', 'price': 'numeric', 'quantity': 'numeric'},
            'column_stats': {
                'id': {'unique': 1000, 'missing': 0, 'missing_pct': 0.0},
                'price': {'unique': 500, 'missing': 10, 'missing_pct': 1.0}
            }
        }
        
        result = service.save_dataset_metadata(metadata)
        assert result is True
        
        retrieved = service.get_dataset_metadata('ds-001')
        
        assert retrieved is not None
        assert retrieved['dataset_id'] == 'ds-001'
        assert retrieved['filename'] == 'sales_data.csv'
        assert retrieved['row_count'] == 1000
        assert 'price' in retrieved['column_types']
    
    @pytest.mark.integration
    def test_get_dataset_metadata_not_found(self, dynamodb_setup):
        """DynamoDBService returns None for non-existing dataset."""
        service = dynamodb_setup['service']
        
        result = service.get_dataset_metadata('nonexistent')
        
        assert result is None


class TestDynamoDBServiceJobOperations:
    """Test DynamoDBService job operations."""
    
    @pytest.mark.integration
    def test_create_and_get_job(self, dynamodb_setup):
        """DynamoDBService creates and retrieves job."""
        service = dynamodb_setup['service']
        
        from api.models.schemas import JobDetails, JobStatus, ProblemType
        
        job = JobDetails(
            job_id='job-001',
            dataset_id='ds-001',
            user_id='default',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=JobStatus.PENDING,
            dataset_name='test.csv',
            target_column='price',
            problem_type=ProblemType.REGRESSION
        )
        
        result = service.create_job(job)
        assert result is True
        
        retrieved = service.get_job('job-001')
        
        assert retrieved is not None
        assert retrieved['job_id'] == 'job-001'
        assert retrieved['status'] == 'pending'
        assert retrieved['target_column'] == 'price'
    
    @pytest.mark.integration
    def test_get_job_not_found(self, dynamodb_setup):
        """DynamoDBService returns None for non-existing job."""
        service = dynamodb_setup['service']
        
        result = service.get_job('nonexistent')
        
        assert result is None
    
    @pytest.mark.integration
    def test_update_job_status(self, dynamodb_setup):
        """DynamoDBService updates job status."""
        service = dynamodb_setup['service']
        tables = dynamodb_setup['tables']
        
        from api.models.schemas import JobStatus
        
        # Create job directly in table
        tables['jobs'].put_item(Item={
            'job_id': 'job-002',
            'status': 'pending',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })
        
        # Update status
        result = service.update_job_status('job-002', JobStatus.RUNNING)
        assert result is True
        
        retrieved = service.get_job('job-002')
        assert retrieved['status'] == 'running'
    
    @pytest.mark.integration
    def test_update_job_status_with_updates(self, dynamodb_setup):
        """DynamoDBService updates job status with additional fields."""
        service = dynamodb_setup['service']
        tables = dynamodb_setup['tables']
        
        from api.models.schemas import JobStatus
        
        # Create job
        tables['jobs'].put_item(Item={
            'job_id': 'job-003',
            'status': 'pending',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })
        
        # Update status with batch job ID
        result = service.update_job_status(
            'job-003',
            JobStatus.RUNNING,
            updates={'batch_job_id': 'arn:aws:batch:us-east-1:123456789:job/abc123'}
        )
        assert result is True
        
        retrieved = service.get_job('job-003')
        assert retrieved['status'] == 'running'
        assert retrieved['batch_job_id'] == 'arn:aws:batch:us-east-1:123456789:job/abc123'
    
    @pytest.mark.integration
    def test_list_jobs(self, dynamodb_setup):
        """DynamoDBService lists jobs with pagination."""
        service = dynamodb_setup['service']
        tables = dynamodb_setup['tables']
        
        # Create multiple jobs
        for i in range(5):
            tables['jobs'].put_item(Item={
                'job_id': f'job-list-{i}',
                'user_id': 'default',
                'status': 'completed',
                'dataset_id': f'ds-{i}',
                'target_column': 'price',
                'created_at': f'2024-01-{15+i}T10:00:00Z',
                'updated_at': f'2024-01-{15+i}T10:30:00Z',
            })
        
        jobs, next_key = service.list_jobs(user_id='default', limit=10)
        
        assert len(jobs) == 5
        # Should be sorted by created_at descending
        assert jobs[0]['created_at'] > jobs[4]['created_at']
    
    @pytest.mark.integration
    def test_delete_job(self, dynamodb_setup):
        """DynamoDBService deletes job."""
        service = dynamodb_setup['service']
        tables = dynamodb_setup['tables']
        
        # Create job
        tables['jobs'].put_item(Item={
            'job_id': 'job-delete-001',
            'status': 'failed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
        })
        
        result = service.delete_job('job-delete-001')
        assert result is True
        
        retrieved = service.get_job('job-delete-001')
        assert retrieved is None
    
    @pytest.mark.integration
    def test_update_job_metadata(self, dynamodb_setup):
        """DynamoDBService updates job tags and notes."""
        service = dynamodb_setup['service']
        tables = dynamodb_setup['tables']
        
        # Create job
        tables['jobs'].put_item(Item={
            'job_id': 'job-meta-001',
            'status': 'completed',
            'dataset_id': 'ds-001',
            'target_column': 'price',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })
        
        # Update metadata
        result = service.update_job_metadata(
            'job-meta-001',
            tags=['experiment-1', 'baseline', 'v1'],
            notes='This is the baseline model with default hyperparameters'
        )
        assert result is True
        
        retrieved = service.get_job('job-meta-001')
        assert retrieved['tags'] == ['experiment-1', 'baseline', 'v1']
        assert 'baseline model' in retrieved['notes']


class TestDynamoDBServiceDecimalConversion:
    """Test DynamoDB Decimal conversion utilities."""
    
    @pytest.mark.integration
    def test_convert_decimals_to_float(self, dynamodb_setup):
        """DynamoDBService converts Decimal to float correctly."""
        service = dynamodb_setup['service']
        
        data = {
            'accuracy': Decimal('0.95'),
            'f1_score': Decimal('0.94'),
            'nested': {
                'value': Decimal('100.5'),
                'list': [Decimal('1.1'), Decimal('2.2')]
            }
        }
        
        converted = service._convert_decimals(data)
        
        assert isinstance(converted['accuracy'], float)
        assert converted['accuracy'] == 0.95
        assert isinstance(converted['nested']['value'], float)
        assert all(isinstance(x, float) for x in converted['nested']['list'])
    
    @pytest.mark.integration
    def test_convert_floats_to_decimal(self, dynamodb_setup):
        """DynamoDBService converts float to Decimal for storage."""
        service = dynamodb_setup['service']
        
        data = {
            'accuracy': 0.95,
            'nested': {
                'value': 100.5,
                'list': [1.1, 2.2]
            }
        }
        
        converted = service._convert_floats_to_decimal(data)
        
        assert isinstance(converted['accuracy'], Decimal)
        assert converted['accuracy'] == Decimal('0.95')
        assert isinstance(converted['nested']['value'], Decimal)
        assert all(isinstance(x, Decimal) for x in converted['nested']['list'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
