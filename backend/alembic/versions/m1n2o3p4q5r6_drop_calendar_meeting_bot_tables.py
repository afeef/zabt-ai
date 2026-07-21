# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""drop calendar_event and bot_job tables (feature removed)

Revision ID: m1n2o3p4q5r6
Revises: l0m1n2o3p4q5
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "m1n2o3p4q5r6"
down_revision: Union[str, None] = "l0m1n2o3p4q5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop child first (botjob.calendar_event_id -> calendarevent.id), then parent.
    op.drop_table("botjob")
    op.drop_table("calendarevent")


def downgrade() -> None:
    # Recreate the table structures (empty -- original row data is not restored).
    #
    # calendarevent: base shape copied from
    # alembic/versions/c1d2e3f4g5h6_add_integration_and_calendar_event.py
    # (op.create_table("calendarevent", ...) in upgrade()), with two later
    # ALTERs folded in so the recreated schema matches the pre-drop state:
    #   - j8k9l0m1n2o3_drop_calendar_event_recording_columns.py dropped
    #     recording_url / recording_source -- they are NOT recreated here.
    #   - k9l0m1n2o3p4_cascade_delete_integration_events.py added
    #     ON DELETE CASCADE to calendarevent.integration_id -- reproduced
    #     below via ondelete="CASCADE".
    op.create_table(
        "calendarevent",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column(
            "integration_id",
            sa.Integer(),
            sa.ForeignKey("integration.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("external_event_id", sa.String(), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("conferencing_platform", sa.String(), nullable=True),
        sa.Column("join_url", sa.String(), nullable=True),
        sa.Column("organizer_email", sa.String(), nullable=True),
        sa.Column("attendees", JSONB(), nullable=True),
        sa.Column("auto_join", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("bot_status", sa.String(), nullable=False, server_default="IDLE"),
        sa.Column("meeting_id", sa.Integer(), sa.ForeignKey("meeting.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # botjob: base shape copied from
    # alembic/versions/e3f4g5h6i7j8_add_bot_job.py
    # (op.create_table("botjob", ...) in upgrade()), with the later ALTER
    # folded in:
    #   - k9l0m1n2o3p4_cascade_delete_integration_events.py added
    #     ON DELETE CASCADE to botjob.calendar_event_id -- reproduced below
    #     via ondelete="CASCADE".
    op.create_table(
        "botjob",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "calendar_event_id",
            sa.Integer(),
            sa.ForeignKey("calendarevent.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
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
