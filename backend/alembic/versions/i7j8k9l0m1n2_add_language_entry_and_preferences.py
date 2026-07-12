"""add language entry and preferences

Revision ID: i7j8k9l0m1n2
Revises: h5i6j7k8l9m0
Create Date: 2026-04-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "i7j8k9l0m1n2"
down_revision = "h5i6j7k8l9m0"
branch_labels = None
depends_on = None


SEED_LANGUAGES = [
    # (code, display_name, whisper_lang, script, transliterate_from, is_default)
    ("english", "English", "en", "latin", None, True),
    ("urdu_arabic", "Urdu (اردو)", "ur", "arabic", None, True),
    ("urdu_roman", "Urdu (Roman)", "ur", "latin", "urdu_arabic", False),
    ("hindi", "Hindi", "hi", "devanagari", None, False),
    ("punjabi_shahmukhi", "Punjabi (شاہمکھی)", "pa", "arabic", None, False),
    ("punjabi_gurmukhi", "Punjabi (ਗੁਰਮੁਖੀ)", "pa", "gurmukhi", None, False),
    ("arabic", "Arabic (العربية)", "ar", "arabic", None, False),
    ("spanish", "Spanish (Español)", "es", "latin", None, False),
    ("french", "French (Français)", "fr", "latin", None, False),
    ("german", "German (Deutsch)", "de", "latin", None, False),
    ("mandarin", "Mandarin (中文)", "zh", "chinese", None, False),
]


def upgrade() -> None:
    op.create_table(
        "language_entry",
        sa.Column("code", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("whisper_lang", sa.Text(), nullable=False),
        sa.Column("script", sa.Text(), nullable=False),
        sa.Column("transliterate_from", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.add_column(
        "user",
        sa.Column(
            "language_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column("meeting", sa.Column("requested_language", sa.Text(), nullable=True))
    op.add_column("meeting", sa.Column("transliterated_text", sa.Text(), nullable=True))

    table = sa.table(
        "language_entry",
        sa.column("code", sa.Text),
        sa.column("display_name", sa.Text),
        sa.column("whisper_lang", sa.Text),
        sa.column("script", sa.Text),
        sa.column("transliterate_from", sa.Text),
        sa.column("is_default", sa.Boolean),
    )
    op.bulk_insert(
        table,
        [
            dict(
                code=c, display_name=d, whisper_lang=w, script=s,
                transliterate_from=tf, is_default=isd,
            )
            for c, d, w, s, tf, isd in SEED_LANGUAGES
        ],
    )


def downgrade() -> None:
    op.drop_column("meeting", "transliterated_text")
    op.drop_column("meeting", "requested_language")
    op.drop_column("user", "language_preferences")
    op.drop_table("language_entry")
