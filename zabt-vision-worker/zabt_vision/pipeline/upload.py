import io
import json
from typing import Any

from PIL import Image


def upload_keyframe_jpg(
    client,
    bucket: str,
    owner_id: str,
    meeting_id: str,
    segment_id: str,
    image: Image.Image,
    quality: int = 90,
) -> str:
    key = f"users/{owner_id}/meetings/{meeting_id}/visual/{segment_id}.jpg"
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buf.getvalue(),
        ContentType="image/jpeg",
    )
    return key


def upload_raw_output_json(
    client,
    bucket: str,
    owner_id: str,
    meeting_id: str,
    payload: dict[str, Any],
) -> str:
    key = f"users/{owner_id}/meetings/{meeting_id}/visual/raw_output.json"
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, default=str),
        ContentType="application/json",
    )
    return key


def make_s3_client(settings):
    """Lazy factory — kept here so tests don't need boto3 imported."""
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
