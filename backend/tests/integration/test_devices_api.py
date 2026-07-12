"""/devices endpoint integration tests."""

import uuid

from fastapi.testclient import TestClient


def _payload() -> dict:
    suffix = uuid.uuid4().hex[:8]
    return {
        "expo_push_token": f"ExpoPushToken[{suffix}]",
        "platform": "ios",
    }


def test_register_device_succeeds(client: TestClient, normal_user_token_headers: dict):
    payload = _payload()
    resp = client.post("/api/v1/devices", headers=normal_user_token_headers, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["expo_push_token"] == payload["expo_push_token"]
    assert body["platform"] == "ios"
    assert body["user_id"] is not None


def test_register_device_is_idempotent(client: TestClient, normal_user_token_headers: dict):
    payload = _payload()
    first = client.post(
        "/api/v1/devices", headers=normal_user_token_headers, json=payload
    ).json()
    second = client.post(
        "/api/v1/devices", headers=normal_user_token_headers, json=payload
    ).json()
    assert first["id"] == second["id"]


def test_invalid_platform_rejected(client: TestClient, normal_user_token_headers: dict):
    suffix = uuid.uuid4().hex[:8]
    resp = client.post(
        "/api/v1/devices",
        headers=normal_user_token_headers,
        json={"expo_push_token": f"tok-{suffix}", "platform": "windows_phone"},
    )
    assert resp.status_code == 400


def test_delete_device(client: TestClient, normal_user_token_headers: dict):
    payload = _payload()
    created = client.post(
        "/api/v1/devices", headers=normal_user_token_headers, json=payload
    ).json()
    device_id = created["id"]
    resp = client.delete(
        f"/api/v1/devices/{device_id}", headers=normal_user_token_headers
    )
    assert resp.status_code == 204


def test_delete_nonexistent_device_404(
    client: TestClient, normal_user_token_headers: dict
):
    resp = client.delete("/api/v1/devices/999999", headers=normal_user_token_headers)
    assert resp.status_code == 404
