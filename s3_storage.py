"""
AWS S3 Cloud Storage Module (Free Tier Compliant)
Uploads, manages, and versions historical sales CSV datasets in Amazon S3.
Includes seamless local simulation for zero-login, zero-cost execution.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger("DemandForecast.S3")


class S3DatasetStorage:
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.has_credentials = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        self.local_dir = settings.S3_LOCAL_STORAGE
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.s3_client = None

        if self.has_credentials:
            try:
                import boto3
                self.s3_client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                logger.info(f"Connected to AWS S3 Bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"AWS S3 connection failed ({e}). Falling back to Local S3 Simulation.")
                self.has_credentials = False
        else:
            logger.info("Running AWS S3 in Free-Tier Local Simulation Mode (Zero credentials required).")

    def upload_dataset(self, file_bytes: bytes, filename: str) -> dict:
        """
        Uploads a sales dataset CSV to AWS S3 (or local S3 store).
        """
        key = f"datasets/{filename}"

        if self.has_credentials and self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_bytes,
                    ContentType="text/csv"
                )
                s3_uri = f"s3://{self.bucket_name}/{key}"
                # Generate a temporary pre-signed URL (valid 24h)
                presigned_url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": key},
                    ExpiresIn=86400
                )
                return {
                    "storage_provider": "AWS_S3_FREE_TIER",
                    "bucket": self.bucket_name,
                    "key": key,
                    "s3_uri": s3_uri,
                    "access_url": presigned_url,
                    "size_bytes": len(file_bytes)
                }
            except Exception as e:
                logger.error(f"S3 PutObject error: {e}. Falling back to local store.")

        # Local S3 Simulation Fallback
        local_file = self.local_dir / filename
        local_file.write_bytes(file_bytes)
        return {
            "storage_provider": "AWS_S3_LOCAL_SIMULATION",
            "bucket": self.bucket_name,
            "key": key,
            "s3_uri": f"s3://{self.bucket_name}/{key}",
            "access_url": f"/api/s3/download/{filename}",
            "size_bytes": len(file_bytes)
        }

    def read_dataset(self, filename: str) -> Optional[bytes]:
        """Reads dataset bytes from S3 or local simulation store."""
        key = f"datasets/{filename}"
        if self.has_credentials and self.s3_client:
            try:
                resp = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                return resp["Body"].read()
            except Exception:
                pass

        local_file = self.local_dir / filename
        if local_file.exists():
            return local_file.read_bytes()
        return None


# Global S3 Singleton
s3_storage = S3DatasetStorage()
