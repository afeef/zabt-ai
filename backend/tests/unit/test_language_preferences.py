import pytest
from sqlmodel import Session

from app.db.engine import engine
from app.models.base import User, UserTier
from app.services.languages.preferences import (
    get_preferences, get_primary_code, get_allowed_whisper_langs,
    set_preferences, InvalidLanguageCode,
)


@pytest.fixture
def user():
    with Session(engine) as s:
        u = User(
            email="lang-test@example.com",
            supabase_id="lang-test-supa",
            tier=UserTier.FREE,
        )
        s.add(u)
        s.commit()
        s.refresh(u)
        uid = u.id
        yield u
        # cleanup
        u2 = s.get(User, uid)
        if u2:
            s.delete(u2)
            s.commit()


def test_get_preferences_returns_defaults_when_unset(user):
    with Session(engine) as s:
        prefs = get_preferences(s, user.id)
    assert "english" in prefs
    assert "urdu_arabic" in prefs


def test_set_preferences_persists_order(user):
    with Session(engine) as s:
        set_preferences(s, user.id, ["urdu_arabic", "english"])
    with Session(engine) as s:
        prefs = get_preferences(s, user.id)
    assert prefs == ["urdu_arabic", "english"]


def test_set_preferences_rejects_invalid_code(user):
    with Session(engine) as s:
        with pytest.raises(InvalidLanguageCode):
            set_preferences(s, user.id, ["english", "klingon"])


def test_get_primary_code(user):
    with Session(engine) as s:
        set_preferences(s, user.id, ["urdu_arabic", "english"])
    with Session(engine) as s:
        assert get_primary_code(s, user.id) == "urdu_arabic"


def test_get_allowed_whisper_langs_dedupes(user):
    # urdu_arabic and urdu_roman both map to whisper_lang=ur
    with Session(engine) as s:
        set_preferences(s, user.id, ["urdu_arabic", "urdu_roman", "english"])
    with Session(engine) as s:
        langs = get_allowed_whisper_langs(s, user.id)
    assert sorted(langs) == ["en", "ur"]
