"""Uploads endpoints — chunked multipart flow."""

from unittest.mock import patch

from fastapi.testclient import TestClient


@patch("app.api.v1.endpoints.uploads.storage")
def test_initiate_returns_upload_id_and_part_urls(mock_storage, client: TestClient, normal_user_token_headers: dict):
    mock_storage.create_multipart_upload.return_value = ("upload-abc", "users/1/meetings/uuid_audio.m4a")
    mock_storage.generate_part_url.side_effect = lambda key, upload_id, part_number, expiration=3600: f"https://s3/part{part_number}"

    resp = client.post(
        "/api/v1/uploads/initiate",
        headers=normal_user_token_headers,
        json={"filename": "audio.m4a", "content_type": "audio/mp4", "total_parts": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["upload_id"] == "upload-abc"
    assert body["s3_key"] == "users/1/meetings/uuid_audio.m4a"
    assert len(body["part_urls"]) == 3
    assert body["part_urls"][0]["part_number"] == 1


@patch("app.api.v1.endpoints.uploads.storage")
def test_get_part_url_returns_single_url(mock_storage, client: TestClient, normal_user_token_headers: dict):
    mock_storage.generate_part_url.return_value = "https://s3/part5"
    resp = client.post(
        "/api/v1/uploads/part-url",
        headers=normal_user_token_headers,
        json={"s3_key": "users/1/meetings/abc.m4a", "upload_id": "u1", "part_number": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://s3/part5"


@patch("app.api.v1.endpoints.uploads.storage")
def test_complete_returns_s3_key(mock_storage, client: TestClient, normal_user_token_headers: dict):
    resp = client.post(
        "/api/v1/uploads/complete",
        headers=normal_user_token_headers,
        json={
            "s3_key": "users/1/meetings/abc.m4a",
            "upload_id": "u1",
            "parts": [
                {"part_number": 1, "etag": "e1"},
                {"part_number": 2, "etag": "e2"},
            ],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["s3_key"] == "users/1/meetings/abc.m4a"
    mock_storage.complete_multipart_upload.assert_called_once_with(
        object_key="users/1/meetings/abc.m4a",
        upload_id="u1",
        parts=[{"PartNumber": 1, "ETag": "e1"}, {"PartNumber": 2, "ETag": "e2"}],
    )


def test_total_parts_must_be_positive(client: TestClient, normal_user_token_headers: dict):
    resp = client.post(
        "/api/v1/uploads/initiate",
        headers=normal_user_token_headers,
        json={"filename": "a.m4a", "content_type": "audio/mp4", "total_parts": 0},
    )
    # Pydantic validation returns 422
    assert resp.status_code in (400, 422)


@patch("app.api.v1.endpoints.uploads.storage")
def test_complete_with_no_parts_400(mock_storage, client: TestClient, normal_user_token_headers: dict):
    resp = client.post(
        "/api/v1/uploads/complete",
        headers=normal_user_token_headers,
        json={"s3_key": "k", "upload_id": "u", "parts": []},
    )
    assert resp.status_code == 400
