"""add russian language

Revision ID: 092dafc12d61
Revises: l0m1n2o3p4q5
Create Date: 2026-08-10 17:18:35.676139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '092dafc12d61'
down_revision: Union[str, None] = 'l0m1n2o3p4q5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    table = sa.table(
        "language_entry",
        sa.column("code", sa.Text),
        sa.column("display_name", sa.Text),
        sa.column("whisper_lang", sa.Text),
        sa.column("script", sa.Text),
        sa.column("transliterate_from", sa.Text),
        sa.column("is_default", sa.Boolean),
    )

    op.bulk_insert(table, [
        dict(code="russian", display_name="Russian (Русский)",
             whisper_lang="ru", script="cyrillic",
             transliterate_from=None, is_default=False),
    ])


def downgrade() -> None:
    op.execute("DELETE FROM language_entry WHERE code = 'russian'")

