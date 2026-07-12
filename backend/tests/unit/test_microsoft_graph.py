"""Unit tests for MicrosoftGraphClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse, parse_qs

from app.services.microsoft_graph import (
    MicrosoftGraphClient,
    MicrosoftGraphError,
    SCOPES,
    MICROSOFT_AUTH_BASE,
    GRAPH_API_BASE,
)


@pytest.fixture
def graph_client():
    return MicrosoftGraphClient(
        client_id="test-client-id",
        client_secret="test-client-secret",
        tenant_id="test-tenant-id",
        redirect_uri="https://example.com/callback",
    )


class TestBuildAuthUrl:
    def test_contains_client_id(self, graph_client: MicrosoftGraphClient):
        url = graph_client.build_auth_url(state="abc123")
        parsed = parse_qs(urlparse(url).query)
        assert parsed["client_id"] == ["test-client-id"]

    def test_contains_state(self, graph_client: MicrosoftGraphClient):
        url = graph_client.build_auth_url(state="my-state-value")
        parsed = parse_qs(urlparse(url).query)
        assert parsed["state"] == ["my-state-value"]

    def test_contains_scopes(self, graph_client: MicrosoftGraphClient):
        url = graph_client.build_auth_url(state="s")
        parsed = parse_qs(urlparse(url).query)
        scope_str = parsed["scope"][0]
        for scope in SCOPES:
            assert scope in scope_str

    def test_response_type_is_code(self, graph_client: MicrosoftGraphClient):
        url = graph_client.build_auth_url(state="s")
        parsed = parse_qs(urlparse(url).query)
        assert parsed["response_type"] == ["code"]

    def test_uses_correct_auth_base(self, graph_client: MicrosoftGraphClient):
        url = graph_client.build_auth_url(state="s")
        assert url.startswith(MICROSOFT_AUTH_BASE)

    def test_includes_tenant_in_url(self, graph_client: MicrosoftGraphClient):
        url = graph_client.build_auth_url(state="s")
        assert "/test-tenant-id/" in url


class TestExchangeCode:
    @pytest.mark.asyncio
    async def test_returns_tokens(self, graph_client: MicrosoftGraphClient):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "at-123",
            "refresh_token": "rt-456",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await graph_client.exchange_code("auth-code-xyz")

        assert result["access_token"] == "at-123"
        assert result["refresh_token"] == "rt-456"
        mock_instance.post.assert_called_once()
        call_kwargs = mock_instance.post.call_args
        assert "auth-code-xyz" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_raises_on_error(self, graph_client: MicrosoftGraphClient):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Code expired",
        }
        mock_response.text = '{"error":"invalid_grant"}'

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            with pytest.raises(MicrosoftGraphError) as exc_info:
                await graph_client.exchange_code("bad-code")
            assert exc_info.value.status_code == 400


class TestRefreshAccessToken:
    @pytest.mark.asyncio
    async def test_returns_new_tokens(self, graph_client: MicrosoftGraphClient):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-at",
            "refresh_token": "new-rt",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await graph_client.refresh_access_token("old-refresh-token")

        assert result["access_token"] == "new-at"


class TestFetchCalendarEvents:
    @pytest.mark.asyncio
    async def test_normalizes_events(self, graph_client: MicrosoftGraphClient):
        raw_events = {
            "value": [
                {
                    "id": "event-1",
                    "subject": "Weekly Standup",
                    "start": {"dateTime": "2026-04-03T10:00:00.0000000", "timeZone": "UTC"},
                    "end": {"dateTime": "2026-04-03T10:30:00.0000000", "timeZone": "UTC"},
                    "onlineMeeting": {
                        "joinUrl": "https://teams.microsoft.com/l/meetup-join/abc123"
                    },
                    "organizer": {
                        "emailAddress": {"address": "org@example.com", "name": "Organizer"}
                    },
                    "attendees": [
                        {
                            "emailAddress": {"address": "alice@example.com", "name": "Alice"},
                            "status": {"response": "accepted"},
                        },
                        {
                            "emailAddress": {"address": "bob@example.com", "name": "Bob"},
                            "status": {"response": "tentativelyAccepted"},
                        },
                    ],
                },
                {
                    "id": "event-2",
                    "subject": "Zoom Call",
                    "start": {"dateTime": "2026-04-03T14:00:00.0000000", "timeZone": "UTC"},
                    "end": {"dateTime": "2026-04-03T15:00:00.0000000", "timeZone": "UTC"},
                    "onlineMeeting": None,
                    "location": {
                        "displayName": "https://zoom.us/j/123456789"
                    },
                    "organizer": {
                        "emailAddress": {"address": "org@example.com", "name": "Organizer"}
                    },
                    "attendees": [],
                    "body": {
                        "content": "Join via https://zoom.us/j/123456789"
                    },
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = raw_events
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            events = await graph_client.fetch_calendar_events("access-token-123", window_hours=24)

        assert len(events) == 2

        # First event: Teams meeting
        e1 = events[0]
        assert e1["external_event_id"] == "event-1"
        assert e1["title"] == "Weekly Standup"
        assert e1["conferencing_platform"] == "teams"
        assert "teams.microsoft.com" in e1["join_url"]
        assert e1["organizer_email"] == "org@example.com"
        assert len(e1["attendees"]) == 2
        assert e1["attendees"][0]["email"] == "alice@example.com"
        assert e1["attendees"][0]["name"] == "Alice"

        # Second event: Zoom link in location/body
        e2 = events[1]
        assert e2["external_event_id"] == "event-2"
        assert e2["conferencing_platform"] == "zoom"
        assert "zoom.us" in e2["join_url"]

    @pytest.mark.asyncio
    async def test_event_without_conferencing(self, graph_client: MicrosoftGraphClient):
        raw_events = {
            "value": [
                {
                    "id": "event-3",
                    "subject": "Lunch",
                    "start": {"dateTime": "2026-04-03T12:00:00.0000000", "timeZone": "UTC"},
                    "end": {"dateTime": "2026-04-03T13:00:00.0000000", "timeZone": "UTC"},
                    "onlineMeeting": None,
                    "organizer": {
                        "emailAddress": {"address": "org@example.com", "name": "Organizer"}
                    },
                    "attendees": [],
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = raw_events
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            events = await graph_client.fetch_calendar_events("token")

        assert events[0]["conferencing_platform"] is None
        assert events[0]["join_url"] is None


class TestGetUserProfile:
    @pytest.mark.asyncio
    async def test_returns_profile(self, graph_client: MicrosoftGraphClient):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "user-id-123",
            "mail": "user@example.com",
            "displayName": "Test User",
            "userPrincipalName": "user@example.com",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            profile = await graph_client.get_user_profile("access-token")

        assert profile["id"] == "user-id-123"
        assert profile["email"] == "user@example.com"
        assert profile["display_name"] == "Test User"


class TestSendEmail:
    @pytest.mark.asyncio
    async def test_send_email(self, graph_client: MicrosoftGraphClient):
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.text = ""

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await graph_client.send_email(
                access_token="token-123",
                to_email="recipient@example.com",
                to_name="Recipient Name",
                subject="Meeting Summary",
                html_body="<h1>Summary</h1><p>Notes here.</p>",
            )

        mock_instance.post.assert_called_once()
        call_kwargs = mock_instance.post.call_args
        assert "sendMail" in str(call_kwargs)
        # Verify payload structure
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["message"]["subject"] == "Meeting Summary"
        assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == "recipient@example.com"
        assert payload["saveToSentItems"] is True

    @pytest.mark.asyncio
    async def test_send_email_raises_on_error(self, graph_client: MicrosoftGraphClient):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = '{"error":"MailboxNotEnabledForRESTAPI"}'

        with patch("app.services.microsoft_graph.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            with pytest.raises(MicrosoftGraphError) as exc_info:
                await graph_client.send_email(
                    access_token="bad-token",
                    to_email="recipient@example.com",
                    to_name="Recipient",
                    subject="Test",
                    html_body="<p>Test</p>",
                )
            assert exc_info.value.status_code == 403


