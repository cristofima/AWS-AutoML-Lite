"""
Integration tests for S3 service using moto.

These tests verify S3 operations work correctly
with a mocked AWS environment.
"""
import pytest
import boto3
from moto import mock_aws
import sys
from pathlib import Path

# Add API module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))


@pytest.fixture
def s3_bucket():
    """Create mocked S3 bucket."""
    with mock_aws():
        s3 = boto3.client('s3', region_name='us-east-1')
        
        # Create test buckets
        s3.create_bucket(Bucket='test-datasets-bucket')
        s3.create_bucket(Bucket='test-models-bucket')
        s3.create_bucket(Bucket='test-reports-bucket')
        
        yield {
            'client': s3,
            'datasets_bucket': 'test-datasets-bucket',
            'models_bucket': 'test-models-bucket',
            'reports_bucket': 'test-reports-bucket'
        }


class TestS3UploadOperations:
    """Test S3 upload operations."""
    
    @pytest.mark.integration
    def test_upload_csv_file(self, s3_bucket):
        """Upload a CSV file to S3."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        
        csv_content = b"id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300"
        key = "datasets/test-001/data.csv"
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_content,
            ContentType='text/csv'
        )
        
        # Verify upload
        response = s3.get_object(Bucket=bucket, Key=key)
        assert response['Body'].read() == csv_content
        assert response['ContentType'] == 'text/csv'
    
    @pytest.mark.integration
    def test_upload_model_pickle(self, s3_bucket):
        """Upload a model pickle file to S3."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['models_bucket']
        
        # Simulate pickle content
        model_content = b"fake pickle content for testing"
        key = "models/job-001/model.pkl"
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=model_content,
            ContentType='application/octet-stream'
        )
        
        # Verify upload
        response = s3.head_object(Bucket=bucket, Key=key)
        assert response['ContentLength'] == len(model_content)
    
    @pytest.mark.integration
    def test_generate_presigned_url(self, s3_bucket):
        """Generate presigned URL for upload."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        key = "datasets/test-002/upload.csv"
        
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=3600
        )
        
        assert url is not None
        assert bucket in url
        assert 'Signature' in url or 'X-Amz-Signature' in url


class TestS3DownloadOperations:
    """Test S3 download operations."""
    
    @pytest.mark.integration
    def test_download_csv_file(self, s3_bucket):
        """Download a CSV file from S3."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        key = "datasets/test-003/data.csv"
        
        # Upload first
        original_content = b"col1,col2,col3\na,b,c\nd,e,f"
        s3.put_object(Bucket=bucket, Key=key, Body=original_content)
        
        # Download
        response = s3.get_object(Bucket=bucket, Key=key)
        downloaded_content = response['Body'].read()
        
        assert downloaded_content == original_content
    
    @pytest.mark.integration
    def test_download_nonexistent_file(self, s3_bucket):
        """Download non-existent file raises error."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        
        with pytest.raises(s3.exceptions.NoSuchKey):
            s3.get_object(Bucket=bucket, Key='nonexistent/file.csv')
    
    @pytest.mark.integration
    def test_generate_presigned_download_url(self, s3_bucket):
        """Generate presigned URL for download."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['models_bucket']
        key = "models/job-002/model.pkl"
        
        # Upload first
        s3.put_object(Bucket=bucket, Key=key, Body=b"model content")
        
        # Generate download URL
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=3600
        )
        
        assert url is not None
        assert bucket in url


class TestS3ListOperations:
    """Test S3 list operations."""
    
    @pytest.mark.integration
    def test_list_objects_in_prefix(self, s3_bucket):
        """List objects with a specific prefix."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        
        # Upload multiple files
        files = [
            "datasets/ds-001/data.csv",
            "datasets/ds-001/metadata.json",
            "datasets/ds-002/data.csv",
        ]
        
        for file_key in files:
            s3.put_object(Bucket=bucket, Key=file_key, Body=b"content")
        
        # List objects for ds-001
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="datasets/ds-001/"
        )
        
        assert response['KeyCount'] == 2
        keys = [obj['Key'] for obj in response['Contents']]
        assert "datasets/ds-001/data.csv" in keys
        assert "datasets/ds-001/metadata.json" in keys
    
    @pytest.mark.integration
    def test_list_empty_prefix(self, s3_bucket):
        """List objects with prefix that has no matches."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="nonexistent/prefix/"
        )
        
        assert response['KeyCount'] == 0
        assert 'Contents' not in response


