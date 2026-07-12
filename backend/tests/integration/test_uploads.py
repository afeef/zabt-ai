# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from fastapi.testclient import TestClient
from sqlmodel import Session
import os

def test_upload_meeting_file(client: TestClient, db: Session, normal_user_token_headers):
    # Prepare a dummy file
    filename = "test_audio.mp3"
    with open(filename, "wb") as f:
        f.write(b"dummy audio content")
        
    try:
        with open(filename, "rb") as f:
            response = client.post(
                "/api/v1/meetings/upload",
                headers=normal_user_token_headers,
                files={"file": (filename, f, "audio/mpeg")},
                data={"title": "Upload Test"}
            )
            
        assert response.status_code == 200
        content = response.json()
        assert content["title"] == "Upload Test"
        assert content["status"] == "queued"
        assert "id" in content
        
    finally:
        if os.path.exists(filename):
            os.remove(filename)
