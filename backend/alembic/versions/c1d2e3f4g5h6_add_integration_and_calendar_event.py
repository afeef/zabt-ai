"""add integration and calendar_event tables

Revision ID: c1d2e3f4g5h6
Revises: b3c4d5e6f7a8
Create Date: 2026-04-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


revision: str = "c1d2e3f4g5h6"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integration",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("scopes", ARRAY(sa.String()), nullable=True),
        sa.Column("provider_user_id", sa.String(), nullable=True),
        sa.Column("provider_email", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("connected_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_integration_user_provider"),
    )

    op.create_table(
        "calendarevent",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("integration_id", sa.Integer(), sa.ForeignKey("integration.id"), nullable=False, index=True),
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
        sa.Column("recording_url", sa.String(), nullable=True),
        sa.Column("recording_source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("calendarevent")
    op.drop_table("integration")