class TestS3DeleteOperations:
    """Test S3 delete operations."""
    
    @pytest.mark.integration
    def test_delete_single_object(self, s3_bucket):
        """Delete a single object."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        key = "datasets/to-delete/file.csv"
        
        # Upload and then delete
        s3.put_object(Bucket=bucket, Key=key, Body=b"content")
        s3.delete_object(Bucket=bucket, Key=key)
        
        # Verify deletion
        with pytest.raises(s3.exceptions.NoSuchKey):
            s3.get_object(Bucket=bucket, Key=key)
    
    @pytest.mark.integration
    def test_delete_multiple_objects(self, s3_bucket):
        """Delete multiple objects at once."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        
        # Upload multiple files
        keys = [f"datasets/batch-delete/{i}.csv" for i in range(5)]
        for key in keys:
            s3.put_object(Bucket=bucket, Key=key, Body=b"content")
        
        # Delete all
        s3.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': [{'Key': key} for key in keys]
            }
        )
        
        # Verify all deleted
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="datasets/batch-delete/"
        )
        assert response['KeyCount'] == 0


class TestS3MetadataOperations:
    """Test S3 object metadata operations."""
    
    @pytest.mark.integration
    def test_head_object(self, s3_bucket):
        """Get object metadata without downloading content."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        key = "datasets/metadata-test/file.csv"
        
        content = b"id,value\n1,100\n2,200"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType='text/csv',
            Metadata={'row-count': '2', 'column-count': '2'}
        )
        
        response = s3.head_object(Bucket=bucket, Key=key)
        
        assert response['ContentLength'] == len(content)
        assert response['ContentType'] == 'text/csv'
        assert response['Metadata']['row-count'] == '2'
    
    @pytest.mark.integration
    def test_object_exists(self, s3_bucket):
        """Check if object exists using head_object."""
        s3 = s3_bucket['client']
        bucket = s3_bucket['datasets_bucket']
        
        # Upload file
        s3.put_object(Bucket=bucket, Key="exists.csv", Body=b"content")
        
        # Check exists
        try:
            s3.head_object(Bucket=bucket, Key="exists.csv")
            exists = True
        except s3.exceptions.ClientError:
            exists = False
        
        assert exists == True
        
        # Check not exists
        try:
            s3.head_object(Bucket=bucket, Key="not-exists.csv")
            not_exists = True
        except s3.exceptions.ClientError:
            not_exists = False
        
        assert not_exists == False



class TestS3CacheOperations:
    """Test S3 Service in-memory caching"""

    def test_presigned_url_caching(self, s3_bucket):
        """Repeated calls for same key return cached URL within TTL."""
        from datetime import datetime, timedelta
        from api.services.s3_service import s3_service
        
        bucket = "test-bucket"
        key = "cache-test.csv"
        
        # 1. First call - generates new URL
        url1 = s3_service.generate_presigned_download_url_cached(bucket, key, expiration=3600)
        
        # 2. Second call - should match first URL (cache hit)
        url2 = s3_service.generate_presigned_download_url_cached(bucket, key, expiration=3600)
        assert url1 == url2
        
        # Verify it's in cache
        assert (bucket, key) in s3_service._url_cache

    def test_presigned_url_expiry(self, s3_bucket):
        """Expired entries trigger new URL generation."""
        from datetime import datetime, timedelta
        from api.services.s3_service import s3_service
        import time
        
        bucket = "test-bucket"
        key = "expiry-test.csv"
        
        # 1. Generate URL with short internal TTL (mocking logic)
        # We can't easily mock inner datetime of the service without patching,
        # but we can manually manipulate the cache for testing.
        
        url1 = s3_service.generate_presigned_download_url_cached(bucket, key)
        
        # Manually set expiry to the past
        past_time = datetime.utcnow() - timedelta(seconds=1)
        s3_service._url_cache[(bucket, key)] = (url1, past_time)
        
        # 2. Call again - should generate NEW URL because cache entry is expired
        url2 = s3_service.generate_presigned_download_url_cached(bucket, key)
        
        # Ideally url2 != url1, but AWS presigned URLs are deterministic if params are same.
        # However, generate_presigned_download_url_cached implementation logs "Cache MISS"
        # and re-inserts. We can verify the expiry updated.
        
        new_cached_url, new_expiry = s3_service._url_cache[(bucket, key)]
        assert new_expiry > datetime.utcnow()

    def test_lazy_cleanup(self, s3_bucket):
        """Expired entries are removed from cache on access."""
        from datetime import datetime, timedelta
        from api.services.s3_service import s3_service
        
        bucket = "test-bucket"
        key_expired = "expired.csv"
        key_active = "active.csv"
        
        # 1. Populate cache
        now = datetime.utcnow()
        s3_service._url_cache[(bucket, key_expired)] = ("http://old", now - timedelta(seconds=10))
        s3_service._url_cache[(bucket, key_active)] = ("http://new", now + timedelta(seconds=3600))
        
        # 2. Access cache (trigger cleanup)
        # We access a different key to trigger the global scan
        s3_service.generate_presigned_download_url_cached(bucket, "trigger.csv")
        
        # 3. Verify expired key is gone
        assert (bucket, key_expired) not in s3_service._url_cache
        # 4. Verify active key remains
        assert (bucket, key_active) in s3_service._url_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
