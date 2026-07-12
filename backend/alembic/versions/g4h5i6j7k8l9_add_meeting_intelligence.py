"""add meeting intelligence columns and highlight table

Revision ID: g4h5i6j7k8l9
Revises: e3f4g5h6i7j8
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "g4h5i6j7k8l9"
down_revision: Union[str, None] = "e3f4g5h6i7j8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meeting", sa.Column("meeting_type", sa.String(), server_default="generic", nullable=False))
    op.add_column("meeting", sa.Column("structured_output", JSONB(), nullable=True))
    op.add_column("meeting", sa.Column("structured_output_status", sa.String(), server_default="pending", nullable=False))
    op.add_column("summarytemplate", sa.Column("meeting_type", sa.String(), nullable=True))
    op.add_column("summarytemplate", sa.Column("output_schema", JSONB(), nullable=True))
    op.add_column("summarytemplate", sa.Column("layout_hint", sa.String(), nullable=True))
    op.create_table(
        "meetinghighlight",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meeting_id", sa.Integer(), sa.ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("highlight_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("speaker", sa.String(), nullable=True),
        sa.Column("timestamp_start", sa.Float(), nullable=False),
        sa.Column("timestamp_end", sa.Float(), nullable=True),
        sa.Column("ai_answer", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_meetinghighlight_type", "meetinghighlight", ["meeting_id", "highlight_type"])


def downgrade() -> None:
    op.drop_table("meetinghighlight")
    op.drop_column("summarytemplate", "layout_hint")
    op.drop_column("summarytemplate", "output_schema")
    op.drop_column("summarytemplate", "meeting_type")
    op.drop_column("meeting", "structured_output_status")
    op.drop_column("meeting", "structured_output")
    op.drop_column("meeting", "meeting_type")
