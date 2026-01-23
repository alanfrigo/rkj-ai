"""
Meeting Assistant - Cloudflare R2 Client
S3-compatible storage client for R2
"""
import boto3
from botocore.config import Config
from typing import Optional, BinaryIO
from contextlib import contextmanager
import logging
from datetime import datetime
import mimetypes

from ..config import settings

logger = logging.getLogger(__name__)


def get_r2_client():
    """Create R2 client using boto3 S3 interface"""
    return boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            }
        ),
        region_name='auto'  # R2 uses 'auto' region
    )


class R2Storage:
    """Cloudflare R2 storage operations"""
    
    def __init__(self):
        self.client = get_r2_client()
        self.bucket = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
    
    def _get_content_type(self, filename: str) -> str:
        """Get MIME type for file"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def upload_file(
        self,
        file_path: str,
        storage_path: str,
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to R2
        
        Args:
            file_path: Local file path
            storage_path: Destination path in R2 (e.g., "recordings/user123/meeting456/video.mp4")
            content_type: Optional MIME type
        
        Returns:
            dict with storage_path and url
        """
        if content_type is None:
            content_type = self._get_content_type(file_path)
        
        logger.info(f"Uploading {file_path} to R2: {storage_path}")
        
        with open(file_path, 'rb') as f:
            self.client.upload_fileobj(
                f,
                self.bucket,
                storage_path,
                ExtraArgs={
                    'ContentType': content_type
                }
            )
        
        url = f"{self.public_url}/{storage_path}" if self.public_url else None
        
        logger.info(f"Upload complete: {storage_path}")
        
        return {
            "storage_path": storage_path,
            "storage_url": url,
            "bucket": self.bucket
        }
    
    def upload_bytes(
        self,
        data: bytes,
        storage_path: str,
        content_type: str = 'application/octet-stream'
    ) -> dict:
        """Upload bytes directly to R2"""
        from io import BytesIO
        
        logger.info(f"Uploading bytes to R2: {storage_path}")
        
        self.client.upload_fileobj(
            BytesIO(data),
            self.bucket,
            storage_path,
            ExtraArgs={
                'ContentType': content_type
            }
        )
        
        url = f"{self.public_url}/{storage_path}" if self.public_url else None
        
        return {
            "storage_path": storage_path,
            "storage_url": url,
            "bucket": self.bucket
        }
    
    def download_file(self, storage_path: str, local_path: str) -> str:
        """
        Download a file from R2
        
        Args:
            storage_path: Path in R2
            local_path: Local destination path
        
        Returns:
            Local file path
        """
        logger.info(f"Downloading from R2: {storage_path} -> {local_path}")
        
        self.client.download_file(
            self.bucket,
            storage_path,
            local_path
        )
        
        logger.info(f"Download complete: {local_path}")
        return local_path
    
    def download_bytes(self, storage_path: str) -> bytes:
        """Download file as bytes"""
        from io import BytesIO
        
        buffer = BytesIO()
        self.client.download_fileobj(
            self.bucket,
            storage_path,
            buffer
        )
        buffer.seek(0)
        return buffer.read()
    
    def get_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> str:
        """
        Generate a presigned URL for temporary access
        
        Args:
            storage_path: Path in R2
            expiration: URL expiration in seconds (default 1 hour)
            method: 'get_object' for download, 'put_object' for upload
        
        Returns:
            Presigned URL string
        """
        url = self.client.generate_presigned_url(
            method,
            Params={
                'Bucket': self.bucket,
                'Key': storage_path
            },
            ExpiresIn=expiration
        )
        
        return url
    
    def delete_file(self, storage_path: str) -> bool:
        """Delete a file from R2"""
        logger.info(f"Deleting from R2: {storage_path}")
        
        self.client.delete_object(
            Bucket=self.bucket,
            Key=storage_path
        )
        
        return True
    
    def delete_folder(self, prefix: str) -> int:
        """
        Delete all files with a given prefix
        
        Args:
            prefix: Folder prefix (e.g., "recordings/user123/meeting456/")
        
        Returns:
            Number of files deleted
        """
        logger.info(f"Deleting folder from R2: {prefix}")
        
        # List all objects with prefix
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return 0
        
        # Delete all objects
        objects = [{'Key': obj['Key']} for obj in response['Contents']]
        
        self.client.delete_objects(
            Bucket=self.bucket,
            Delete={'Objects': objects}
        )
        
        deleted_count = len(objects)
        logger.info(f"Deleted {deleted_count} files from {prefix}")
        
        return deleted_count
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> list:
        """
        List files in R2 with optional prefix
        
        Args:
            prefix: Filter by prefix
            max_keys: Maximum number of keys to return
        
        Returns:
            List of file info dicts
        """
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        if 'Contents' not in response:
            return []
        
        return [
            {
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
                'etag': obj['ETag'].strip('"')
            }
            for obj in response['Contents']
        ]
    
    def file_exists(self, storage_path: str) -> bool:
        """Check if a file exists in R2"""
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=storage_path
            )
            return True
        except self.client.exceptions.ClientError:
            return False
    
    def get_file_info(self, storage_path: str) -> Optional[dict]:
        """Get file metadata"""
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=storage_path
            )
            return {
                'key': storage_path,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"')
            }
        except self.client.exceptions.ClientError:
            return None


# Helper function to generate storage paths
def generate_storage_path(
    user_id: str,
    meeting_id: str,
    filename: str,
    folder: str = 'recordings'
) -> str:
    """
    Generate a standardized storage path
    
    Format: {folder}/{user_id}/{meeting_id}/{filename}
    Example: recordings/abc123/def456/video.mp4
    """
    return f"{folder}/{user_id}/{meeting_id}/{filename}"


# Singleton instance
_r2_storage: Optional[R2Storage] = None


def get_r2_storage() -> R2Storage:
    """Get R2 storage singleton"""
    global _r2_storage
    if _r2_storage is None:
        _r2_storage = R2Storage()
    return _r2_storage
