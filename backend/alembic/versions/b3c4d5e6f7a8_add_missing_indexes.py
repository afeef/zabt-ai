# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""add missing indexes for meeting.owner_id and transcriptsegment.meeting_id

Revision ID: b3c4d5e6f7a8
Revises: f7a8b9c0d1e2
Create Date: 2026-04-01

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_meeting_owner_id", "meeting", ["owner_id"])
    op.create_index("ix_transcriptsegment_meeting_id", "transcriptsegment", ["meeting_id"])


def downgrade() -> None:
    op.drop_index("ix_transcriptsegment_meeting_id", table_name="transcriptsegment")
    op.drop_index("ix_meeting_owner_id", table_name="meeting")
