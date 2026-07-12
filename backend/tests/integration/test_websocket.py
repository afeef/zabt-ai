# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from fastapi.testclient import TestClient
from app.main import app
import pytest

def test_websocket_transcription(client: TestClient):
    # Token mock
    token = "mock-token" # In real test, generate valid JWT

    # Mock meeting creation first if needed, or assume ID 1
    meeting_id = 999

    with client.websocket_connect(f"/api/v1/transcriptions/ws/{meeting_id}?token={token}") as websocket:
        # Send binary data (simulated audio)
        data = b"\x00" * 1024 # Dummy bytes
        websocket.send_bytes(data)

        # Expect response (mocked or real if whisper configured)
        # If whisper is mocked or failures handled, we expect some JSON or close
        # For basic connectivity test:
        # data = websocket.receive_json()
        # assert "text" in data
        pass
