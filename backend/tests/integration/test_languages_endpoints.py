# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
def test_list_languages_returns_catalog(client):
    resp = client.get("/api/v1/languages")
    assert resp.status_code == 200
    body = resp.json()
    codes = {e["code"] for e in body}
    assert "urdu_arabic" in codes
    assert "english" in codes
    sample = next(e for e in body if e["code"] == "urdu_arabic")
    assert sample["whisper_lang"] == "ur"
    assert sample["display_name"].startswith("Urdu")


def test_get_preferences_returns_defaults(client):
    resp = client.get("/api/v1/users/me/language-preferences")
    assert resp.status_code == 200
    codes = resp.json()["codes"]
    assert "english" in codes
    assert "urdu_arabic" in codes


def test_put_preferences_persists(client):
    resp = client.put(
        "/api/v1/users/me/language-preferences",
        json={"codes": ["urdu_arabic", "english"]},
    )
    assert resp.status_code == 200
    assert resp.json()["codes"] == ["urdu_arabic", "english"]

    resp = client.get("/api/v1/users/me/language-preferences")
    assert resp.json()["codes"] == ["urdu_arabic", "english"]


def test_put_preferences_rejects_invalid_code(client):
    resp = client.put(
        "/api/v1/users/me/language-preferences",
        json={"codes": ["english", "klingon"]},
    )
    assert resp.status_code == 400
    assert "klingon" in resp.json()["detail"]


def test_put_preferences_rejects_empty_list(client):
    resp = client.put(
        "/api/v1/users/me/language-preferences", json={"codes": []},
    )
    assert resp.status_code == 400
