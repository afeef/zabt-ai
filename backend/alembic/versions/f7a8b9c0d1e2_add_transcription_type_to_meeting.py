"""add transcription_type to meeting

Revision ID: f7a8b9c0d1e2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create native Postgres ENUM type matching Python TranscriptionType
    transcription_type_enum = sa.Enum("GENERAL", "MEDICAL", name="transcriptiontype")
    transcription_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "meeting",
        sa.Column(
            "transcription_type",
            transcription_type_enum,
            server_default="GENERAL",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("meeting", "transcription_type")
    sa.Enum(name="transcriptiontype").drop(op.get_bind(), checkfirst=True)
