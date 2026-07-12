"""Tests that the meeting-creation flow accepts an optional `language` field
and falls back to the user's primary preference."""

from unittest.mock import patch
import pytest
from sqlmodel import Session
from app.db.engine import engine
from app.models.base import User


COMPLETE_ENDPOINT = "/api/v1/meetings/"


def _build_complete_payload(language=None):
    payload = {
        "title": "Test Meeting",
        "file_key": "users/1/meetings/test_audio.m4a",
        "transcription_type": "general",
        "meeting_type": "generic",
    }
    if language is not None:
        payload["language"] = language
    return payload


def _set_user_prefs(codes):
    with Session(engine) as s:
        u = s.get(User, 1)
        u.language_preferences = codes
        s.add(u)
        s.commit()


def _clear_user_prefs():
    with Session(engine) as s:
        u = s.get(User, 1)
        u.language_preferences = None
        s.add(u)
        s.commit()


def test_upload_complete_with_language_persists_requested_language(client):
    payload = _build_complete_payload(language="urdu_arabic")
    resp = client.post(COMPLETE_ENDPOINT, json=payload)
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["requested_language"] == "urdu_arabic"


def test_upload_complete_without_language_uses_user_primary(client):
    _set_user_prefs(["urdu_arabic", "english"])
    try:
        payload = _build_complete_payload(language=None)
        resp = client.post(COMPLETE_ENDPOINT, json=payload)
        assert resp.status_code in (200, 201), resp.text
        body = resp.json()
        assert body["requested_language"] == "urdu_arabic"
    finally:
        _clear_user_prefs()


def test_upload_complete_with_invalid_language_returns_400(client):
    payload = _build_complete_payload(language="klingon")
    payload["language"] = "klingon"
    resp = client.post(COMPLETE_ENDPOINT, json=payload)
    assert resp.status_code == 400
