from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models import User, Meeting
from app.core import security

def test_create_meeting(client: TestClient, db: Session, normal_user_token_headers):
    data = {
        "title": "Test Meeting",
        "description": "Integration Test"
    }
    response = client.post(
        "/api/v1/meetings/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content

def test_read_meeting(client: TestClient, db: Session, normal_user_token_headers):
    # predefined meeting or create one
    data = {"title": "Read Test", "description": "Read Me"}
    create_res = client.post("/api/v1/meetings/", headers=normal_user_token_headers, json=data)
    meeting_id = create_res.json()["id"]

    response = client.get(f"/api/v1/meetings/{meeting_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Read Test"
