"""LLM-backed transliteration between scripts of the same spoken language."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


_PROMPT_TEMPLATE = """You are a transliteration assistant. Convert the following \
{source_label} text into {target_label}. Preserve meaning, punctuation, line \
breaks, and proper nouns exactly. Do NOT translate — only transliterate the \
script. Output ONLY the transliterated text, no preamble.

INPUT:
{text}
"""


_LANG_LABELS = {
    "urdu_arabic": "Urdu (Arabic script)",
    "urdu_roman": "Roman Urdu (Latin script)",
    "punjabi_shahmukhi": "Punjabi (Shahmukhi/Arabic script)",
    "punjabi_gurmukhi": "Punjabi (Gurmukhi script)",
}


def _call_llm(prompt: str) -> str:
    # Use the same OpenAI wrapper the rest of the codebase uses (langfuse-instrumented if available).
    try:
        from langfuse.openai import OpenAI
    except ImportError:
        from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()


def transliterate(text: str, source_code: str, target_code: str) -> str:
    if not text or not text.strip():
        return ""
    source_label = _LANG_LABELS.get(source_code, source_code)
    target_label = _LANG_LABELS.get(target_code, target_code)
    prompt = _PROMPT_TEMPLATE.format(
        source_label=source_label, target_label=target_label, text=text,
    )
    try:
        return _call_llm(prompt)
    except Exception:
        logger.exception("Transliteration failed (%s → %s)", source_code, target_code)
        raise
