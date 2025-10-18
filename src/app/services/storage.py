"""S3/MinIO storage abstraction for document uploads"""

import logging
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ..core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Abstraction over S3/MinIO for document storage"""

    def __init__(self) -> None:
        self.bucket = settings.STORAGE_BUCKET
        self.client = self._create_client()

    def _create_client(self):
        """Create S3/MinIO client"""
        config = Config(signature_version="s3v4", s3={"addressing_style": "path"})

        kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.STORAGE_ACCESS_KEY,
            "aws_secret_access_key": settings.STORAGE_SECRET_KEY,
            "config": config,
        }

        if settings.STORAGE_ENDPOINT_URL:
            # MinIO or R2
            kwargs["endpoint_url"] = settings.STORAGE_ENDPOINT_URL
        else:
            # AWS S3
            kwargs["region_name"] = settings.STORAGE_REGION

        return boto3.client(**kwargs)

    async def put_object(self, key: str, file_obj: BinaryIO, content_type: str) -> str:
        """Upload file to storage"""
        try:
            self.client.upload_fileobj(
                file_obj, self.bucket, key, ExtraArgs={"ContentType": content_type}
            )
            uri = f"s3://{self.bucket}/{key}"
            logger.info(f"Uploaded object to {uri}")
            return uri
        except ClientError as e:
            logger.error(f"Failed to upload object: {e}")
            raise

    async def get_object(self, key: str) -> bytes:
        """Download file from storage"""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to get object {key}: {e}")
            raise

    async def delete_object(self, key: str) -> None:
        """Delete file from storage"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted object {key}")
        except ClientError as e:
            logger.error(f"Failed to delete object {key}: {e}")
            raise

    def parse_uri(self, uri: str) -> str:
        """Extract key from S3 URI"""
        if uri.startswith("s3://"):
            parts = uri.replace("s3://", "").split("/", 1)
            if len(parts) == 2:
                return parts[1]
        return uri


# Singleton instance
storage_service = StorageService()
