"""add visual breakdown

Revision ID: k9l0m1n2o3p4
Revises: j8k9l0m1n2o3
Create Date: 2026-04-19
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "k9l0m1n2o3p4"
down_revision = "j8k9l0m1n2o3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visualsegment",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "meeting_id",
            sa.Integer(),
            sa.ForeignKey("meeting.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("screenshot_s3_key", sa.String(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_visualsegment_meeting_id",
        "visualsegment",
        ["meeting_id"],
    )

    op.add_column(
        "meeting",
        sa.Column("visual_breakdown_status", sa.String(), nullable=True),
    )
    op.add_column(
        "meeting",
        sa.Column("visual_breakdown_error", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "meeting",
        sa.Column("visual_breakdown_completed_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "meeting",
        sa.Column("visual_raw_output_s3_key", sa.String(), nullable=True),
    )
    op.add_column(
        "meeting",
        sa.Column("visual_breakdown_model", sa.String(), nullable=True),
    )
    op.add_column(
        "meeting",
        sa.Column(
            "visual_breakdown_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "meeting",
        sa.Column(
            "visual_breakdown_run_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("meeting", "visual_breakdown_run_count")
    op.drop_column("meeting", "visual_breakdown_params")
    op.drop_column("meeting", "visual_breakdown_model")
    op.drop_column("meeting", "visual_raw_output_s3_key")
    op.drop_column("meeting", "visual_breakdown_completed_at")
    op.drop_column("meeting", "visual_breakdown_error")
    op.drop_column("meeting", "visual_breakdown_status")

    op.drop_index("ix_visualsegment_meeting_id", table_name="visualsegment")
    op.drop_table("visualsegment")
