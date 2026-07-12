# Feature Specification: Home Page Redesign

**Feature Branch**: `005-home-redesign`  
**Created**: 2026-02-22  
**Status**: Draft  
**Input**: User description: "The landing page or the home page after logging in is very outdated. I have attached a modern landing page screenshot that we need to use to design the application layout and reuse for all screens after logging in. Help me build this design using our existing design system."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Navigating the Dashboard After Login (Priority: P1)

A logged-in user lands on the home/dashboard page and sees a modern three-column layout: a left sidebar for navigation and profile info, a wide central area with a personalized greeting and AI query bar, and a right panel for contextual quick-actions. The user can navigate to any section of the app from the sidebar without leaving this shell.

**Why this priority**: This is the foundation of the entire authenticated experience. Every other screen lives inside this layout shell. Delivering a working shell immediately establishes the design language for all subsequent pages.

**Independent Test**: Can be fully tested by logging in and verifying the three-panel layout, the sidebar navigation links, and the personalized greeting all render correctly without any further screens being implemented.

**Acceptance Scenarios**:

1. **Given** a user is logged in, **When** they navigate to `/`, **Then** they see a left sidebar with the Zabt logo, navigation links (Home, AI Chat, Meetings, Integrations), and their avatar/name at the top; a central content area with a greeting ("Good morning, [Name]") and an AI query input bar; and a right panel with quick-action buttons.
2. **Given** a user is on any authenticated sub-page, **When** they look at the left sidebar, **Then** the active/current route link is visually highlighted and the layout shell remains consistent.
3. **Given** a first-time visitor or unauthenticated user, **When** they navigate to `/`, **Then** they are redirected to the login page (no layout shell is shown).

---

### User Story 2 - AI Query Bar on Home (Priority: P2)

The user types a question or a command into the AI query bar in the central area and submits it. The system acknowledges the input (e.g., routes to AI Chat with the query pre-filled, or shows a response inline).

**Why this priority**: The AI query bar is the primary value driver of the product on the home screen and should be functioning even before deeper AI Chat capabilities are fully built.

**Independent Test**: Can be tested by typing into the query bar and pressing Enter or clicking send; the query is either submitted to the AI Chat page or handled inline. This test is independent of the sidebar or right panel.

**Acceptance Scenarios**:

1. **Given** the user is on the home dashboard, **When** they type a question and press Enter or the send button, **Then** they are routed to the AI Chat screen with the query pre-populated.
2. **Given** the query bar is empty, **When** the user attempts to submit, **Then** no navigation or API call occurs and the bar shows a subtle placeholder hint.

---

### User Story 3 - Meeting Activity Feed (Priority: P3)

The central area below the AI query bar shows the user's recent meeting activity grouped by date. Each entry shows the meeting title, source/uploader, and a summary preview. The user can click an entry to open the full meeting detail.

**Why this priority**: Gives returning users immediate value by surfacing their most recent meetings, making the home page functionally useful rather than a static greeting.

**Independent Test**: Can be tested by uploading at least one meeting and then visiting the home page; the meeting should appear as a card in the activity feed, and clicking it should navigate to the meeting detail page.

**Acceptance Scenarios**:

1. **Given** the user has at least one processed meeting, **When** they visit the home dashboard, **Then** a chronological activity feed is displayed with date group headers (e.g., "Today, Feb 22") and meeting cards.
2. **Given** the user has no meetings, **When** they visit the home dashboard, **Then** an empty-state message is shown (e.g., "You have no meetings yet — upload one to get started") with a CTA to upload.
3. **Given** a meeting card is displayed, **When** the user clicks it, **Then** they are navigated to the meeting detail page.

---

### Edge Cases

- What happens when the user's name is very long? The greeting and sidebar avatar/name should truncate gracefully.
- What happens when there are no meeting records and the right panel has no upcoming events? Both areas must show tasteful empty states rather than blank space.
- What happens on a narrow viewport (tablet)? The right panel should collapse; on mobile the sidebar should become an off-canvas drawer.
- What happens if the network is slow and data takes time to load? Skeleton loaders should be shown for the feed and right panel while data is fetched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The authenticated home page MUST display a persistent three-column layout shell (left sidebar, main content, right panel) across all authenticated routes.
- **FR-002**: The left sidebar MUST display the Zabt application logo at the top, a list of primary navigation links (Home, AI Chat, Meetings, Integrations) with icons, section groupings (Channels, Direct Messages, Folders), and the signed-in user's avatar and display name at the top.
- **FR-003**: The main content area MUST display a personalized greeting keyed to the current time of day ("Good morning/afternoon/evening, [User First Name]").
- **FR-004**: The main content area MUST display an AI query input bar with placeholder text, an "Advanced" mode toggle, and a submit button.
- **FR-005**: The main content area MUST display a chronological meeting activity feed grouped by date, with meeting-card entries showing the meeting title and a brief summary previewing the first 2–3 sentences.
- **FR-006**: The right panel MUST display quick-action buttons relevant to the user's context (e.g., "Upload a meeting", "Connect a calendar").
- **FR-007**: The active navigation link in the left sidebar MUST be visually distinguished from inactive links.
- **FR-008**: Users MUST be able to navigate between sections by clicking sidebar links without the layout shell remounting.
- **FR-009**: The layout MUST reuse the existing design system tokens (stone/indigo color palette, Geist font, border-radius, spacing scale).
- **FR-010**: The layout shell MUST NOT be rendered for unauthenticated users; unauthenticated access to `/` MUST redirect to `/login`.

### Key Entities

- **Layout Shell**: Persistent authenticated wrapper component containing the sidebar, main slot, and right panel slot.
- **Sidebar**: Navigation component with logo, user profile, nav links, and collapsible sections.
- **Meeting Card**: A content card representing a single meeting with title, date, uploader, and summary preview.
- **AI Query Bar**: An input component with submit capability and advanced mode toggle.
- **Right Panel**: A contextual sidebar for quick-actions and secondary information widgets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate between any two authenticated sections in under 1 second without seeing a full page reload (shell-preserved navigation).
- **SC-002**: The home page renders the personalized greeting, meeting feed, and AI query bar correctly on first load, with no blank areas visible after data resolves.
- **SC-003**: The layout is visually consistent across all authenticated routes — 100% of post-login pages use the shared layout shell.
- **SC-004**: On viewports below 768 px wide, all critical actions (navigation, AI query bar, upload CTA) remain accessible without horizontal scrolling.
- **SC-005**: Loading skeleton states are shown for dynamic content within 100 ms of navigation, so users always see immediate visual feedback.

## Assumptions

- The `frontend-2` directory is the active Next.js frontend. All changes are scoped to this codebase.
- The existing design system tokens (indigo-600 primary, stone-* neutrals, Geist Sans/Mono, rounded-lg radius) are preserved and extended; no new third-party UI library is introduced.
- User authentication state is already handled via a token stored in local storage (`getToken()` from `lib/api`). The spec does not change the auth flow.
- "AI Chat" is a future navigable route; for now, the AI query bar will route the user to `/meetings` or hold state until the AI Chat screen is implemented.
- "Integrations", "Channels", "Direct Messages", and "Folders" sidebar sections are navigation placeholders; they may link to unimplemented routes in the initial delivery.
- The right panel content (calendar, quick-action buttons) will be partially static/mocked in the first iteration and populated with live data in a later sprint.
