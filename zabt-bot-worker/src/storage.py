"""S3 storage client for uploading recorded audio with retry."""

import time

import boto3
from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each attempt


def upload_audio(file_path: str, key: str, content_type: str = "audio/wav") -> str:
    """Upload an audio file to S3 with retry. Returns the key."""
    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with open(file_path, "rb") as f:
                client.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=key,
                    Body=f,
                    ContentType=content_type,
                )
            logger.info("Uploaded audio to s3://%s/%s", settings.S3_BUCKET_NAME, key)
            return key
        except Exception as e:
            last_error = e
            wait = RETRY_BACKOFF * (2 ** attempt)
            logger.warning(
                "S3 upload attempt %d/%d failed: %s. Retrying in %ds",
                attempt + 1, MAX_RETRIES, e, wait,
            )
            time.sleep(wait)

    raise RuntimeError(f"S3 upload failed after {MAX_RETRIES} attempts: {last_error}")
