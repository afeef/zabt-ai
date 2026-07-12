# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from typing import Optional, List
from pydantic import BaseModel, Field
from langfuse.openai import OpenAI
from sqlmodel import Session, select, col

from app.core.config import settings
from app.core.logging import get_logger
from app.db.engine import engine
from app.models.meeting_intelligence import MeetingHighlight

logger = get_logger(__name__)

_client = OpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)


# ── Pydantic models for structured output (enforced by OpenAI beta.parse) ────

class HighlightChapter(BaseModel):
    title: str = Field(description="Chapter title (3-8 words)")
    description: str = Field(default="", description="1-2 sentence description")
    timestamp_start: float = Field(description="Start time in seconds")
    timestamp_end: Optional[float] = Field(default=None, description="End time in seconds")
    tags: List[str] = Field(default_factory=list, description="Topic tags")

class HighlightActionItem(BaseModel):
    content: str = Field(description="Clear, actionable task starting with a verb")
    speaker: Optional[str] = Field(default=None, description="Speaker name")
    assignee: Optional[str] = Field(default=None, description="Person responsible")
    timestamp: float = Field(default=0.0, description="Timestamp in seconds")

class HighlightKeyQuestion(BaseModel):
    content: str = Field(description="The question that was asked")
    speaker: Optional[str] = Field(default=None, description="Who asked it")
    proposed_answer: Optional[str] = Field(default=None, description="AI-proposed answer")
    timestamp: float = Field(default=0.0, description="Timestamp in seconds")

class HighlightsExtraction(BaseModel):
    chapters: List[HighlightChapter] = Field(default_factory=list)
    action_items: List[HighlightActionItem] = Field(default_factory=list)
    key_questions: List[HighlightKeyQuestion] = Field(default_factory=list)


# ── Per-meeting-type Pydantic models ─────────────────────────────────────────

class GenericItem(BaseModel):
    title: str
    summary: str
    speakers: List[str] = Field(default_factory=list)

class GenericOutput(BaseModel):
    meeting_type: str = "generic"
    summary: str
    topics: List[GenericItem] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)

