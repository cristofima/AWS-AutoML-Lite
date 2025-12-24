"""
Integration tests for DynamoDB service using moto.

These tests verify DynamoDB operations work correctly
with a mocked AWS environment.
"""
import pytest
import boto3
from moto import mock_aws
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add API module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))


@pytest.fixture
def dynamodb_tables():
    """Create mocked DynamoDB tables."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create datasets table
        datasets_table = dynamodb.create_table(
            TableName='test-datasets-table',
            KeySchema=[
                {'AttributeName': 'dataset_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'dataset_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create jobs table
        jobs_table = dynamodb.create_table(
            TableName='test-jobs-table',
            KeySchema=[
                {'AttributeName': 'job_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for tables to be created
        datasets_table.meta.client.get_waiter('table_exists').wait(TableName='test-datasets-table')
        jobs_table.meta.client.get_waiter('table_exists').wait(TableName='test-jobs-table')
        
        yield {
            'datasets': datasets_table,
            'jobs': jobs_table,
            'dynamodb': dynamodb
        }


class TestDynamoDBDatasetOperations:
    """Test DynamoDB dataset CRUD operations."""
    
    @pytest.mark.integration
    def test_create_and_get_dataset(self, dynamodb_tables):
        """Create a dataset and retrieve it."""
        datasets_table = dynamodb_tables['datasets']
        
        # Create dataset
        dataset_item = {
            'dataset_id': 'test-dataset-001',
            'filename': 'sales_data.csv',
            's3_key': 'datasets/test-dataset-001/sales_data.csv',
            'status': 'pending',
            'uploaded_at': datetime.now(timezone.utc).isoformat(),
        }
        datasets_table.put_item(Item=dataset_item)
        
        # Retrieve dataset
        response = datasets_table.get_item(Key={'dataset_id': 'test-dataset-001'})
        
        assert 'Item' in response
        assert response['Item']['dataset_id'] == 'test-dataset-001'
        assert response['Item']['filename'] == 'sales_data.csv'
        assert response['Item']['status'] == 'pending'
    
    @pytest.mark.integration
    def test_update_dataset_status(self, dynamodb_tables):
        """Update dataset status after confirmation."""
        datasets_table = dynamodb_tables['datasets']
        
        # Create initial dataset
        datasets_table.put_item(Item={
            'dataset_id': 'test-dataset-002',
            'filename': 'data.csv',
            'status': 'pending',
        })
        
        # Update status to confirmed
        datasets_table.update_item(
            Key={'dataset_id': 'test-dataset-002'},
            UpdateExpression='SET #status = :status, row_count = :rows, column_count = :cols',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'confirmed',
                ':rows': 1000,
                ':cols': 10
            }
        )
        
        # Verify update
        response = datasets_table.get_item(Key={'dataset_id': 'test-dataset-002'})
        assert response['Item']['status'] == 'confirmed'
        assert response['Item']['row_count'] == 1000
        assert response['Item']['column_count'] == 10
    
    @pytest.mark.integration
    def test_get_nonexistent_dataset(self, dynamodb_tables):
        """Get operation for non-existent dataset returns no item."""
        datasets_table = dynamodb_tables['datasets']
        
        response = datasets_table.get_item(Key={'dataset_id': 'nonexistent'})
        
        assert 'Item' not in response
    
    @pytest.mark.integration
    def test_delete_dataset(self, dynamodb_tables):
        """Delete a dataset."""
        datasets_table = dynamodb_tables['datasets']
        
        # Create and then delete
        datasets_table.put_item(Item={
            'dataset_id': 'test-dataset-003',
            'filename': 'to_delete.csv',
        })
        
        datasets_table.delete_item(Key={'dataset_id': 'test-dataset-003'})
        
        # Verify deletion
        response = datasets_table.get_item(Key={'dataset_id': 'test-dataset-003'})
        assert 'Item' not in response


class TestDynamoDBJobOperations:
    """Test DynamoDB job CRUD operations."""
    
    @pytest.mark.integration
    def test_create_and_get_job(self, dynamodb_tables):
        """Create a training job and retrieve it."""
        jobs_table = dynamodb_tables['jobs']
        
        job_item = {
            'job_id': 'job-001',
            'dataset_id': 'dataset-001',
            'target_column': 'price',
            'status': 'SUBMITTED',
            'time_budget': 300,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        jobs_table.put_item(Item=job_item)
        
        response = jobs_table.get_item(Key={'job_id': 'job-001'})
        
        assert 'Item' in response
        assert response['Item']['job_id'] == 'job-001'
        assert response['Item']['status'] == 'SUBMITTED'
        assert response['Item']['target_column'] == 'price'
    
    @pytest.mark.integration
    def test_update_job_status_running(self, dynamodb_tables):
        """Update job status to RUNNING."""
        jobs_table = dynamodb_tables['jobs']
        
        # Create initial job
        jobs_table.put_item(Item={
            'job_id': 'job-002',
            'status': 'SUBMITTED',
        })
        
        # Update to RUNNING
        jobs_table.update_item(
            Key={'job_id': 'job-002'},
            UpdateExpression='SET #status = :status, updated_at = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'RUNNING',
                ':updated': datetime.now(timezone.utc).isoformat()
            }
        )
        
        response = jobs_table.get_item(Key={'job_id': 'job-002'})
        assert response['Item']['status'] == 'RUNNING'
    
    @pytest.mark.integration
    def test_update_job_with_metrics(self, dynamodb_tables):
        """Update job with training metrics on completion."""
        from decimal import Decimal
        
        jobs_table = dynamodb_tables['jobs']
        
        # Create job
        jobs_table.put_item(Item={
            'job_id': 'job-003',
            'status': 'RUNNING',
        })
        
        # Update with metrics (DynamoDB requires Decimal for numbers)
        metrics = {
            'accuracy': Decimal('0.95'),
            'f1_score': Decimal('0.94'),
            'training_time': Decimal('120.5')
        }
        
        # Note: 'metrics' is a reserved keyword in DynamoDB, use #metrics alias
        jobs_table.update_item(
            Key={'job_id': 'job-003'},
            UpdateExpression='SET #status = :status, #metrics = :metrics',
            ExpressionAttributeNames={
                '#status': 'status',
                '#metrics': 'metrics'
            },
            ExpressionAttributeValues={
                ':status': 'SUCCEEDED',
                ':metrics': metrics
            }
        )
        
        response = jobs_table.get_item(Key={'job_id': 'job-003'})
        assert response['Item']['status'] == 'SUCCEEDED'
        assert 'metrics' in response['Item']
        assert float(response['Item']['metrics']['accuracy']) == 0.95
    
    @pytest.mark.integration
    def test_update_job_failed_with_error(self, dynamodb_tables):
        """Update job to FAILED with error message."""
        jobs_table = dynamodb_tables['jobs']
        
        # Create job
        jobs_table.put_item(Item={
            'job_id': 'job-004',
            'status': 'RUNNING',
        })
        
        # Update to FAILED
        jobs_table.update_item(
            Key={'job_id': 'job-004'},
            UpdateExpression='SET #status = :status, error_message = :error',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':error': 'Target column not found in dataset'
            }
        )
        
        response = jobs_table.get_item(Key={'job_id': 'job-004'})
        assert response['Item']['status'] == 'FAILED'
        assert 'Target column not found' in response['Item']['error_message']
    
    @pytest.mark.integration
    def test_list_jobs_by_status(self, dynamodb_tables):
        """Scan jobs by status (for listing purposes)."""
        jobs_table = dynamodb_tables['jobs']
        
        # Create multiple jobs with different statuses
        jobs = [
            {'job_id': 'job-a', 'status': 'SUCCEEDED'},
            {'job_id': 'job-b', 'status': 'SUCCEEDED'},
            {'job_id': 'job-c', 'status': 'FAILED'},
            {'job_id': 'job-d', 'status': 'RUNNING'},
        ]
        
        for job in jobs:
            jobs_table.put_item(Item=job)
        
        # Scan for SUCCEEDED jobs
        response = jobs_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'SUCCEEDED'}
        )
        
        assert response['Count'] == 2
        assert all(item['status'] == 'SUCCEEDED' for item in response['Items'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
