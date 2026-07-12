# Feature Specification: Home Page UI Redesign

**Feature Branch**: `018-home-ui-redesign`
**Created**: 2026-03-04
**Status**: Draft
**Input**: Redesign the home page to match Otter.ai-style layout: richer meeting cards with summary previews, top action bar with Meeting URL / Import / Record buttons, remove Meetings nav item and dedicated meetings page, consolidate all meetings onto the home page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Richer Meeting List Cards (Priority: P1)

As a user viewing my home page, I want each meeting card to show a summary preview, timestamp, duration, and speaker name so I can quickly scan what each meeting was about without opening it.

**Why this priority**: The meeting list is the core content area users interact with most. Enriching the cards immediately improves daily usability and information density.

**Independent Test**: Can be tested by loading the home page with existing meetings and verifying each card displays the title, time, duration, speaker, and a truncated summary preview with a "Show more" affordance.

**Acceptance Scenarios**:

1. **Given** a completed meeting with a summary, **When** the user views the home page, **Then** the meeting card shows: meeting title (as heading), time + duration + speaker name (as subtitle), and a 2-3 line summary preview with "Show more" text if truncated.
2. **Given** a meeting without a summary (still processing or failed), **When** the user views the home page, **Then** the card shows the title, time metadata, and the current status badge — no empty summary area is displayed.
3. **Given** multiple meetings on different dates, **When** the user views the home page, **Then** meetings are grouped by date with collapsible date headers (e.g., "Sunday, Feb 22 ˅").

---

### User Story 2 - Top Action Bar with Import, Meeting URL, and Record Buttons (Priority: P2)

As a user, I want quick-access action buttons in the top bar area (Meeting URL, Import, Record) so I can start capturing meetings without navigating to a separate page or relying on the sidebar.

**Why this priority**: The current "Upload a meeting" button is buried in the right panel. Promoting actions to a visible top bar matches the Otter.ai pattern and reduces friction for the primary user action.

**Independent Test**: Can be tested by verifying the three buttons appear in the top area of the main content, and that "Import" opens the existing upload modal.

**Acceptance Scenarios**:

1. **Given** the user is on the home page, **When** they look at the area above the meeting feed, **Then** they see three action buttons: a Meeting URL button (camera icon), an "Import" button, and a "Record" button (primary/red with microphone icon).
2. **Given** the user clicks "Import", **When** the upload modal opens, **Then** the existing upload flow works unchanged.
3. **Given** the user clicks "Meeting URL", **When** the button is clicked, **Then** a placeholder interaction is shown (tooltip or disabled state indicating "Coming soon") since this feature is not yet implemented on the backend.
4. **Given** the user clicks "Record", **When** the button is clicked, **Then** a placeholder interaction is shown (tooltip or disabled state indicating "Coming soon") since this feature is not yet implemented on the backend.

---

### User Story 3 - Remove Meetings Nav Item and Meetings Page (Priority: P3)

As a user, I want a single place to see all my meetings (the home page) instead of having both a "Home" and a "Meetings" page that show overlapping content.

**Why this priority**: Consolidating reduces confusion. The current Meetings page duplicates the home page's meeting list with a different card style. Removing it simplifies navigation.

**Independent Test**: Can be tested by verifying the sidebar no longer shows a "Meetings" link and that navigating to `/meetings` redirects to `/`.

**Acceptance Scenarios**:

1. **Given** the user is logged in, **When** they view the sidebar, **Then** the "Meetings" navigation item is not present. The sidebar shows: Home, AI Chat, Integrations.
2. **Given** the user navigates directly to `/meetings`, **When** the page loads, **Then** they are redirected to the home page (`/`).
3. **Given** the user is on the home page, **When** they view the meeting list, **Then** it contains all meetings that were previously shown on both the home page and the meetings page.

---

### User Story 4 - Updated Right Panel Quick Actions (Priority: P4)

As a user, I want the right panel to reflect the new action bar so the "Upload a meeting" button is replaced or relabeled to stay consistent with the new "Import" terminology.

**Why this priority**: Consistency between the top action bar and the right panel avoids confusion.

**Independent Test**: Can be tested by verifying the right panel's primary button label matches the top bar's "Import" action and triggers the same upload modal.

**Acceptance Scenarios**:

1. **Given** the user views the right panel on desktop, **When** they see the Quick Actions section, **Then** the primary button reads "Import" (not "Upload a meeting") and opens the upload modal.

---

### Edge Cases

- What happens when the user has no meetings? The empty state should still display with the AI query bar and action buttons visible.
- What happens on mobile where the right panel is hidden? The top action bar buttons remain accessible in the main content area.
- What happens when a meeting has no summary and no status (legacy data)? The card falls back to showing only the title and file name.
- What happens when the summary preview is very long? It is truncated to 3 lines with a "Show more" text affordance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The home page MUST display meeting cards with: meeting title (as a heading), time of day + duration + speaker name (as subtitle line), and a truncated summary preview (up to 3 lines).
- **FR-002**: Each meeting card MUST show a user avatar or initials badge to the left of the content, matching the current pattern.
- **FR-003**: The top area of the main content (above the AI query bar or between the query bar and meeting feed) MUST show three action buttons: Meeting URL (camera icon), Import (text label), and Record (primary/red button with microphone icon).
- **FR-004**: The "Import" button MUST open the existing upload modal with no changes to the upload flow.
- **FR-005**: The "Meeting URL" and "Record" buttons MUST show a "Coming soon" indicator (tooltip or disabled visual state) since they have no backend functionality yet.
- **FR-006**: The sidebar navigation MUST NOT include a "Meetings" link.
- **FR-007**: Navigating to `/meetings` MUST redirect to the home page (`/`).
- **FR-008**: The right panel's primary quick action button MUST be relabeled to "Import" and trigger the upload modal.
- **FR-009**: Meeting cards with a "completed" status MUST show the summary preview. Cards in any other status MUST show only the status badge without an empty summary area.
- **FR-010**: Date group headers MUST be collapsible with a chevron indicator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the subject of a completed meeting from the home page list without clicking into it, at least 80% of the time (summary preview visible).
- **SC-002**: Users can initiate a meeting import (file upload) in 1 click from the home page action bar.
- **SC-003**: Navigation has 3 items instead of 4 — no duplicate meeting views exist.
- **SC-004**: All action buttons (Import, Meeting URL, Record) are visible without scrolling on standard viewport sizes (1280x720 and above).

## Assumptions

- The "Meeting URL" and "Record" features are placeholder buttons only — no backend implementation is needed for this feature. They will be wired up in future features.
- The existing upload modal and upload flow remain completely unchanged. Only the trigger button location and label change.
- The meeting detail page (`/meetings/[id]`) remains accessible — only the meetings list page is removed.
- The Otter.ai design is used as directional inspiration, not a pixel-perfect target. We match the layout pattern and information hierarchy, using Zabt's existing color scheme and design system.
- The "Show more" text on summary previews is a visual affordance — clicking the card navigates to the meeting detail page (existing behavior).
