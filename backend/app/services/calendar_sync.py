# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Calendar sync service — fetches events from Microsoft Graph and upserts into CalendarEvent table.

Handles token refresh on 401, detects conferencing platforms, and
removes cancelled events (future events no longer present in the API response).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.engine import engine
from app.models.calendar_event import BotStatus, CalendarEvent
from app.models.integration import Integration, IntegrationProvider
from app.services.integration import integration_service
from app.services.microsoft_graph import MicrosoftGraphClient, MicrosoftGraphError

logger = get_logger(__name__)


class CalendarSyncService:
    """Syncs calendar events from Microsoft Graph into the local database."""

    # ------------------------------------------------------------------
    # Graph client factory
    # ------------------------------------------------------------------

    def _get_graph_client(self) -> MicrosoftGraphClient:
        """Create a MicrosoftGraphClient from application settings."""
        return MicrosoftGraphClient(
            client_id=settings.MICROSOFT_CLIENT_ID,
            client_secret=settings.MICROSOFT_CLIENT_SECRET,
            tenant_id=settings.MICROSOFT_TENANT_ID,
            redirect_uri=settings.MICROSOFT_REDIRECT_URI,
        )

    # ------------------------------------------------------------------
    # Platform detection
    # ------------------------------------------------------------------

    @staticmethod
    def _to_naive_utc(dt: datetime) -> datetime:
        """Coerce a datetime to naive UTC.

        The ``calendarevent.start_time`` / ``end_time`` columns are stored
        naive in Postgres. Graph returns tz-aware UTC datetimes. Without
        normalization, the in-memory attribute stays aware until the DB
        roundtrip, which breaks in-process comparisons (ZABT-API-29).
        """
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _detect_platform(url: Optional[str]) -> Optional[str]:
        """Detect conferencing platform from a URL.

        Returns "teams", "zoom", "meet", or None.
        """
        if not url:
            return None
        lower = url.lower()
        if "teams.microsoft.com" in lower:
            return "teams"
        if "zoom.us" in lower:
            return "zoom"
        if "meet.google.com" in lower:
            return "meet"
        return None

    # ------------------------------------------------------------------
    # Sync orchestration
    # ------------------------------------------------------------------

    async def sync_for_integration(
        self,
        integration: Integration,
        *,
        session: Optional[Session] = None,
        existing_events: Optional[list[CalendarEvent]] = None,
    ) -> int:
        """Sync calendar events for a single integration.

        Returns the number of upserted events. Handles 401 by refreshing
        the access token once and retrying.

        When called from the Celery beat task, the caller passes a shared
        ``session`` plus a pre-loaded ``existing_events`` slice so we can
        skip re-querying per integration. Direct callers can omit both and
        the method falls back to opening its own session (legacy path).
        See ZABT-API-1Z for why this matters.
        """
        client = self._get_graph_client()
        access_token = integration_service.decrypt_token(integration.access_token)

        try:
            events = await client.fetch_calendar_events(access_token)
        except MicrosoftGraphError as exc:
            if exc.status_code != 401:
                logger.error(
                    "Graph API error for integration %s: %s",
                    integration.id,
                    exc,
                )
                raise

            # Token expired — attempt refresh
            logger.info(
                "Access token expired for integration %s, refreshing…",
                integration.id,
            )
            try:
                refresh_token = integration_service.decrypt_token(
                    integration.refresh_token
                )
                token_data = await client.refresh_access_token(refresh_token)
                integration_service.update_tokens(
                    integration_id=integration.id,
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get(
                        "refresh_token", refresh_token
                    ),
                    expires_in=token_data.get("expires_in", 3600),
                )
                access_token = token_data["access_token"]
                events = await client.fetch_calendar_events(access_token)
            except MicrosoftGraphError:
                logger.warning(
                    "Token refresh failed for integration %s, marking expired",
                    integration.id,
                )
                integration_service.mark_expired(integration.id)
                raise

        if session is not None:
            count = self._upsert_events(
                integration, events, session=session, existing_events=existing_events or [],
            )
        else:
            with Session(engine) as owned_session:
                existing = list(
                    owned_session.exec(
                        select(CalendarEvent).where(
                            CalendarEvent.integration_id == integration.id
                        )
                    ).all()
                )
                count = self._upsert_events(
                    integration, events, session=owned_session, existing_events=existing,
                )
        logger.info(
            "Synced %d events for integration %s (user %s)",
            count,
            integration.id,
            integration.user_id,
        )
        return count

    # ------------------------------------------------------------------
    # Upsert / cleanup
    # ------------------------------------------------------------------

    def _upsert_events(
        self,
        integration: Integration,
        events: list[dict],
        *,
        session: Session,
        existing_events: list[CalendarEvent],
    ) -> int:
        """Upsert events and remove cancelled future events.

        Requires a caller-owned ``session`` plus the pre-loaded
        ``existing_events`` for this integration. We used to issue two
        SELECTs here (one for the full set, one filtered by end_time);
        both are now derived from ``existing_events`` in memory. See
        ZABT-API-1V (the future-events query) and ZABT-API-1Z (the
        per-integration batch load when iterated across integrations).

        ``end_time`` is stored naive in the DB, so compare against a
        naive ``now`` when filtering in Python.
        """
        now = datetime.now(timezone.utc)
        now_naive = now.replace(tzinfo=None)
        incoming_ids: set[str] = set()

        existing_map = {ev.external_event_id: ev for ev in existing_events}

        for ev in events:
            ext_id = ev["external_event_id"]
            incoming_ids.add(ext_id)

            existing = existing_map.get(ext_id)

            # Prefer platform from the Graph response; fall back to URL detection
            platform = ev.get("conferencing_platform") or self._detect_platform(
                ev.get("join_url")
            )

            start_time = self._to_naive_utc(ev["start_time"])
            end_time = self._to_naive_utc(ev["end_time"])

            if existing:
                existing.title = ev["title"]
                existing.start_time = start_time
                existing.end_time = end_time
                existing.conferencing_platform = platform
                existing.join_url = ev.get("join_url")
                existing.organizer_email = ev.get("organizer_email")
                existing.attendees = ev.get("attendees", [])
                existing.updated_at = now_naive
                session.add(existing)
            else:
                new_event = CalendarEvent(
                    user_id=integration.user_id,
                    integration_id=integration.id,
                    provider=IntegrationProvider.MICROSOFT.value,
                    external_event_id=ext_id,
                    title=ev["title"],
                    start_time=start_time,
                    end_time=end_time,
                    conferencing_platform=platform,
                    join_url=ev.get("join_url"),
                    organizer_email=ev.get("organizer_email"),
                    attendees=ev.get("attendees", []),
                    created_at=now_naive,
                    updated_at=now_naive,
                )
                session.add(new_event)

        # Delete future events that are no longer in the API response
        # (cancelled). Derive from the cached set — no DB query.
        for fe in existing_map.values():
            if self._to_naive_utc(fe.end_time) < now_naive:
                continue
            if fe.external_event_id in incoming_ids:
                continue
            # Skip if linked to a meeting or being handled by a bot (FK)
            if fe.meeting_id is not None or fe.bot_status != BotStatus.IDLE:
                logger.info(
                    "Skipping deletion of event %s (%s) — has linked records",
                    fe.external_event_id, fe.title,
                )
                continue
            from app.models.bot_job import BotJob
            bot_jobs = session.exec(
                select(BotJob).where(BotJob.calendar_event_id == fe.id)
            ).all()
            if bot_jobs:
                logger.info(
                    "Skipping deletion of event %s (%s) — has %d bot jobs",
                    fe.external_event_id, fe.title, len(bot_jobs),
                )
                continue
            logger.debug(
                "Removing cancelled event %s (%s)",
                fe.external_event_id, fe.title,
            )
            session.delete(fe)

        session.commit()

        return len(events)

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_events_for_user(self, user_id: int) -> list[CalendarEvent]:
        """Return upcoming events (end_time >= now) for a user, ordered by start_time."""
        now = datetime.now(timezone.utc)
        with Session(engine) as session:
            stmt = (
                select(CalendarEvent)
                .where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.end_time >= now,
                )
                .order_by(CalendarEvent.start_time)
            )
            return list(session.exec(stmt).all())

    def update_auto_join(
        self, event_id: int, user_id: int, auto_join: bool
    ) -> Optional[CalendarEvent]:
        """Toggle auto_join for a calendar event.

        Returns the updated CalendarEvent, or None if not found / not owned by user.
        """
        with Session(engine) as session:
            stmt = select(CalendarEvent).where(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id,
            )
            event = session.exec(stmt).first()
            if not event:
                return None
            event.auto_join = auto_join
            event.updated_at = datetime.now(timezone.utc)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event


calendar_sync_service = CalendarSyncService()
