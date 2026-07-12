# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""cascade delete integration → calendarevent → botjob

Disconnecting a Microsoft integration (DELETE /api/v1/integrations/microsoft)
raised ForeignKeyViolation because calendarevent rows still referenced
integration.id with no ON DELETE rule (Sentry ZABT-API-18). Cascade
removes the synced events — and transitively their bot jobs — when
the integration is disconnected.

Revision ID: k9l0m1n2o3p4
Revises: j8k9l0m1n2o3
Create Date: 2026-04-19
"""
from alembic import op


revision = "k9l0m1n2o3p4"
down_revision = "j8k9l0m1n2o3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # calendarevent.integration_id → integration.id — CASCADE
    op.drop_constraint(
        "calendarevent_integration_id_fkey",
        "calendarevent",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "calendarevent_integration_id_fkey",
        "calendarevent",
        "integration",
        ["integration_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # botjob.calendar_event_id → calendarevent.id — CASCADE
    # Needed because the calendarevent cascade above would otherwise be
    # blocked by dangling botjob rows.
    op.drop_constraint(
        "botjob_calendar_event_id_fkey",
        "botjob",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "botjob_calendar_event_id_fkey",
        "botjob",
        "calendarevent",
        ["calendar_event_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "botjob_calendar_event_id_fkey",
        "botjob",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "botjob_calendar_event_id_fkey",
        "botjob",
        "calendarevent",
        ["calendar_event_id"],
        ["id"],
    )

    op.drop_constraint(
        "calendarevent_integration_id_fkey",
        "calendarevent",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "calendarevent_integration_id_fkey",
        "calendarevent",
        "integration",
        ["integration_id"],
        ["id"],
    )
