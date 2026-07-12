# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""drop calendar_event recording columns

The recording_url / recording_source columns were written only by the
OneDrive recording-pickup flow, which has been removed (see the
chore/remove-recording-pickup commit). No live code writes these
columns anymore; the headless Chromium bot captures audio directly.

Revision ID: j8k9l0m1n2o3
Revises: i7j8k9l0m1n2
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa


revision = "j8k9l0m1n2o3"
down_revision = "i7j8k9l0m1n2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("calendarevent", "recording_url")
    op.drop_column("calendarevent", "recording_source")


def downgrade() -> None:
    op.add_column(
        "calendarevent",
        sa.Column("recording_source", sa.String(), nullable=True),
    )
    op.add_column(
        "calendarevent",
        sa.Column("recording_url", sa.String(), nullable=True),
    )
