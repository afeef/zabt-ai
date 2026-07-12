# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""E2E tests for the Summary Toolbar on the meeting detail page.

Prerequisites:
- Playwright for Python installed (`pip install playwright && playwright install`)
- Frontend running at BASE_URL (default: http://localhost:3000)
- A completed meeting exists in the database
- User is authenticated (cookie/session setup in conftest)
"""

import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000")
COMPLETED_MEETING_ID = os.getenv("E2E_COMPLETED_MEETING_ID", "")


@pytest.fixture(autouse=True)
def skip_if_no_meeting():
    if not COMPLETED_MEETING_ID:
        pytest.skip("E2E_COMPLETED_MEETING_ID not set")


def navigate_to_meeting(page: Page) -> None:
    page.goto(f"{BASE_URL}/meetings/{COMPLETED_MEETING_ID}")
    page.wait_for_load_state("networkidle")


def test_summary_tab_shows_toolbar(page: Page) -> None:
    """Toolbar is visible on the Summary tab for a completed meeting."""
    navigate_to_meeting(page)
    # Summary tab should be active by default
    toolbar = page.locator("[data-testid='summary-toolbar']")
    if toolbar.count() == 0:
        # Fallback: look for the toolbar by its button content
        toolbar = page.locator("text=Export").first
    expect(toolbar).to_be_visible()


def test_exports_dropdown_shows_three_items(page: Page) -> None:
    """Exports dropdown contains Copy, .txt, and PDF options."""
    navigate_to_meeting(page)
    # Open exports dropdown
    page.get_by_role("button", name="Export").click()
    expect(page.get_by_text("Copy summary")).to_be_visible()
    expect(page.get_by_text("Download as .txt")).to_be_visible()
    expect(page.get_by_text("Download as PDF")).to_be_visible()


def test_templates_dropdown_loads(page: Page) -> None:
    """Templates dropdown opens and loads template list."""
    navigate_to_meeting(page)
    # Click the templates trigger (contains "Template:" text)
    page.locator("button:has-text('Template:')").click()
    # Should show at least the "Built-in" section label
    expect(page.get_by_text("Built-in")).to_be_visible()


def test_transcript_tab_hides_toolbar(page: Page) -> None:
    """Toolbar is NOT visible on the Transcript tab."""
    navigate_to_meeting(page)
    # Switch to Transcript tab
    page.get_by_role("tab", name="Transcript").click()
    # Toolbar should not be visible
    export_button = page.get_by_role("button", name="Export")
    expect(export_button).not_to_be_visible()


def test_transcript_tab_has_download_pdf(page: Page) -> None:
    """Transcript tab has a Download PDF button."""
    navigate_to_meeting(page)
    page.get_by_role("tab", name="Transcript").click()
    expect(page.get_by_role("button", name="Download PDF")).to_be_visible()
