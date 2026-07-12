from typing import Protocol, runtime_checkable
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


@runtime_checkable
class StorageProvider(Protocol):
    """Abstract storage interface — all storage backends must satisfy this."""

    @property
    def provider_name(self) -> str: ...

    def generate_presigned_upload_url(
        self, user_id: int, filename: str, content_type: str, expiration: int = 3600
    ) -> tuple[str, str]: ...

    def get_presigned_download_url(self, object_key: str, expiration: int = 3600) -> str: ...

    def get_public_presigned_download_url(self, object_key: str, expiration: int = 3600) -> str: ...

    def upload_file(self, file_data: bytes, object_key: str, content_type: str) -> None: ...

    def delete_file(self, object_key: str) -> None: ...

    def delete_prefix(self, prefix: str) -> int:
        """Delete every object whose key starts with `prefix`. Returns the count
        deleted. Used for cascading cleanup (e.g., when a meeting is deleted)."""
        ...

    def create_multipart_upload(
        self, user_id: int, filename: str, content_type: str
    ) -> tuple[str, str]:
        """Start an S3 multipart upload. Returns (upload_id, object_key)."""
        ...

    def generate_part_url(
        self, object_key: str, upload_id: str, part_number: int, expiration: int = 3600
    ) -> str:
        """Return a presigned URL for uploading a single part."""
        ...

    def complete_multipart_upload(
        self, object_key: str, upload_id: str, parts: list[dict]
    ) -> None:
        """Finalize a multipart upload. `parts` is a list of {PartNumber, ETag} dicts."""
        ...

    def abort_multipart_upload(self, object_key: str, upload_id: str) -> None:
        """Abort an in-progress multipart upload (releases all stored parts)."""
        ...

    def list_pending_multipart_uploads(self, older_than_hours: int = 24) -> list[dict]:
        """Return list of {Key, UploadId, Initiated} for uploads older than given hours."""
        ...


def _make_object_key(user_id: int, filename: str) -> str:
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    return f"users/{user_id}/meetings/{safe_name}"


class MinioStorage:
    """Storage backend using MinIO (local development)."""

    provider_name = "minio"

    def __init__(self) -> None:
        self.bucket = settings.MINIO_BUCKET_NAME
        scheme = "https" if settings.MINIO_SECURE else "http"
        raw_public = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
        if raw_public.startswith("http://") or raw_public.startswith("https://"):
            public_endpoint_url = raw_public
        else:
            public_endpoint_url = f"{scheme}://{raw_public}"

        # Internal client — server-to-server operations
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )

        # Public client — presigned URLs for the browser
        self._public_client = boto3.client(
            "s3",
            endpoint_url=public_endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )

        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
            except ClientError as e:
                print(f"Warning: Could not create bucket {self.bucket}: {e}")

    def generate_presigned_upload_url(
        self, user_id: int, filename: str, content_type: str, expiration: int = 3600
    ) -> tuple[str, str]:
        object_key = _make_object_key(user_id, filename)
        response = self._public_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": object_key, "ContentType": content_type},
            ExpiresIn=expiration,
        )
        return response, object_key

    def get_presigned_download_url(self, object_key: str, expiration: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expiration,
        )

    def get_public_presigned_download_url(self, object_key: str, expiration: int = 3600) -> str:
        """Presigned URL reachable from outside Docker (for RunPod, browser, etc.)."""
        return self._public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expiration,
        )

    def upload_file(self, file_data: bytes, object_key: str, content_type: str) -> None:
        self.s3_client.put_object(
            Bucket=self.bucket, Key=object_key, Body=file_data, ContentType=content_type
        )

    def delete_file(self, object_key: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket, Key=object_key)

    def delete_prefix(self, prefix: str) -> int:
        """Delete every object whose key starts with `prefix`.

        Returns count deleted. Uses the list_objects_v2 paginator which chunks
        the listing automatically; delete_objects is bounded to 1000 keys/call
        so we ship one batch per page."""
        paginator = self.s3_client.get_paginator("list_objects_v2")
        deleted = 0
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            objs = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not objs:
                continue
            self.s3_client.delete_objects(Bucket=self.bucket, Delete={"Objects": objs})
            deleted += len(objs)
        return deleted

    def create_multipart_upload(
        self, user_id: int, filename: str, content_type: str
    ) -> tuple[str, str]:
        object_key = _make_object_key(user_id, filename)
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket,
            Key=object_key,
            ContentType=content_type,
        )
        return response["UploadId"], object_key

    def generate_part_url(
        self, object_key: str, upload_id: str, part_number: int, expiration: int = 3600
    ) -> str:
        return self._public_client.generate_presigned_url(
            "upload_part",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=expiration,
        )

    def complete_multipart_upload(
        self, object_key: str, upload_id: str, parts: list[dict]
    ) -> None:
        self.s3_client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )

    def abort_multipart_upload(self, object_key: str, upload_id: str) -> None:
        self.s3_client.abort_multipart_upload(
            Bucket=self.bucket,
            Key=object_key,
            UploadId=upload_id,
        )

    def list_pending_multipart_uploads(self, older_than_hours: int = 24) -> list[dict]:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        pending: list[dict] = []
        paginator = self.s3_client.get_paginator("list_multipart_uploads")
        for page in paginator.paginate(Bucket=self.bucket):
            for upload in page.get("Uploads", []) or []:
                if upload["Initiated"] < cutoff:
                    pending.append({
                        "Key": upload["Key"],
                        "UploadId": upload["UploadId"],
                        "Initiated": upload["Initiated"],
                    })
        return pending


