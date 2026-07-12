# Feature Specification: Summary Templates

**Feature Branch**: `001-summary-templates`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "As a user, i want to create and use markdown templates that can be used with the summarization prompt to instruct the LLM to output a specific type of response. For example, retrospective, minutes of meetnigs, actions items etc"

## Clarifications

### Session 2026-03-04

- Q: How does template selection work at meeting upload time, and is there a system/user-level default? → A: The system has a default template (built-in). When a meeting is uploaded, summarization automatically runs using the current default template for that user. Users can set their own default from the Templates page, overriding the system default. Users can also change the template in the summary tab menu at any time, which immediately triggers a new summarization run using the newly selected template.
- Q: After selecting a different template in the summary tab, does re-summarization start immediately or require user confirmation? → A: Confirmation first — selecting a template from the menu shows a "Re-summarize with [Template]" button or prompt; the user must confirm before re-summarization begins.
- Q: When a user sets a new personal default on the Templates page, does it retroactively re-summarize existing meetings or apply only to future uploads? → A: Future uploads only — existing summaries are untouched when the default changes.
- Q: When a user changes the template in the summary tab and re-summarizes, does that also update their personal default for future uploads? → A: One-off — the template change applies to that meeting only; the personal default remains unchanged.
- Q: On the Templates page, can users preview the markdown body of a template before selecting or setting it as default? → A: Yes — users can expand/view the markdown body of any template (built-in or custom) before selecting or setting it as default.
- Q: In the summary tab template picker, are templates shown with names only or with inline previews? → A: Names only — all built-in and custom templates listed by name in the dropdown; no inline preview in the summary tab menu.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto-summarize on Upload Using Default Template (Priority: P1)

When a user uploads a meeting recording, the system automatically runs summarization using the user's active default template (which is the system default until the user overrides it). The user receives a structured summary without any manual template selection step.

**Why this priority**: Zero-friction summarization on upload is the primary value proposition. Every user benefits from this immediately, even before they know templates exist.

**Independent Test**: Can be fully tested by uploading a meeting and verifying that the resulting summary matches the structure of the active default template, without the user having to manually select anything.

**Acceptance Scenarios**:

1. **Given** a user has not set a personal default template, **When** they upload a meeting, **Then** the system automatically summarizes using the system default template.
2. **Given** a user has set a personal default template (e.g., "Action Items"), **When** they upload a meeting, **Then** the system automatically summarizes using their chosen default template.
3. **Given** summarization completes on upload, **When** the user opens the summary tab, **Then** they see the generated summary and the name of the template used to produce it.

---

### User Story 2 - Change Template in Summary Tab (Triggers New Summary) (Priority: P2)

A user views an existing meeting summary and wants a different format. They pick a different template from the summary tab menu, and a new summary is immediately generated using the selected template, replacing the previous one.

**Why this priority**: Changing the template is the core interactive feature. It closes the loop on the upload-time automation and lets users explore different views of the same meeting.

**Independent Test**: Can be fully tested by opening any completed meeting's summary tab, selecting a different template from the menu, and verifying a new summary is generated in the new template's structure.

**Acceptance Scenarios**:

1. **Given** a meeting has an existing summary, **When** the user selects a different template from the summary tab menu, **Then** a confirmation prompt (or "Re-summarize with [Template]" button) appears; re-summarization only begins after the user confirms, and the new summary replaces the old one upon completion.
2. **Given** re-summarization is in progress after a template change, **When** the user navigates away and returns, **Then** the processing state is shown and the new summary appears when complete.
3. **Given** re-summarization fails, **When** the user returns to the summary tab, **Then** the previous summary is restored and an error message is displayed.

---

### User Story 3 - Set Personal Default Template (Priority: P3)

A user visits the Templates page and marks one of the available templates (built-in or custom) as their personal default. All meetings uploaded after this change will automatically be summarized using this template. Existing meeting summaries are not affected.

**Why this priority**: Allows users to set-and-forget their preferred format rather than repeatedly changing it in the summary tab.

**Independent Test**: Can be fully tested by setting a personal default on the Templates page, then uploading a new meeting and verifying its summary matches the newly set default template.

**Acceptance Scenarios**:

1. **Given** the user is on the Templates page, **When** they designate a template as default, **Then** it is marked as the active default and replaces any previous default selection.
2. **Given** the user has set a personal default, **When** they upload a new meeting, **Then** the system uses the personal default template for auto-summarization.
3. **Given** the user's personal default template is deleted, **When** they upload a new meeting, **Then** the system falls back to the system default template.

---

### User Story 4 - Create a Custom Template (Priority: P4)

A user authors their own template using markdown, giving it a name and defining the sections and instructions the LLM should follow. The template is saved to their account and available as a selectable option in the template picker and as a default candidate.

**Why this priority**: Custom templates serve power users; built-in templates satisfy most users out of the box.

**Independent Test**: Can be tested by creating a custom template on the Templates page, then selecting it on a meeting and verifying the summary structure matches it.

**Acceptance Scenarios**:

