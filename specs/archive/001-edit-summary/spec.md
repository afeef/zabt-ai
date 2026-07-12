# Feature Specification: Edit Summary Markdown In-App

**Feature Branch**: `001-edit-summary`
**Created**: 2026-03-09
**Status**: Draft
**Input**: User description: "Users should be able to edit the AI-generated meeting summary directly in the app."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Edit and Save Summary (Priority: P1)

A user opens a completed meeting and notices the AI-generated summary contains an error or is missing context. They click an edit button on the summary section, which activates a WYSIWYG markdown editor in place. The editor shows the content as rendered markdown — what you see is what you get — so the user can make both formatting changes (headings, bold, lists) and content changes (fixing errors, adding context) without needing to know raw markdown syntax. They click "Save" to persist the changes, and the editor deactivates, returning to the normal read-only rendered view.

**Why this priority**: This is the core value proposition. Without the ability to edit and save, the feature delivers nothing.

**Independent Test**: Can be fully tested by navigating to any completed meeting with a summary, clicking edit, making changes in the WYSIWYG editor, saving, and confirming the changes persist after a page refresh.

**Acceptance Scenarios**:

1. **Given** a completed meeting with a summary, **When** the user clicks the edit button, **Then** the summary section switches to a WYSIWYG markdown editor showing the content as formatted text (not raw markdown).
2. **Given** the editor is active, **When** the user applies formatting (bold, heading, list) using toolbar buttons or keyboard shortcuts, **Then** the changes are immediately visible in the editor as rendered output.
3. **Given** the editor is active, **When** the user modifies content and clicks "Save", **Then** the changes are persisted to the server, the editor deactivates, and the updated summary is displayed in read-only view.
4. **Given** the editor is active, **When** the user clicks "Cancel", **Then** the editor discards all changes and returns to the read-only view with the original text.
5. **Given** the user has saved an edited summary, **When** they refresh the page, **Then** the edited summary is displayed (changes are persisted to the server).

---

### User Story 2 - Track Edit History (Priority: P2)

After editing a summary, the system retains the original AI-generated version so users can compare or revert. A visual indicator shows that the summary has been manually edited.

**Why this priority**: Provides confidence that edits are non-destructive. Users can always get back to the original AI output. Lower priority because it enhances trust but is not required for basic editing.

**Independent Test**: Can be tested by editing a summary, then checking that the original AI version is still accessible and that an "edited" indicator is visible.

**Acceptance Scenarios**:

1. **Given** a meeting with an unedited summary, **When** the user views it, **Then** no edit indicator is shown.
2. **Given** a user has saved edits to a summary, **When** they view the meeting, **Then** a visual indicator (e.g., "Edited" badge) shows the summary has been modified.
3. **Given** a user has edited a summary, **When** they choose to view the original, **Then** the original AI-generated summary is displayed.
4. **Given** a user is viewing the original summary, **When** they choose to restore it, **Then** the current summary is replaced with the original AI-generated version.

---

### Edge Cases

- What happens when the user edits while a re-summarization is in progress? The edit button should be disabled while the meeting is in a processing state.
- What happens if the user's session expires mid-edit? Unsaved changes are lost; the system should warn before navigating away with unsaved edits.
- What happens if the summary is empty (e.g., transcription produced no text)? The edit button should still be available so users can manually write a summary.
- What happens if two users edit the same summary concurrently? Last-write-wins is acceptable for the current single-user model; no conflict resolution is needed.
- What happens when the user saves with no changes? The save should succeed silently without creating unnecessary update records.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a toggle to switch the summary section between read-only (rendered) mode and WYSIWYG edit mode.
- **FR-002**: The WYSIWYG editor MUST display content as formatted text (what you see is what you get), not raw markdown syntax.
- **FR-003**: The editor MUST provide formatting controls for headings, bold, italic, lists (ordered and unordered), and links — via toolbar buttons and/or keyboard shortcuts.
- **FR-004**: System MUST pre-fill the editor with the current summary content when entering edit mode.
- **FR-005**: System MUST persist summary edits to the server when the user saves. The saved content MUST be stored as markdown.
- **FR-006**: System MUST allow the user to cancel editing and discard unsaved changes.
- **FR-007**: System MUST disable the edit button while the meeting is in a processing state (pending_upload, queued, or processing).
- **FR-008**: System MUST store the original AI-generated summary separately so it is not overwritten by user edits (P2).
- **FR-009**: System MUST display a visual indicator when a summary has been manually edited (P2).
- **FR-010**: System MUST allow users to view and restore the original AI-generated summary (P2).
- **FR-011**: System MUST warn the user before navigating away from the page with unsaved edits (browser-level beforeunload).
- **FR-012**: System MUST allow editing even when the summary is empty, enabling users to write a summary manually.

### Key Entities

- **Meeting**: Existing entity — extended with an original summary field and an edited flag to track whether the user has modified the AI-generated summary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can switch to edit mode, modify the summary, and save in under 10 seconds (excluding typing time).
- **SC-002**: Saved edits persist across page refreshes and browser sessions with 100% reliability.
- **SC-003**: The editor renders correctly on screens 768px wide and above.
- **SC-004**: Users can apply markdown formatting (headings, bold, lists) without knowing markdown syntax.
- **SC-005**: 100% of edited summaries retain the original AI-generated version for comparison or restoration (P2 complete).

## Assumptions

- The app is single-user per meeting (no collaborative editing or conflict resolution needed).
- The existing meeting detail page layout has sufficient space for an inline editor.
- Markdown rendering already exists in the app and does not need to be changed for the read-only view.
- The save action is explicit (button click), not auto-save, to avoid accidental overwrites.
- Only the meeting owner can edit the summary (existing auth model applies).
- The WYSIWYG editor outputs standard markdown (not HTML) to maintain compatibility with existing markdown rendering and PDF export.

## Out of Scope

- Real-time collaborative editing.
- Version history beyond original vs. current (no full audit trail of every edit).
- Editing the transcript text — only the summary is editable.
- Mobile-optimized editing experience (functional but not optimized for small screens).
- Image embedding or file attachments in the summary.

## Clarifications

### Session 2026-03-09

- Q: Should the editor be a raw markdown text editor or a WYSIWYG editor? → A: WYSIWYG markdown editor — what you see is what you get. Users can change both formatting and content visually without knowing markdown syntax.
