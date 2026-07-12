# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
def test_language_entry_model_fields():
    from app.models.base import LanguageEntry
    fields = LanguageEntry.model_fields
    assert "code" in fields
    assert "display_name" in fields
    assert "whisper_lang" in fields
    assert "script" in fields
    assert "transliterate_from" in fields
    assert "is_default" in fields


def test_user_has_language_preferences_field():
    from app.models.base import User
    assert "language_preferences" in User.model_fields


def test_meeting_has_requested_language_and_transliterated_text():
    from app.models.base import Meeting
    assert "requested_language" in Meeting.model_fields
    assert "transliterated_text" in Meeting.model_fields