1. **Given** the user is on the Templates page, **When** they enter a template name and markdown body and save, **Then** the template appears in the template picker and the default selector.
2. **Given** a custom template is selected for a meeting, **When** summarization runs, **Then** the output follows the structure defined in the user's custom markdown template.
3. **Given** the user edits a custom template, **When** they re-summarize a meeting using it, **Then** the updated template structure is applied.
4. **Given** the user deletes a custom template, **When** they view the template picker, **Then** the deleted template no longer appears.

---

### User Story 5 - Manage Templates (Priority: P5)

A user can view all available templates (built-in and custom) in one place, create/edit/delete custom templates, and designate any template as their personal default.

**Why this priority**: Management is required for long-term usability but is secondary to core creation and selection.

**Independent Test**: Testable by navigating to the Templates page and performing create, edit, delete, and set-default actions, verifying each is reflected in the picker and default behavior.

**Acceptance Scenarios**:

1. **Given** the user is on the Templates page, **When** they view it, **Then** they see all built-in templates and their own custom templates, with the active default clearly indicated.
2. **Given** the user edits a custom template's name or body, **When** they save, **Then** the updated details appear in the picker and management list.

---

### Edge Cases

- What happens when the default template is deleted (custom template was set as default)? The system falls back to the system default template for future uploads.
- What happens when the LLM receives a template that is ambiguous or very short? The system proceeds; output quality is LLM-dependent with no additional validation.
- What happens if re-summarization fails partway through? The previous summary is preserved and the user is shown an error.
- How does the system handle very long custom templates that may exceed prompt limits? A character limit is enforced at save time with a clear user-facing message.
- What happens if a meeting is uploaded while the user has no active default (e.g., system default was somehow unset)? The system falls back to a hardcoded general-purpose summary format.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a library of at least 3 built-in summary templates (e.g., General Summary, Meeting Minutes, Action Items, Retrospective) available to all users.
- **FR-002**: System MUST designate one built-in template as the out-of-box system default template, used automatically when no user default has been set.
- **FR-003**: System MUST automatically run summarization on meeting upload using the user's active default template (personal default if set, otherwise the system default).
- **FR-004**: System MUST pass the active template's markdown content as part of the summarization prompt sent to the LLM.
- **FR-005**: System MUST allow users to change the template from the summary tab menu, displaying all available templates by name only (no inline preview); after selection, the system MUST display a confirmation step (e.g., "Re-summarize with [Template]" button) before triggering a new summarization run. This is a one-off change for that meeting only and does not update the user's personal default template.
- **FR-006**: System MUST allow users to designate any available template (built-in or custom) as their personal default from the Templates page; this change applies only to meetings uploaded after the change and does not affect existing summaries.
- **FR-014**: System MUST allow users to preview the full markdown body of any template (built-in or custom) on the Templates page before selecting or setting it as default.
- **FR-007**: System MUST fall back to the system default template when a user's personal default template is deleted or unavailable.
- **FR-008**: System MUST allow authenticated users to create custom markdown templates with a name and body.
- **FR-009**: System MUST persist custom templates to the user's account so they are available across sessions.
- **FR-010**: System MUST allow users to edit and delete their own custom templates.
- **FR-011**: System MUST enforce a maximum length on custom template bodies to prevent excessive prompt usage, with a clear error message when exceeded.
- **FR-012**: System MUST display which template was used to generate the current summary on the summary tab.
- **FR-013**: System MUST preserve the existing summary if re-summarization fails, and display an error state to the user.

### Key Entities

- **SummaryTemplate**: Represents a template used to guide LLM summarization. Attributes: name, markdown body, type (built-in vs. custom), owner (user reference for custom templates), is_system_default (boolean, for built-in only), created/updated timestamps.
- **UserTemplatePreference**: Represents a user's chosen personal default template. Attributes: user reference, template reference, updated timestamp.
- **Meeting (extended)**: Gains a reference to the template used for its most recent summarization run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every meeting upload automatically produces a summary using the active default template, with no manual template selection required by the user.
- **SC-002**: 100% of built-in templates produce structurally distinct summary outputs that match the template's intended format when tested with representative meeting transcripts.
- **SC-003**: Users can change the template in the summary tab and receive a new summary without navigating away from the meeting.
- **SC-004**: Users can set a personal default template and verify it applies to the next uploaded meeting, in under 1 minute of setup.
- **SC-005**: Users can create and save a custom template in under 2 minutes.
- **SC-006**: Custom templates and personal default preferences are retrievable across sessions without data loss.

## Assumptions

- Built-in templates are defined and maintained by the development team; they are not user-editable.
- The "General Summary" (or equivalent) built-in template serves as the out-of-box system default.
- The LLM used for summarization accepts an instruction-level prompt where the template's markdown content is injected alongside the transcript.
- Users must be authenticated to create/save custom templates and to set a personal default; built-in templates are available to all tiers.
- The maximum custom template body length is 4,000 characters as a reasonable default balancing prompt context and usability.
- Changing the template in the summary tab requires a confirmation step before re-summarization begins; the existing summary remains visible and intact until the new one completes.