class S3Storage:
    """Storage backend using S3-compatible cloud providers (R2, AWS S3, etc.)."""

    provider_name = "s3"

    def __init__(self) -> None:
        if not settings.S3_ENDPOINT_URL:
            raise RuntimeError(
                "STORAGE_PROVIDER is set to 's3' but S3_ENDPOINT_URL is empty. "
                "Set S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, and S3_SECRET_ACCESS_KEY."
            )

        self.bucket = settings.S3_BUCKET_NAME
        public_url = settings.S3_PUBLIC_URL or settings.S3_ENDPOINT_URL

        # Internal client — server-to-server operations
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )

        # Public client — presigned URLs for the browser
        self._public_client = boto3.client(
            "s3",
            endpoint_url=public_url,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )

        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                print(f"Warning: Bucket '{self.bucket}' does not exist on S3 endpoint.")
            else:
                print(f"Warning: Could not verify bucket '{self.bucket}': {e}")

    def generate_presigned_upload_url(
        self, user_id: int, filename: str, content_type: str, expiration: int = 3600
    ) -> tuple[str, str]:
        object_key = _make_object_key(user_id, filename)
        response = self._public_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": object_key, "ContentType": content_type},
            ExpiresIn=expiration,
        )
        return response, object_key

    def get_presigned_download_url(self, object_key: str, expiration: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expiration,
        )

    def get_public_presigned_download_url(self, object_key: str, expiration: int = 3600) -> str:
        """Presigned URL reachable from outside Docker (for RunPod, browser, etc.)."""
        return self._public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expiration,
        )

    def upload_file(self, file_data: bytes, object_key: str, content_type: str) -> None:
        self.s3_client.put_object(
            Bucket=self.bucket, Key=object_key, Body=file_data, ContentType=content_type
        )

    def delete_file(self, object_key: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket, Key=object_key)

    def delete_prefix(self, prefix: str) -> int:
        """Delete every object whose key starts with `prefix`.

        Returns count deleted. Uses the list_objects_v2 paginator which chunks
        the listing automatically; delete_objects is bounded to 1000 keys/call
        so we ship one batch per page."""
        paginator = self.s3_client.get_paginator("list_objects_v2")
        deleted = 0
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            objs = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not objs:
                continue
            self.s3_client.delete_objects(Bucket=self.bucket, Delete={"Objects": objs})
            deleted += len(objs)
        return deleted

    def create_multipart_upload(
        self, user_id: int, filename: str, content_type: str
    ) -> tuple[str, str]:
        object_key = _make_object_key(user_id, filename)
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket,
            Key=object_key,
            ContentType=content_type,
        )
        return response["UploadId"], object_key

    def generate_part_url(
        self, object_key: str, upload_id: str, part_number: int, expiration: int = 3600
    ) -> str:
        return self._public_client.generate_presigned_url(
            "upload_part",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=expiration,
        )

    def complete_multipart_upload(
        self, object_key: str, upload_id: str, parts: list[dict]
    ) -> None:
        self.s3_client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )

    def abort_multipart_upload(self, object_key: str, upload_id: str) -> None:
        self.s3_client.abort_multipart_upload(
            Bucket=self.bucket,
            Key=object_key,
            UploadId=upload_id,
        )

    def list_pending_multipart_uploads(self, older_than_hours: int = 24) -> list[dict]:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        pending: list[dict] = []
        paginator = self.s3_client.get_paginator("list_multipart_uploads")
        for page in paginator.paginate(Bucket=self.bucket):
            for upload in page.get("Uploads", []) or []:
                if upload["Initiated"] < cutoff:
                    pending.append({
                        "Key": upload["Key"],
                        "UploadId": upload["UploadId"],
                        "Initiated": upload["Initiated"],
                    })
        return pending


def create_storage() -> StorageProvider:
    """Factory: returns MinioStorage or S3Storage based on STORAGE_PROVIDER setting."""
    provider = settings.STORAGE_PROVIDER.lower()
    if provider == "s3":
        return S3Storage()
    return MinioStorage()


storage: StorageProvider = create_storage()
