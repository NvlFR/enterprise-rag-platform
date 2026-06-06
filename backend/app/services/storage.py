import logging
from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.s3_config = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "endpoint_url": settings.S3_ENDPOINT,
            "region_name": settings.S3_REGION,
            "use_ssl": settings.S3_USE_SSL,
        }
        self.bucket = settings.S3_BUCKET

    async def initialize_bucket(self):
        """Ensure the bucket exists."""
        async with self.session.client("s3", **self.s3_config) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket)
                logger.info(f"Bucket {self.bucket} already exists.")
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "404":
                    logger.info(f"Bucket {self.bucket} does not exist. Creating...")
                    await s3.create_bucket(Bucket=self.bucket)
                    logger.info(f"Bucket {self.bucket} created successfully.")
                else:
                    logger.error(f"Error checking bucket {self.bucket}: {e}")
                    raise

    async def upload_file(
        self, file: BinaryIO, key: str, content_type: str = None
    ) -> str:
        """Upload a file to S3/MinIO."""
        async with self.session.client("s3", **self.s3_config) as s3:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            try:
                await s3.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args)
                logger.info(f"File {key} uploaded successfully to {self.bucket}.")
                return f"s3://{self.bucket}/{key}"
            except Exception as e:
                logger.error(f"Failed to upload file {key} to {self.bucket}: {e}")
                raise

    async def download_file(self, key: str, destination: str):
        """Download a file from S3/MinIO."""
        async with self.session.client("s3", **self.s3_config) as s3:
            try:
                await s3.download_file(self.bucket, key, destination)
                logger.info(f"File {key} downloaded successfully from {self.bucket}.")
            except Exception as e:
                logger.error(f"Failed to download file {key} from {self.bucket}: {e}")
                raise

    async def delete_file(self, key: str):
        """Delete a file from S3/MinIO."""
        async with self.session.client("s3", **self.s3_config) as s3:
            try:
                await s3.delete_object(Bucket=self.bucket, Key=key)
                logger.info(f"File {key} deleted successfully from {self.bucket}.")
            except Exception as e:
                logger.error(f"Failed to delete file {key} from {self.bucket}: {e}")
                raise

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed URL for an object."""
        async with self.session.client("s3", **self.s3_config) as s3:
            try:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate pre-signed URL for {key}: {e}")
                raise


storage_service = StorageService()
