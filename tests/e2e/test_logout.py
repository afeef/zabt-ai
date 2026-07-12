# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""
E2E Test: Logout Flow (015-logout-button)

Tests the logout functionality via the sidebar profile dropdown menu.

Prerequisites:
  - Set E2E_BASE_URL, E2E_TEST_EMAIL, and E2E_TEST_PASSWORD in your .env.test
  - The frontend web app must be running at the configured BASE_URL
  - Run with: pytest tests/e2e/test_logout.py --headed (or headless)

Covers:
  - User Story 1 (P1): Logout from sidebar
  - User Story 2 (P2): Logout confirmation (confirm + cancel)
  - Edge case: Protected route access after logout
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


def _login(page: Page):
    """Helper: log in with test credentials."""
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign In").click()
    # Wait for dashboard to load (sidebar visible)
    page.wait_for_url(f"{BASE_URL}/", timeout=10000)


class TestLogoutFlow:
    """
    User Story 1 (P1): Logout from Sidebar
    User Story 2 (P2): Logout Confirmation

    Acceptance Scenarios Covered:
      1. Logged-in user clicks profile → dropdown opens → clicks Logout →
         confirmation appears → clicks Confirm → redirected to /login.
      2. Logged-in user clicks Logout → clicks Cancel → stays logged in.
      3. After logout → navigating to protected route → redirected to /login.
    """

    def test_logout_with_confirmation(self, page: Page):
        """
        Scenario 1: Full logout flow with confirmation.
        Given I am logged in,
        When I click the profile section, click Logout, and click Confirm,
        Then my session is terminated and I am redirected to the login page.
        """
        _login(page)

        # Click the profile section in the sidebar to open dropdown
        page.get_by_role("button").filter(has_text=TEST_EMAIL.split("@")[0]).click()

        # Verify dropdown is visible with Logout option
        logout_button = page.get_by_role("button", name="Logout")
        expect(logout_button).to_be_visible()

        # Click Logout — confirmation prompt should appear
        logout_button.click()

        # Verify confirmation state
        confirm_button = page.get_by_role("button", name="Confirm")
        expect(confirm_button).to_be_visible()
        expect(page.get_by_text("Confirm logout?")).to_be_visible()

        # Click Confirm — should redirect to login
        confirm_button.click()
        page.wait_for_url(f"{BASE_URL}/login", timeout=10000)
        expect(page).to_have_url(f"{BASE_URL}/login")

    def test_logout_cancel_stays_logged_in(self, page: Page):
        """
        Scenario 2: Cancel logout keeps user logged in.
        Given I am logged in and I click Logout,
        When the confirmation appears and I click Cancel,
        Then I remain logged in and on the same page.
        """
        _login(page)

        # Open profile dropdown
        page.get_by_role("button").filter(has_text=TEST_EMAIL.split("@")[0]).click()

        # Click Logout
        page.get_by_role("button", name="Logout").click()

        # Click Cancel
        page.get_by_role("button", name="Cancel").click()

        # Should still be on the dashboard (not redirected)
        expect(page).to_have_url(f"{BASE_URL}/")

        # Dropdown should close or revert to normal menu items
        # Verify we can still see nav elements (still authenticated)
        expect(page.get_by_text("Meetings")).to_be_visible()

    def test_protected_route_after_logout(self, page: Page):
        """
        Scenario 3: Cannot access protected routes after logout.
        Given I have logged out,
        When I navigate to a protected route,
        Then I am redirected to the login page.
        """
        _login(page)

        # Perform full logout
        page.get_by_role("button").filter(has_text=TEST_EMAIL.split("@")[0]).click()
        page.get_by_role("button", name="Logout").click()
        page.get_by_role("button", name="Confirm").click()
        page.wait_for_url(f"{BASE_URL}/login", timeout=10000)

        # Try to access a protected route directly
        page.goto(f"{BASE_URL}/meetings")

        # Should be redirected to login
        page.wait_for_url(f"{BASE_URL}/login", timeout=10000)
        expect(page).to_have_url(f"{BASE_URL}/login")
