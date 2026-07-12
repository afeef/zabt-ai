# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from fastapi.testclient import TestClient
from sqlmodel import Session

def test_create_style_profile(client: TestClient, db: Session, normal_user_token_headers):
    data = {
        "name": "Corporate Style",
        "description": "Formal meeting minutes",
        "prompt_template": "Summarize in bullet points."
    }
    response = client.post(
        "/api/v1/styles/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content

def test_read_styles(client: TestClient, db: Session, normal_user_token_headers):
    response = client.get("/api/v1/styles/", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
