"""
Meet Bot - R2 Uploader
Uploads recordings to Cloudflare R2
"""
import logging
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig

from .config import config

logger = logging.getLogger(__name__)


class R2Uploader:
    """Handles uploading files to Cloudflare R2"""
    
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version="s3v4"),
            region_name="auto"
        )
        self.bucket = config.R2_BUCKET_NAME
    
    def upload_recording(
        self,
        local_path: Path,
        user_id: str,
        meeting_id: str
    ) -> str:
        """
        Upload recording to R2
        
        Returns the storage path (key) in R2
        """
        # Build storage path: recordings/{user_id}/{meeting_id}/video.mp4
        storage_path = f"recordings/{user_id}/{meeting_id}/{local_path.name}"
        
        logger.info(f"Uploading {local_path} to R2: {storage_path}")
        
        try:
            # Get file size for progress logging
            file_size = local_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"File size: {file_size_mb:.2f} MB")
            
            # Upload with content type
            content_type = "video/mp4" if local_path.suffix == ".mp4" else "audio/mpeg"
            
            self.client.upload_file(
                str(local_path),
                self.bucket,
                storage_path,
                ExtraArgs={
                    "ContentType": content_type
                }
            )
            
            logger.info(f"Upload complete: {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Failed to upload to R2: {e}")
            raise
    
    def upload_transcription(
        self,
        local_path: Path,
        user_id: str,
        meeting_id: str
    ) -> str:
        """
        Upload transcription txt file to R2
        
        Returns the storage path (key) in R2
        """
        storage_path = f"recordings/{user_id}/{meeting_id}/transcription.txt"
        
        logger.info(f"Uploading transcription {local_path} to R2: {storage_path}")
        
        try:
            self.client.upload_file(
                str(local_path),
                self.bucket,
                storage_path,
                ExtraArgs={
                    "ContentType": "text/plain; charset=utf-8"
                }
            )
            
            logger.info(f"Transcription upload complete: {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Failed to upload transcription to R2: {e}")
            raise
    
    
    def upload_captions_json(
        self,
        local_path: Path,
        user_id: str,
        meeting_id: str
    ) -> str:
        """
        Upload captions JSON file to R2
        
        Returns the storage path (key) in R2
        """
        storage_path = f"recordings/{user_id}/{meeting_id}/captions.json"
        
        logger.info(f"Uploading captions JSON {local_path} to R2: {storage_path}")
        
        try:
            self.client.upload_file(
                str(local_path),
                self.bucket,
                storage_path,
                ExtraArgs={
                    "ContentType": "application/json"
                }
            )
            
            logger.info(f"Captions JSON upload complete: {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Failed to upload captions JSON to R2: {e}")
            raise

    def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600
    ) -> str:
        """Generate a presigned URL for a file"""
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": storage_path
            },
            ExpiresIn=expiration
        )
