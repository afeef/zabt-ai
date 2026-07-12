# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""
E2E Test: Server-Side PDF Export

Tests PDF download for both summary and transcript from the meeting detail page:
  - Summary "Download PDF" triggers a download with correct filename pattern
  - Transcript "Download PDF" button visible and triggers download

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Environment variables:
    FRONTEND_URL         Base URL of the running frontend (default: http://localhost:3000)
    TEST_USER_EMAIL      Email of a test user with at least one completed meeting
    TEST_USER_PASSWORD   Password for the test user
    TEST_MEETING_ID      ID of a completed meeting with transcript segments

Run:
    pytest tests/e2e/test_pdf_export.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")
TEST_MEETING_ID = os.environ.get("TEST_MEETING_ID", "")


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=10_000)


def navigate_to_meeting(page: Page) -> None:
    page.goto(f"{BASE_URL}/meetings/{TEST_MEETING_ID}")
    page.wait_for_timeout(1000)


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_summary_pdf_download(page: Page) -> None:
    """Clicking Download PDF on Summary tab triggers a PDF download."""
    login(page)
    navigate_to_meeting(page)

    # Summary tab should be visible — click the menu to find Download PDF
    page.get_by_role("button", name="Summary").click()
    page.wait_for_timeout(500)

    # Look for the Download PDF option in the summary menu
    with page.expect_download(timeout=30_000) as download_info:
        page.get_by_text("Download PDF").first.click()

    download = download_info.value
    filename = download.suggested_filename
    assert filename.endswith("-summary.pdf"), (
        f"Expected filename ending with '-summary.pdf', got '{filename}'"
    )


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_transcript_pdf_button_visible(page: Page) -> None:
    """Download PDF button is visible on Transcript tab for a completed meeting."""
    login(page)
    navigate_to_meeting(page)

    page.get_by_role("button", name="Transcript").click()
    page.wait_for_timeout(500)

    download_btn = page.get_by_role("button", name="Download PDF")
    expect(download_btn).to_be_visible()


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_transcript_pdf_download(page: Page) -> None:
    """Clicking Download PDF on Transcript tab triggers a PDF download."""
    login(page)
    navigate_to_meeting(page)

    page.get_by_role("button", name="Transcript").click()
    page.wait_for_timeout(500)

    download_btn = page.get_by_role("button", name="Download PDF")
    expect(download_btn).to_be_visible()

    with page.expect_download(timeout=30_000) as download_info:
        download_btn.click()

    download = download_info.value
    filename = download.suggested_filename
    assert filename.endswith("-transcript.pdf"), (
        f"Expected filename ending with '-transcript.pdf', got '{filename}'"
    )