class GroomingStory(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    estimate: Optional[str] = None
    status: Optional[str] = None

class GroomingOutput(BaseModel):
    meeting_type: str = "grooming"
    sprint_name: Optional[str] = None
    items: List[GroomingStory] = Field(default_factory=list)

class StandupUpdate(BaseModel):
    speaker: str
    yesterday: Optional[str] = None
    today: Optional[str] = None
    blockers: Optional[str] = None

class StandupOutput(BaseModel):
    meeting_type: str = "standup"
    items: List[StandupUpdate] = Field(default_factory=list)

class RetroActionItem(BaseModel):
    text: str
    owner: Optional[str] = None
    due: Optional[str] = None

class RetroOutput(BaseModel):
    meeting_type: str = "retro"
    went_well: List[str] = Field(default_factory=list)
    to_improve: List[str] = Field(default_factory=list)
    action_items: List[RetroActionItem] = Field(default_factory=list)

class OneOnOneFollowUp(BaseModel):
    text: str
    owner: Optional[str] = None

class OneOnOneOutput(BaseModel):
    meeting_type: str = "one_on_one"
    talking_points: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    follow_ups: List[OneOnOneFollowUp] = Field(default_factory=list)
    career_notes: List[str] = Field(default_factory=list)

# ── Highlight extraction prompt ─────────────────────────────────────────────

HIGHLIGHT_EXTRACTION_PROMPT = """\
You are a meeting analyst. Given a meeting transcript with speaker labels and timestamps, extract structured highlights.

Return a JSON object with these arrays:

{
  "chapters": [
    {
      "title": "Chapter title (3-8 words)",
      "description": "1-2 sentence description of what was discussed",
      "timestamp_start": 0.0,
      "timestamp_end": 120.5,
      "tags": ["topic1", "topic2"]
    }
  ],
  "action_items": [
    {
      "content": "Clear, actionable task starting with a verb",
      "speaker": "Speaker name or null",
      "assignee": "Person responsible or null",
      "timestamp": 45.2
    }
  ],
  "key_questions": [
    {
      "content": "The question that was asked",
      "speaker": "Who asked it",
      "proposed_answer": "AI-proposed answer based on transcript context, or null if unanswered",
      "timestamp": 78.3
    }
  ]
}

Rules:
- Timestamps are in seconds from start of meeting.
- Use speaker names exactly as they appear in the transcript.
- Chapters should cover the full meeting duration with no gaps.
- Action items must be explicitly stated or clearly implied commitments.
- Key questions are questions raised during the meeting. Include AI-proposed answers when the transcript contains enough context.
- Return valid JSON only. No markdown, no commentary.
"""

# ── Meeting type prompt templates (presets) ──────────────────────────────────

MEETING_TYPE_PROMPTS: dict = {
    "generic": {
        "prompt": "Generate a structured summary of this meeting. Include the main topics discussed, decisions made, and any follow-up items.",
        "model": GenericOutput,
        "layout_hint": "list",
    },
    "grooming": {
        "prompt": (
            "This is a sprint grooming/refinement meeting. Extract user stories discussed. "
            "Each story should follow the format 'As a [role], I want [feature] so that [benefit]'. "
            "Include acceptance criteria as bullet points and story point estimates if discussed."
        ),
        "model": GroomingOutput,
        "layout_hint": "cards",
    },
    "standup": {
        "prompt": (
            "This is a standup/daily scrum meeting. Extract each participant's update. "
            "For each speaker, capture what they did yesterday, what they're doing today, and any blockers."
        ),
        "model": StandupOutput,
        "layout_hint": "table",
    },
    "retro": {
        "prompt": (
            "This is a sprint retrospective meeting. Extract items into three categories: "
            "what went well, what needs improvement, and action items with owners."
        ),
        "model": RetroOutput,
        "layout_hint": "columns",
    },
    "one_on_one": {
        "prompt": (
            "This is a 1:1 meeting. Extract talking points discussed, decisions made, "
            "follow-up items with owners, and any career/growth notes mentioned."
        ),
        "model": OneOnOneOutput,
        "layout_hint": "list",
    },
}


class MeetingIntelligenceService:
    """Extracts structured intelligence from meeting transcripts."""

    def extract_highlights(self, transcript_text: str) -> dict:
        """Call 1: Extract action items, key questions, and chapters from transcript."""
        response = _client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": HIGHLIGHT_EXTRACTION_PROMPT},
                {"role": "user", "content": transcript_text},
            ],
            temperature=0.2,
            response_format=HighlightsExtraction,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            logger.warning("extract_highlights: parse returned None, falling back to empty")
            return {"chapters": [], "action_items": [], "key_questions": []}
        return parsed.model_dump()

    def extract_structured_output(self, transcript_text: str, meeting_type: str) -> dict:
        """Call 2: Extract meeting-type-specific structured output."""
        type_config = MEETING_TYPE_PROMPTS.get(meeting_type, MEETING_TYPE_PROMPTS["generic"])
        pydantic_model = type_config["model"]

        response = _client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": type_config["prompt"]},
                {"role": "user", "content": transcript_text},
            ],
            temperature=0.2,
            response_format=pydantic_model,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            logger.warning("extract_structured_output: parse returned None for type=%s", meeting_type)
            return {"meeting_type": meeting_type}
        return parsed.model_dump()

    def save_highlights(self, meeting_id: int, highlights_data: dict) -> list[MeetingHighlight]:
        """Persist extracted highlights to DB, replacing any existing ones."""
        with Session(engine) as session:
            # Delete existing highlights for this meeting
            existing = session.exec(
                select(MeetingHighlight).where(MeetingHighlight.meeting_id == meeting_id)
            ).all()
            for h in existing:
                session.delete(h)

            saved = []
            sort_order = 0

            # Chapters
            for ch in highlights_data.get("chapters", []):
                highlight = MeetingHighlight(
                    meeting_id=meeting_id,
                    highlight_type="chapter",
                    content=ch["title"],
                    timestamp_start=ch.get("timestamp_start", 0.0),
                    timestamp_end=ch.get("timestamp_end"),
                    extra_metadata={
                        "description": ch.get("description", ""),
                        "tags": ch.get("tags", []),
                    },
                    sort_order=sort_order,
                )
                session.add(highlight)
                saved.append(highlight)
                sort_order += 1

            # Action items
            for ai in highlights_data.get("action_items", []):
                highlight = MeetingHighlight(
                    meeting_id=meeting_id,
                    highlight_type="action_item",
                    content=ai["content"],
                    speaker=ai.get("speaker"),
                    timestamp_start=ai.get("timestamp", 0.0),
                    extra_metadata={"assignee": ai.get("assignee")},
                    sort_order=sort_order,
                )
                session.add(highlight)
                saved.append(highlight)
                sort_order += 1

            # Key questions
            for kq in highlights_data.get("key_questions", []):
                highlight = MeetingHighlight(
                    meeting_id=meeting_id,
                    highlight_type="key_question",
                    content=kq["content"],
                    speaker=kq.get("speaker"),
                    timestamp_start=kq.get("timestamp", 0.0),
                    ai_answer=kq.get("proposed_answer"),
                    sort_order=sort_order,
                )
                session.add(highlight)
                saved.append(highlight)
                sort_order += 1

            session.commit()
            return saved

    def get_highlights(
        self, meeting_id: int, highlight_type: Optional[str] = None
    ) -> list[MeetingHighlight]:
        """Retrieve highlights for a meeting, optionally filtered by type."""
        with Session(engine) as session:
            stmt = select(MeetingHighlight).where(MeetingHighlight.meeting_id == meeting_id)
            if highlight_type:
                stmt = stmt.where(MeetingHighlight.highlight_type == highlight_type)
            stmt = stmt.order_by(col(MeetingHighlight.sort_order))
            return list(session.exec(stmt).all())

    def get_layout_hint(self, meeting_type: str) -> str:
        """Get the layout hint for a meeting type."""
        type_config = MEETING_TYPE_PROMPTS.get(meeting_type, MEETING_TYPE_PROMPTS["generic"])
        return type_config["layout_hint"]


intelligence_service = MeetingIntelligenceService()
