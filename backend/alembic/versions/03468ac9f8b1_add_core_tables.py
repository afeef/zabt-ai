"""Add core tables

Revision ID: 03468ac9f8b1
Revises: d43ee14463f8
Create Date: 2026-02-15 19:25:00.261394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '03468ac9f8b1'
down_revision: Union[str, None] = 'd43ee14463f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SummaryTemplate (must come before user/meeting which reference it)
    op.create_table(
        'summarytemplate',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('body', sa.String(), nullable=False),
        sa.Column('template_type', sa.String(), nullable=False, server_default=sa.text("'custom'")),
        sa.Column('is_system_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('owner_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # User
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('picture', sa.String(), nullable=True),
        sa.Column('tier', sa.String(), nullable=False, server_default=sa.text("'free'")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('minutes_used_this_month', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('supabase_id', sa.String(), nullable=False, unique=True, index=True),
    )

    # Add FK from summarytemplate.owner_id -> user.id (now that user exists)
    op.create_foreign_key('fk_summarytemplate_owner', 'summarytemplate', 'user', ['owner_id'], ['id'])

    # Meeting
    op.create_table(
        'meeting',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default=sa.text("'pending_upload'")),
        sa.Column('sub_status', sa.String(), nullable=True),
        sa.Column('transcript_text', sa.Text(), nullable=True),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('action_items_text', sa.Text(), nullable=True),
    )

    # TranscriptSegment
    op.create_table(
        'transcriptsegment',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('meeting_id', sa.Integer(), sa.ForeignKey('meeting.id'), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('speaker', sa.String(), nullable=True),
        sa.Column('words', JSONB(), nullable=True),
    )

    # StyleProfile
    op.create_table(
        'styleprofile',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('prompt_template', sa.String(), nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
    )

    # Subscription
    op.create_table(
        'subscription',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('stripe_custer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), nullable=False, server_default=sa.text("'free'")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('current_period_end', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('subscription')
    op.drop_table('styleprofile')
    op.drop_table('transcriptsegment')
    op.drop_table('meeting')
    op.drop_constraint('fk_summarytemplate_owner', 'summarytemplate', type_='foreignkey')
    op.drop_table('user')
    op.drop_table('summarytemplate')
