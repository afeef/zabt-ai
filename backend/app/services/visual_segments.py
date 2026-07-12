"""Service layer for VisualSegment persistence and on-read transcript alignment."""
from dataclasses import dataclass, field
from typing import List, Optional

from sqlmodel import Session, delete, select

from app.db.engine import engine
from app.models import TranscriptSegment, VisualSegment
from app.services.base import BaseService


@dataclass
class TranscriptLineOut:
    speaker: Optional[str]
    text: str
    start: float
    end: float


@dataclass
class VisualSegmentWithTranscript:
    id: int
    sequence: int
    start_time: float
    end_time: float
    screenshot_s3_key: str
    caption: str
    confidence: float
    transcript_lines: List[TranscriptLineOut] = field(default_factory=list)


class VisualSegmentService(BaseService):
    def list_for_meeting(self, meeting_id: int) -> List[VisualSegment]:
        with Session(engine) as session:
            stmt = (
                select(VisualSegment)
                .where(VisualSegment.meeting_id == meeting_id)
                .order_by(VisualSegment.sequence)
            )
            return list(session.exec(stmt))

    def replace_for_meeting(self, meeting_id: int, segments: List[VisualSegment]) -> None:
        """Delete prior rows for this meeting, bulk-insert new. Matches the
        overwrite pattern used by re-transcribe."""
        with Session(engine) as session:
            session.exec(delete(VisualSegment).where(VisualSegment.meeting_id == meeting_id))
            for seg in segments:
                # Detach from any other session — caller may have built these from worker output
                seg.id = None
                seg.meeting_id = meeting_id
                session.add(seg)
            session.commit()

    def get_with_transcript_alignment(
        self, meeting_id: int
    ) -> List[VisualSegmentWithTranscript]:
        """Load visual segments and attach transcript lines whose start_time
        falls within each segment's [start_time, end_time). Lines that straddle
        a boundary are assigned to the segment containing their start_time.

        Uses two-pointer alignment because both lists are sorted by time."""
        with Session(engine) as session:
            segments = list(session.exec(
                select(VisualSegment)
                .where(VisualSegment.meeting_id == meeting_id)
                .order_by(VisualSegment.sequence)
            ))
            if not segments:
                return []

            transcript = list(session.exec(
                select(TranscriptSegment)
                .where(TranscriptSegment.meeting_id == meeting_id)
                .order_by(TranscriptSegment.start_time)
            ))

        result: List[VisualSegmentWithTranscript] = []
        ti = 0
        for seg in segments:
            lines: List[TranscriptLineOut] = []
            while ti < len(transcript) and transcript[ti].start_time < seg.end_time:
                if transcript[ti].start_time >= seg.start_time:
                    t = transcript[ti]
                    lines.append(TranscriptLineOut(
                        speaker=t.speaker, text=t.text,
                        start=t.start_time, end=t.end_time,
                    ))
                ti += 1
            result.append(VisualSegmentWithTranscript(
                id=seg.id, sequence=seg.sequence,
                start_time=seg.start_time, end_time=seg.end_time,
                screenshot_s3_key=seg.screenshot_s3_key,
                caption=seg.caption, confidence=seg.confidence,
                transcript_lines=lines,
            ))
        return result
