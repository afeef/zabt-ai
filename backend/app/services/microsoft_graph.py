# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Microsoft Graph API client for OAuth token exchange and email sending.

Handles Microsoft OAuth2 PKCE flow (authorization code grant) and
calls Graph API v1.0 endpoints for user profile and email.
"""

import logging
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
