# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from playwright.sync_api import Page, expect

def login(page: Page) -> None:
    """Helper to log in using Playwright"""
    page.goto("http://localhost:3000/login")
    page.fill('input[placeholder="name@example.com"]', 'test@example.com')
    page.fill('input[type="password"]', 'password123')
    page.click('button:has-text("Sign In")')
    # Wait for navigation to dashboard
    expect(page.locator("text=Upcoming Meetings")).to_be_visible()

def test_meeting_delete_flow(page: Page) -> None:
    """T006: Verifies the successful deletion flow from the UI menu."""
    login(page)

    # 1. Mock the API response to simulate having a meeting to delete
    # First, mock the initial GET /meetings/ to show one completed meeting
    page.route("**/api/v1/meetings/?skip=0&limit=20", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": 999, "title": "test_meeting_to_delete.mp4", "status": "completed", "created_at": "2026-02-22T00:00:00Z"}]',
    ))

    # Needs a reload to catch the mocked route
    page.goto("http://localhost:3000/meetings")
    expect(page.get_by_text("test_meeting_to_delete.mp4")).to_be_visible()

    # 2. Mock the DELETE route
    page.route("**/api/v1/meetings/999", lambda route: route.fulfill(
        status=204,
        body="",
    ))

    # 3. Handle the window.confirm dialog automatically
    page.on("dialog", lambda dialog: dialog.accept())

    # 4. Perform the deletion flow
    # Click the 3-dot dropdown summary element
    page.locator("summary").first.click()

    # Click the Delete button inside the dropdown
    page.get_by_role("button", name="Delete").click()

    # 5. Assert the optimistic UI update removes the meeting
    expect(page.get_by_text("test_meeting_to_delete.mp4")).not_to_be_visible()

    # Assert the empty state appears since it was the only meeting
    expect(page.get_by_text("No meetings yet")).to_be_visible()
