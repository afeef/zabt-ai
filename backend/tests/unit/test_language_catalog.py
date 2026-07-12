import pytest
from sqlmodel import Session

from app.db.engine import engine
from app.services.languages.catalog import (
    list_entries, get_entry, code_exists, default_codes,
    transliteration_target_for,
)


def test_list_entries_returns_seeded_catalog():
    with Session(engine) as s:
        entries = list_entries(s)
    codes = {e.code for e in entries}
    assert "urdu_arabic" in codes
    assert "urdu_roman" in codes
    assert "english" in codes


def test_get_entry_returns_entry_or_none():
    with Session(engine) as s:
        e = get_entry(s, "urdu_arabic")
        assert e is not None
        assert e.whisper_lang == "ur"
        assert get_entry(s, "nonexistent") is None


def test_code_exists():
    with Session(engine) as s:
        assert code_exists(s, "english") is True
        assert code_exists(s, "klingon") is False


def test_default_codes_includes_english_and_urdu():
    with Session(engine) as s:
        defaults = default_codes(s)
    assert "english" in defaults
    assert "urdu_arabic" in defaults


def test_transliteration_target_for_urdu_arabic_returns_urdu_roman():
    with Session(engine) as s:
        target = transliteration_target_for(s, "urdu_arabic")
    assert target is not None
    assert target.code == "urdu_roman"


def test_transliteration_target_for_english_returns_none():
    with Session(engine) as s:
        target = transliteration_target_for(s, "english")
    assert target is None
