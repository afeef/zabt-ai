# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Microsoft Graph API client for OAuth token exchange and calendar event fetching.

Handles Microsoft OAuth2 PKCE flow (authorization code grant) and
calls Graph API v1.0 endpoints for user profile and calendar data.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MICROSOFT_AUTH_BASE = "https://login.microsoftonline.com"
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

SCOPES: list[str] = [
    "Calendars.Read",
    "OnlineMeetings.Read",
    "Mail.Send",
    "Files.Read.All",
    "User.Read",
    "offline_access",
]

# Patterns for detecting conferencing platform from URLs
_TEAMS_RE = re.compile(r"https?://teams\.microsoft\.com/", re.IGNORECASE)
_ZOOM_RE = re.compile(r"https?://[\w.]*zoom\.us/", re.IGNORECASE)
_MEET_RE = re.compile(r"https?://meet\.google\.com/", re.IGNORECASE)

# Generic URL pattern for extracting join links from text
_URL_RE = re.compile(r"https?://[^\s<>\"']+")


def _parse_graph_datetime(raw: str) -> datetime:
    """Parse Graph API datetime like '2026-04-10T10:00:00.0000000' into a UTC datetime.

    Graph sends 7 fractional digits; Python's fromisoformat handles up to 6.
    We truncate excess fractional digits safely (not rstrip which corrupts dates).
    """
    if not raw:
        return datetime.now(timezone.utc)
    # Truncate fractional seconds to 6 digits max (Graph sends 7)
    cleaned = re.sub(r"(\.\d{6})\d+", r"\1", raw)
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt



# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class MicrosoftGraphError(Exception):
    """Error communicating with Microsoft Graph or identity platform."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class MicrosoftGraphClient:
    """Thin async client wrapping Microsoft identity + Graph API v1.0."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        redirect_uri: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri

    # ------------------------------------------------------------------
    # OAuth helpers
    # ------------------------------------------------------------------

    def build_auth_url(self, state: str) -> str:
        """Build the Microsoft OAuth2 authorization URL."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(SCOPES),
            "state": state,
            "response_mode": "query",
        }
        base = f"{MICROSOFT_AUTH_BASE}/{self.tenant_id}/oauth2/v2.0/authorize"
        return f"{base}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        token_url = (
            f"{MICROSOFT_AUTH_BASE}/{self.tenant_id}/oauth2/v2.0/token"
        )
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(SCOPES),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if resp.status_code != 200:
            logger.error("Token exchange failed: %s", resp.text)
            raise MicrosoftGraphError(
                f"Token exchange failed: {resp.text}",
                status_code=resp.status_code,
            )

        return resp.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Use a refresh token to obtain a new access token."""
        token_url = (
            f"{MICROSOFT_AUTH_BASE}/{self.tenant_id}/oauth2/v2.0/token"
        )
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": " ".join(SCOPES),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if resp.status_code != 200:
            logger.error("Token refresh failed: %s", resp.text)
            raise MicrosoftGraphError(
                f"Token refresh failed: {resp.text}",
                status_code=resp.status_code,
            )

        return resp.json()

    # ------------------------------------------------------------------
    # Graph API calls
    # ------------------------------------------------------------------

    async def get_user_profile(self, access_token: str) -> dict:
        """Fetch the authenticated user's profile from /me."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code != 200:
            raise MicrosoftGraphError(
                f"Failed to fetch user profile: {resp.text}",
                status_code=resp.status_code,
            )

        data = resp.json()
        return {
            "id": data.get("id", ""),
            "email": data.get("mail") or data.get("userPrincipalName", ""),
            "display_name": data.get("displayName", ""),
        }

    async def fetch_calendar_events(
        self, access_token: str, window_hours: int = 24
    ) -> list[dict]:
        """Fetch calendar events within a time window and normalize them."""
        now = datetime.now(timezone.utc)
        end = now + timedelta(hours=window_hours)

        params = {
            "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
            "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
            "$orderby": "start/dateTime",
            "$top": "100",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me/calendarview",
                params=params,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Prefer": 'outlook.timezone="UTC"',
                },
            )

        if resp.status_code != 200:
            raise MicrosoftGraphError(
                f"Failed to fetch calendar events: {resp.text}",
                status_code=resp.status_code,
            )

        raw_events = resp.json().get("value", [])
        return [self._normalize_event(e) for e in raw_events]

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    async def send_email(
        self,
        access_token: str,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send an email via Microsoft Graph API on behalf of the user."""
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email,
                            "name": to_name,
                        }
                    }
                ],
            },
            "saveToSentItems": True,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_API_BASE}/me/sendMail",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code not in (200, 202):
            raise MicrosoftGraphError(
                f"Failed to send email: {resp.text}",
                status_code=resp.status_code,
            )

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize_event(self, raw: dict) -> dict:
        """Convert a Graph API event to our internal format."""
        # Extract join URL and platform
        join_url, platform = self._extract_conferencing(raw)

        organizer_addr = (
            raw.get("organizer", {}).get("emailAddress", {})
        )

        attendees = [
            {
                "email": a.get("emailAddress", {}).get("address", ""),
                "name": a.get("emailAddress", {}).get("name", ""),
            }
            for a in raw.get("attendees", [])
        ]

        # Parse datetime strings from Graph API (e.g. "2026-04-03T19:40:00.0000000")
        start_dt = _parse_graph_datetime(raw.get("start", {}).get("dateTime", ""))
        end_dt = _parse_graph_datetime(raw.get("end", {}).get("dateTime", ""))

        return {
            "external_event_id": raw.get("id", ""),
            "title": raw.get("subject") or "Untitled meeting",
            "start_time": start_dt,
            "end_time": end_dt,
            "conferencing_platform": platform,
            "join_url": join_url,
            "organizer_email": organizer_addr.get("address", ""),
            "attendees": attendees,
        }

    @staticmethod
    def _extract_conferencing(raw: dict) -> tuple[str | None, str | None]:
        """Detect conferencing platform and join URL from event data.

        Checks (in order):
        1. onlineMeeting.joinUrl (Teams native field)
        2. location.displayName
        3. body.content

        Returns (join_url, platform) where platform is one of
        "teams", "zoom", "meet", or None.
        """
        # 1. Native Teams online meeting
        online = raw.get("onlineMeeting")
        if online and online.get("joinUrl"):
            url = online["joinUrl"]
            return url, _detect_platform(url)

        # 2. Check location display name for a URL
        location_name = raw.get("location", {}).get("displayName", "") or ""
        url = _find_conferencing_url(location_name)
        if url:
            return url, _detect_platform(url)

        # 3. Check body content
        body_content = raw.get("body", {}).get("content", "") or ""
        url = _find_conferencing_url(body_content)
        if url:
            return url, _detect_platform(url)

        return None, None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_platform(url: str) -> str | None:
    """Return platform name from a conferencing URL."""
    if _TEAMS_RE.search(url):
        return "teams"
    if _ZOOM_RE.search(url):
        return "zoom"
    if _MEET_RE.search(url):
        return "meet"
    return None


def _find_conferencing_url(text: str) -> str | None:
    """Find first conferencing URL (Teams/Zoom/Meet) in a text block."""
    for match in _URL_RE.finditer(text):
        url = match.group(0)
        if _TEAMS_RE.search(url) or _ZOOM_RE.search(url) or _MEET_RE.search(url):
            return url
    return None
