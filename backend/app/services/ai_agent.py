# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from typing import List, Optional
from pydantic import BaseModel, Field
from langfuse.openai import OpenAI
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Output schema (unused for now — will be used via dedicated UI button) ───

class ActionItem(BaseModel):
    description: str = Field(description="Clear, actionable task starting with a verb (e.g. 'Schedule follow-up with…').")
    owner: Optional[str] = Field(default=None, description="Person responsible. Use the speaker name from the transcript, or null if unassigned.")
    due_date: Optional[str] = Field(default=None, description="Deadline if explicitly mentioned (e.g. 'by Friday', 'next week'). Null if not stated.")
    priority: Optional[str] = Field(default=None, description="'high', 'medium', or 'low' — inferred from urgency language. Null if unclear.")


class Topic(BaseModel):
    title: str = Field(description="Short topic heading (3-8 words).")
    summary: str = Field(description="1-3 sentence summary of what was discussed under this topic.")
    speakers: List[str] = Field(default_factory=list, description="Speakers who contributed to this topic.")


class MeetingMinutes(BaseModel):
    title: str = Field(description="A short, descriptive title for the meeting (5-10 words). Infer from the main subject discussed.")
    summary: str = Field(description="A concise executive summary of the entire meeting in 2-4 sentences. Lead with the most important outcome.")
    topics: List[Topic] = Field(default_factory=list, description="Key topics discussed, in chronological order.")
    key_decisions: List[str] = Field(default_factory=list, description="Concrete decisions that were agreed upon. Each should be a complete, standalone statement.")
    action_items: List[ActionItem] = Field(default_factory=list, description="Tasks that need to be done after this meeting.")
    open_questions: List[str] = Field(default_factory=list, description="Unresolved questions or topics that need follow-up.")
    sentiment: str = Field(description="Overall tone of the meeting: 'Positive', 'Neutral', 'Negative', or 'Mixed'.")
    participant_count: Optional[int] = Field(default=None, description="Number of distinct speakers detected in the transcript.")


# ── LLM client setup ────────────────────────────────────────────────────────

_client = OpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)

SYSTEM_PROMPT = """\
You are Zabt, an expert meeting note-taker. You transform raw meeting transcripts into clear, well-structured meeting notes in markdown format.

## Your task

Given a meeting transcript (with speaker labels and timestamps), produce comprehensive meeting notes.

## Output format

Write your notes in this markdown structure:

# [Meeting Title — infer from main subject, 5-10 words]

## Summary
2-4 sentences capturing the meeting's purpose, key outcomes, and next steps. Lead with the most important conclusion or decision, not with "The meeting was about…". Write in past tense, third person.

## Topics Discussed
For each topic (2-6 topics, chronological order):
### [Topic Title]
1-3 sentence factual summary. Mention which speakers contributed.

## Key Decisions
- Only decisions explicitly agreed upon by participants.
- Each as a complete, standalone statement.

## Action Items
- [Action verb] [task description] — Owner: [name or unassigned] | Priority: [high/medium/low] | Due: [date or none]
- Assign owner ONLY if explicitly assigned in transcript.
- Include due dates ONLY if explicitly mentioned.

## Open Questions
- Questions raised but NOT answered during the meeting.
- Topics needing more information or revisiting.

## Guidelines
- Be factual. Do not add information that isn't in the transcript.
- Use speaker names exactly as they appear (e.g. "SPEAKER_00", "Alice").
- If the transcript is too short or unintelligible, write an honest assessment.
- Prefer concise language. Avoid filler phrases.
"""


def _build_system_prompt(style_examples: list[str] | None = None) -> str:
    """Combine the base system prompt with optional style examples."""
    if not style_examples:
        return SYSTEM_PROMPT

    prompt = SYSTEM_PROMPT
    prompt += (
        "\n\n## Style reference (from user-provided PDF examples)\n\n"
        "The user has shared the following meeting notes as examples of their preferred style. "
        "Match their structure, detail level, tone, and emphasis.\n"
    )
    for i, example in enumerate(style_examples, 1):
        text = example[:3000] + "..." if len(example) > 3000 else example
        prompt += f"\n--- EXAMPLE {i} ---\n{text}\n-------------------\n"

    prompt += "\nApply this style to the transcript that follows.\n"
    return prompt


def infer_title(summary_text: str) -> str | None:
    """Ask the LLM for a short, specific meeting title based on the summary."""
    try:
        response = _client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": (
                    "Given a meeting summary, respond with ONLY a short meeting title (5-10 words). "
                    "Be specific about the subject discussed. "
                    "Never use generic titles like 'Meeting Summary', 'Meeting Notes', or 'Team Meeting'. "
                    "Examples: 'Sprint 42 Planning — API Integration', 'Invoice Financing Feature Review', "
                    "'Q2 Marketing Budget Approval'."
                )},
                {"role": "user", "content": summary_text[:2000]},
            ],
            temperature=0.1,
            max_tokens=50,
        )
        title = (response.choices[0].message.content or "").strip().strip('"\'# ')
        if title and 3 < len(title) < 120:
            return title
    except Exception:
        logger.exception("infer_title failed")
    return None


def summarize_transcript(
    transcript_text: str,
    style_examples: list[str] | None = None,
    template_body: str | None = None,
    template_id: str | None = None,
    upload_date: str | None = None,
) -> str:
    """Generate a plain-text markdown summary of the meeting transcript."""
    system_prompt = _build_system_prompt(style_examples)
    if upload_date:
        system_prompt += (
            f"\n\n## Date context\n"
            f"If the meeting date is not mentioned in the transcript, "
            f"use {upload_date} as the meeting date."
        )
    if template_body:
        system_prompt += (
            "\n\n---\nFORMAT INSTRUCTION:\n"
            "The user has selected a custom output template. Structure your response to match "
            "the following template format:\n\n"
            + template_body
        )
    response = _client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript_text},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or "Summary could not be generated."
