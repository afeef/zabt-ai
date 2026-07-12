# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Integration endpoints — connect/disconnect OAuth providers, calendar events."""

import secrets
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.models import User
from app.models.calendar_event import CalendarEventRead, CalendarEventUpdate
from app.models.integration import (
    IntegrationConnectResponse,
    IntegrationProvider,
    IntegrationRead,
)
from app.services.calendar_sync import calendar_sync_service
from app.services.integration import integration_service
from app.services.microsoft_graph import MicrosoftGraphClient

router = APIRouter()


def _get_graph_client() -> MicrosoftGraphClient:
    return MicrosoftGraphClient(
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_secret=settings.MICROSOFT_CLIENT_SECRET,
        tenant_id=settings.MICROSOFT_TENANT_ID,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
    )


# ── List integrations ───────────────────────────────────────────────────────

@router.get("/", response_model=List[IntegrationRead])
def list_integrations(user: User = Depends(get_current_active_user)):
    """Return all integrations for the current user."""
    return integration_service.get_for_user(user.id)


# ── Connect provider ────────────────────────────────────────────────────────

@router.post("/{provider}/connect", response_model=IntegrationConnectResponse)
def connect_provider(
    provider: str,
    user: User = Depends(get_current_active_user),
):
    """Build an OAuth authorization URL for the given provider."""
    if provider != IntegrationProvider.MICROSOFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )

    state = f"{user.id}:{secrets.token_urlsafe(16)}"
    client = _get_graph_client()
    auth_url = client.build_auth_url(state)
    return IntegrationConnectResponse(auth_url=auth_url)


# ── OAuth callback ──────────────────────────────────────────────────────────

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
):
    """Exchange authorization code for tokens and redirect to the app."""
    if provider != IntegrationProvider.MICROSOFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )

    # Parse user_id from state
    parts = state.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    try:
        user_id = int(parts[0])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    client = _get_graph_client()

    # Exchange code for tokens
    token_data = await client.exchange_code(code)
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 3600)
    scopes = token_data.get("scope", "").split()

    # Fetch user profile from Microsoft Graph
    profile = await client.get_user_profile(access_token)

    # Upsert integration
    integration_service.upsert_from_oauth(
        user_id=user_id,
        provider=IntegrationProvider.MICROSOFT,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        scopes=scopes,
        provider_user_id=profile.get("id"),
        provider_email=profile.get("email"),
    )

    redirect_url = f"{settings.APP_URL}/integrations?connected=microsoft"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


# ── Disconnect provider ─────────────────────────────────────────────────────

@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_provider(
    provider: str,
    user: User = Depends(get_current_active_user),
):
    """Remove an integration for the given provider."""
    if provider != IntegrationProvider.MICROSOFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )

    deleted = integration_service.disconnect(user.id, IntegrationProvider.MICROSOFT)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )


# ── Calendar events ─────────────────────────────────────────────────────────

@router.get("/calendar/events", response_model=List[CalendarEventRead])
def list_calendar_events(user: User = Depends(get_current_active_user)):
    """Return upcoming calendar events for the current user."""
    return calendar_sync_service.get_events_for_user(user.id)


@router.patch("/calendar/events/{event_id}", response_model=CalendarEventRead)
def update_calendar_event(
    event_id: int,
    body: CalendarEventUpdate,
    user: User = Depends(get_current_active_user),
):
    """Toggle auto_join for a calendar event."""
    if body.auto_join is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )

    event = calendar_sync_service.update_auto_join(event_id, user.id, body.auto_join)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )
    return event


# ── Bot callback ───────────────────────────────────────────────────────────

@router.post("/bot-callback")
async def bot_callback(request: Request) -> Any:
    """Handle callback from bot worker when a meeting recording ends."""
    from app.services.bot_orchestration import bot_orchestration_service

    body = await request.json()
    bot_orchestration_service.handle_callback(body)
    return {"status": "ok"}
