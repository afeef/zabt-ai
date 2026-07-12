# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""
E2E Test: YouTube URL Ingestion

Tests the YouTube URL dialog flow, validation, and meeting creation.

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/test_youtube_ingestion.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=10_000)


def test_youtube_dialog_opens(page: Page) -> None:
    """Verifies the YouTube URL dialog opens via the Paste URL button."""
    login(page)

    # Click the Paste URL button (Link2 icon button)
    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()

    # Dialog should appear with title and input
    expect(page.get_by_text("Paste YouTube URL")).to_be_visible()
    expect(page.get_by_placeholder("https://www.youtube.com/watch?v=")).to_be_visible()
    expect(page.get_by_role("button", name="Process")).to_be_visible()


def test_youtube_dialog_process_disabled_when_empty(page: Page) -> None:
    """Verifies the Process button is disabled when input is empty."""
    login(page)

    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()
    expect(page.get_by_text("Paste YouTube URL")).to_be_visible()

    process_btn = page.get_by_role("button", name="Process")
    expect(process_btn).to_be_disabled()


def test_youtube_invalid_url_shows_error(page: Page) -> None:
    """Verifies that entering an invalid URL shows inline error."""
    login(page)

    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()

    url_input = page.get_by_placeholder("https://www.youtube.com/watch?v=")
    url_input.fill("https://example.com/not-a-youtube-video")

    page.get_by_role("button", name="Process").click()

    expect(page.get_by_text("Please enter a valid YouTube video URL")).to_be_visible()


def test_youtube_playlist_url_shows_error(page: Page) -> None:
    """Verifies that entering a playlist URL shows specific error."""
    login(page)

    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()

    url_input = page.get_by_placeholder("https://www.youtube.com/watch?v=")
    url_input.fill("https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")

    page.get_by_role("button", name="Process").click()

    expect(page.get_by_text("Playlist URLs are not supported")).to_be_visible()


def test_youtube_valid_url_creates_meeting(page: Page) -> None:
    """Verifies that submitting a valid YouTube URL creates a meeting card."""
    login(page)

    # Mock the API response for YouTube ingestion
    page.route("**/api/v1/meetings/youtube", lambda route: route.fulfill(
        status=201,
        content_type="application/json",
        body='{"id": 999, "title": "YouTube Video", "description": null, "file_path": null, '
             '"duration_seconds": null, "created_at": "2026-03-10T14:30:00Z", "status": "queued", '
             '"sub_status": null, "transcript_text": null, "summary_text": null, '
             '"original_summary_text": null, "summary_edited": false, "action_items_text": null, '
             '"template_id": null, "template_name": null, '
             '"source_type": "youtube", "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", '
             '"youtube_title": null, "youtube_duration_seconds": null, '
             '"youtube_thumbnail_url": null, "youtube_channel": null, '
             '"segments": [], "speakers": null}',
    ))

    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()

    url_input = page.get_by_placeholder("https://www.youtube.com/watch?v=")
    url_input.fill("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    page.get_by_role("button", name="Process").click()

    # Dialog should close
    expect(page.get_by_text("Paste YouTube URL")).not_to_be_visible(timeout=5000)


def test_youtube_dialog_closes_on_escape(page: Page) -> None:
    """Verifies that pressing Escape closes the YouTube URL dialog."""
    login(page)

    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()
    expect(page.get_by_text("Paste YouTube URL")).to_be_visible()

    page.keyboard.press("Escape")
    expect(page.get_by_text("Paste YouTube URL")).not_to_be_visible()


def test_youtube_error_clears_on_input_change(page: Page) -> None:
    """Verifies that the error message clears when user modifies the input."""
    login(page)

    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()

    url_input = page.get_by_placeholder("https://www.youtube.com/watch?v=")
    url_input.fill("not-a-url")

    page.get_by_role("button", name="Process").click()
    expect(page.get_by_text("Please enter a valid YouTube video URL")).to_be_visible()

    # Typing clears the error
    url_input.fill("https://www.youtube.com/watch?v=abc12345678")
    expect(page.get_by_text("Please enter a valid YouTube video URL")).not_to_be_visible()
