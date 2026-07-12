"""add bot_job table

Revision ID: e3f4g5h6i7j8
Revises: d2e3f4g5h6i7
Create Date: 2026-04-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "e3f4g5h6i7j8"
down_revision: Union[str, None] = "d2e3f4g5h6i7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "botjob",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("calendar_event_id", sa.Integer(), sa.ForeignKey("calendarevent.id"), nullable=False, index=True),
        sa.Column("worker_instance_id", sa.String(), nullable=True),
        sa.Column("infrastructure", sa.String(), nullable=False, server_default="local"),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("join_url", sa.String(), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("speakers_count", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("attendees", JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("botjob")
