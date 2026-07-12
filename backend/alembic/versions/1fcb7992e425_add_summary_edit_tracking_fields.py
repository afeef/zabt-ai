"""add summary edit tracking fields

Revision ID: 1fcb7992e425
Revises: 2432691ecffe
Create Date: 2026-03-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fcb7992e425'
down_revision: Union[str, None] = '2432691ecffe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('meeting', sa.Column('original_summary_text', sa.Text(), nullable=True))
    op.add_column('meeting', sa.Column('summary_edited', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('meeting', 'summary_edited')
    op.drop_column('meeting', 'original_summary_text')
