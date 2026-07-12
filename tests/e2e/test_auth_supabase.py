"""
E2E Test: Supabase Registration and Login Flow (T008)

Tests the primary happy path for User Story 1 - Authentication via Hosted Supabase.

Prerequisites:
  - Set SUPABASE_URL and SUPABASE_TEST_USER/PASS in your .env.test
  - The frontend web app must be running at the configured BASE_URL
  - Run with: pytest tests/e2e/test_auth_supabase.py --headed (or headless)

Note: E2E tests use real Supabase cloud auth; no mocking of Supabase itself.
"""

import pytest
from playwright.sync_api import Page, expect
import os

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000")
TEST_EMAIL = os.getenv("E2E_TEST_EMAIL", "e2e-test@example.com")
TEST_PASSWORD = os.getenv("E2E_TEST_PASSWORD", "ChangeMe123!")


@pytest.fixture(scope="module")
def browser_context_args(browser_context_args):
    """Ignore HTTPS errors for local dev certs."""
    return {**browser_context_args, "ignore_https_errors": True}


class TestSupabaseAuthFlow:
    """
    User Story 1: Authentication via Hosted Supabase (Priority: P1)

    Acceptance Scenarios Covered:
      1. Given a new/existing user on the registration/login page,
         When they submit their details,
         Then the user is authenticated and a session is returned.
      2. Given a logged-out user navigates to the app root,
         When they have no active session,
         Then they are redirected to the login page.
    """

    def test_unauthenticated_redirect(self, page: Page):
        """
        Scenario: Unauthenticated users are redirected to login.
        """
        page.goto(BASE_URL)
        # Expect to land on auth/login page (URL or heading check)
        expect(page).to_have_url(f"{BASE_URL}/auth/login", timeout=5000)

    def test_login_with_valid_credentials(self, page: Page):
        """
        Scenario: A returning user logs in successfully via Supabase-backed auth form.
        """
        page.goto(f"{BASE_URL}/auth/login")

        page.get_by_label("Email").fill(TEST_EMAIL)
        page.get_by_label("Password").fill(TEST_PASSWORD)
        page.get_by_role("button", name="Sign In").click()

        # After login, user should land on the dashboard
        expect(page).not_to_have_url(f"{BASE_URL}/auth/login", timeout=8000)

    def test_backend_ai_endpoint_rejects_unauthenticated(self, page: Page):
        """
        Scenario: Backend AI endpoints return 401 when no bearer token is provided.
        Uses a fetch call within the browser context to call the API.
        """
        response = page.request.post(
            f"{os.getenv('E2E_API_URL', 'http://localhost:8000')}/api/v1/transcriptions/initiate",
            data=b"",
        )
        assert response.status == 401, (
            f"Expected 401 for unauthenticated AI request, got {response.status}"
        )
