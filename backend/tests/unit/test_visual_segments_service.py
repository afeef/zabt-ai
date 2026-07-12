"""Tests for VisualSegmentService — DB round-trip + transcript alignment."""
from datetime import datetime

import pytest
from sqlmodel import Session

from app.db.engine import engine
from app.models import Meeting, TranscriptSegment, User, VisualSegment
from app.services.visual_segments import VisualSegmentService


@pytest.fixture
def owner_user(db: Session) -> User:
    user = db.get(User, 1)
    if user is None:
        user = User(id=1, email="test@example.com", supabase_id="test-uuid", full_name="Test")
        db.add(user); db.commit(); db.refresh(user)
    return user


@pytest.fixture
def meeting(db: Session, owner_user: User) -> Meeting:
    m = Meeting(owner_id=owner_user.id, title="Test mtg")
    db.add(m); db.commit(); db.refresh(m)
    yield m
    # Cleanup — segments cascade via FK
    with Session(engine) as s:
        m_db = s.get(Meeting, m.id)
        if m_db is not None:
            s.delete(m_db); s.commit()


def _seg(meeting_id: int, sequence: int, start: float, end: float) -> VisualSegment:
    return VisualSegment(
        meeting_id=meeting_id, sequence=sequence,
        start_time=start, end_time=end,
        screenshot_s3_key=f"k{sequence}",
        caption=f"cap{sequence}", confidence=0.9,
    )


def test_list_for_meeting_returns_empty_when_none(meeting: Meeting):
    svc = VisualSegmentService()
    assert svc.list_for_meeting(meeting.id) == []


def test_replace_for_meeting_deletes_prior_and_inserts_new(meeting: Meeting):
    svc = VisualSegmentService()

    svc.replace_for_meeting(meeting.id, [_seg(meeting.id, 0, 0.0, 5.0)])
    assert len(svc.list_for_meeting(meeting.id)) == 1

    svc.replace_for_meeting(meeting.id, [
        _seg(meeting.id, 0, 0.0, 3.0),
        _seg(meeting.id, 1, 3.0, 6.0),
    ])
    out = svc.list_for_meeting(meeting.id)
    assert len(out) == 2
    assert out[0].end_time == 3.0  # old row with end_time=5.0 is gone


def test_get_with_transcript_alignment_maps_lines_to_segments(meeting: Meeting):
    svc = VisualSegmentService()

    svc.replace_for_meeting(meeting.id, [
        _seg(meeting.id, 0, 0.0, 5.0),
        _seg(meeting.id, 1, 5.0, 10.0),
    ])
    with Session(engine) as s:
        s.add(TranscriptSegment(
            meeting_id=meeting.id, speaker="A", text="hi",
            start_time=1.0, end_time=2.0,
        ))
        s.add(TranscriptSegment(
            meeting_id=meeting.id, speaker="A", text="bye",
            start_time=7.0, end_time=8.0,
        ))
        s.commit()

    out = svc.get_with_transcript_alignment(meeting.id)
    assert len(out) == 2
    assert [len(s.transcript_lines) for s in out] == [1, 1]
    assert out[0].transcript_lines[0].text == "hi"
    assert out[1].transcript_lines[0].text == "bye"


def test_transcript_line_straddling_boundary_assigned_by_start_time(meeting: Meeting):
    svc = VisualSegmentService()
    svc.replace_for_meeting(meeting.id, [
        _seg(meeting.id, 0, 0.0, 5.0),
        _seg(meeting.id, 1, 5.0, 10.0),
    ])
    with Session(engine) as s:
        s.add(TranscriptSegment(
            meeting_id=meeting.id, speaker="A", text="straddle",
            start_time=4.5, end_time=5.8,
        ))
        s.commit()
    out = svc.get_with_transcript_alignment(meeting.id)
    assert len(out[0].transcript_lines) == 1
    assert len(out[1].transcript_lines) == 0
