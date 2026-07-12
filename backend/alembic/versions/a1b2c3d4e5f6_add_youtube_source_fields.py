"""add youtube source fields

Revision ID: a1b2c3d4e5f6
Revises: 1fcb7992e425
Create Date: 2026-03-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '1fcb7992e425'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('meeting', sa.Column('source_type', sa.String(), nullable=False, server_default=sa.text("'upload'")))
    op.add_column('meeting', sa.Column('source_url', sa.String(), nullable=True))
    op.add_column('meeting', sa.Column('youtube_title', sa.String(), nullable=True))
    op.add_column('meeting', sa.Column('youtube_duration_seconds', sa.Integer(), nullable=True))
    op.add_column('meeting', sa.Column('youtube_thumbnail_url', sa.String(), nullable=True))
    op.add_column('meeting', sa.Column('youtube_channel', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('meeting', 'youtube_channel')
    op.drop_column('meeting', 'youtube_thumbnail_url')
    op.drop_column('meeting', 'youtube_duration_seconds')
    op.drop_column('meeting', 'youtube_title')
    op.drop_column('meeting', 'source_url')
    op.drop_column('meeting', 'source_type')
