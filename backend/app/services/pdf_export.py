# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import re

import mistune
import weasyprint


# Arabic script Unicode ranges (covers Arabic, Urdu, Farsi, etc.)
_ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]"
)

_UNSAFE_FILENAME_RE = re.compile(r'[/\\:*?"<>|]')


class PdfExportService:
    """Server-side PDF generation for meeting summaries and transcripts."""

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _detect_direction(text: str) -> str:
        """Return 'rtl' if text contains Arabic-script characters, else 'ltr'."""
        return "rtl" if _ARABIC_RE.search(text) else "ltr"

    @staticmethod
    def _format_duration(seconds: int | None) -> str | None:
        if seconds is None:
            return None
        mins = seconds // 60
        return f"{mins} min" if mins > 0 else f"{seconds} sec"

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        if seconds <= 0:
            return ""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return _UNSAFE_FILENAME_RE.sub("-", name).strip()

    @staticmethod
    def _escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _build_metadata_html(self, meeting) -> str:
        title = self._escape_html(meeting.title)
        direction = self._detect_direction(meeting.title)

        date_str = meeting.created_at.strftime("%a, %b %d, %Y %I:%M %p")
        duration = self._format_duration(meeting.duration_seconds)

        # Resolve speaker names from segments
        speaker_names: list[str] = []
        if meeting.segments:
            seen: set[str] = set()
            for seg in meeting.segments:
                name = seg.speaker or "Unknown Speaker"
                if name not in seen:
                    seen.add(name)
                    speaker_names.append(name)

        lines = [
            f'<h1 dir="{direction}" class="title">{title}</h1>',
            f'<p class="meta"><strong>Date:</strong> {date_str}</p>',
        ]
        if duration:
            lines.append(f'<p class="meta"><strong>Duration:</strong> {duration}</p>')
        if speaker_names:
            names = self._escape_html(", ".join(speaker_names))
            lines.append(f'<p class="meta"><strong>Speakers:</strong> {names}</p>')
        lines.append('<hr class="separator">')

        return "\n".join(lines)

    @staticmethod
    def _get_css() -> str:
        return """
        @page {
            size: A4;
            margin: 48px;
        }
        body {
            font-family: "Noto Sans", "Noto Naskh Arabic", "Noto Sans Devanagari", sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #1c1917;
        }
        .title {
            font-size: 20pt;
            font-weight: bold;
            color: #0c0a09;
            margin-bottom: 4px;
        }
        .meta {
            font-size: 9pt;
            color: #78716c;
            margin: 2px 0;
        }
        .separator {
            border: none;
            border-top: 0.5px solid #e7e5e4;
            margin: 8px 0 14px 0;
        }
        h1 { font-size: 16pt; font-weight: bold; color: #1c1917; margin-top: 12px; }
        h2 { font-size: 13pt; font-weight: bold; color: #1c1917; margin-top: 10px; }
        h3 { font-size: 11pt; font-weight: bold; color: #292524; margin-top: 8px; }
        p { margin-bottom: 6px; text-align: justify; }
        ul, ol { margin-bottom: 4px; }
        .speaker-name {
            font-size: 10pt;
            font-weight: bold;
            color: #4f46e5;
        }
        .timestamp {
            font-size: 9pt;
            color: #78716c;
            margin-left: 8px;
        }
        .segment {
            margin-top: 8px;
            margin-bottom: 4px;
        }
        .segment-text {
            margin-bottom: 4px;
            line-height: 1.4;
        }
        [dir="rtl"] {
            direction: rtl;
            text-align: right;
        }
        """

    def _build_html_document(self, body: str) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{self._get_css()}</style>
</head>
<body>
{body}
</body>
</html>"""

    # ── Public methods ────────────────────────────────────────────────────

    def generate_summary_pdf(self, meeting) -> bytes:
        """Generate a PDF of the meeting summary from markdown."""
        metadata = self._build_metadata_html(meeting)

        summary_html = ""
        if meeting.summary_text:
            direction = self._detect_direction(meeting.summary_text)
            rendered = mistune.html(meeting.summary_text)
            summary_html = f'<div dir="{direction}">{rendered}</div>'

        action_items_html = ""
        if meeting.action_items_text and meeting.action_items_text.strip():
            direction = self._detect_direction(meeting.action_items_text)
            rendered = mistune.html(meeting.action_items_text)
            action_items_html = (
                f'<div dir="{direction}" style="margin-top: 16px;">'
                f"<h2>Action Items</h2>{rendered}</div>"
            )

        body = f"{metadata}\n{summary_html}\n{action_items_html}"
        html_doc = self._build_html_document(body)
        return weasyprint.HTML(string=html_doc).write_pdf()

    def generate_transcript_pdf(self, meeting, segments, speakers: dict) -> bytes:
        """Generate a PDF of the meeting transcript with speaker labels and timestamps."""
        metadata = self._build_metadata_html(meeting)

        parts: list[str] = []
        for i, seg in enumerate(segments):
            speaker_id = seg.speaker or ""
            speaker_info = speakers.get(speaker_id)
            if speaker_info and isinstance(speaker_info, dict):
                speaker_name = speaker_info.get("name", speaker_id or "Unknown Speaker")
            else:
                speaker_name = speaker_id or "Unknown Speaker"

            ts = self._format_timestamp(seg.start_time)
            escaped_name = self._escape_html(speaker_name)
            escaped_text = self._escape_html(seg.text)

            text_dir = self._detect_direction(seg.text)
            name_dir = self._detect_direction(speaker_name)

            ts_html = f'<span class="timestamp">{ts}</span>' if ts else ""

            parts.append(
                f'<div class="segment">'
                f'<div dir="{name_dir}"><span class="speaker-name">{escaped_name}</span>{ts_html}</div>'
                f'<p class="segment-text" dir="{text_dir}">{escaped_text}</p>'
                f"</div>"
            )

        body = f"{metadata}\n{''.join(parts)}"
        html_doc = self._build_html_document(body)
        return weasyprint.HTML(string=html_doc).write_pdf()


pdf_export_service = PdfExportService()
