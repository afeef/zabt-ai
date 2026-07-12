# Feature Specification: Migrate to shadcn/ui Design System & Unified Summary Toolbar

**Feature Branch**: `001-shadcn-ui-migration`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Replace all custom UI components with shadcn/ui. Create unified summary toolbar. Use rose theme."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - shadcn/ui Foundation & Summary Toolbar (Priority: P1)

A user opens a completed meeting and navigates to the Summary tab. Between the tab bar and the summary content, they see a clean horizontal toolbar with: an Edit button (pencil icon), an Exports dropdown (Copy, Download .txt, Download PDF), and a Templates dropdown (built-in + custom templates with re-summarize confirmation). The toolbar replaces the old template dropdown that mixed template selection with export actions. All actions feel snappy, menus are keyboard-navigable, and the UI follows the rose theme with stone neutrals.

**Why this priority**: The summary toolbar is the primary new user-facing feature. Without the shadcn/ui foundation installed, nothing else can be built. Combining these ensures the first deliverable is both the infrastructure and a visible improvement.

**Independent Test**: Install the component library, build the summary toolbar, verify Edit/Export/Template actions all work on a completed meeting's Summary tab. Transcript tab retains its existing Download PDF button unchanged.

**Acceptance Scenarios**:

1. **Given** a completed meeting with a summary, **When** the user opens the Summary tab, **Then** a horizontal toolbar appears below the tabs with Edit, Exports dropdown, and Templates dropdown buttons.
2. **Given** the Summary toolbar is visible, **When** the user clicks Exports, **Then** a dropdown opens with "Copy summary", "Download as .txt", and "Download as PDF" options.
3. **Given** the Summary toolbar is visible, **When** the user clicks Templates, **Then** a dropdown opens showing built-in templates, custom templates (if any), and links to create/manage templates.
4. **Given** the user selects a different template, **When** the confirmation dialog appears and they confirm, **Then** the meeting re-summarizes and the toolbar shows a processing state.
5. **Given** the summary has been edited, **When** the user views the toolbar, **Then** an "Edited" badge appears along with "View Original" and "Restore Original" controls.
6. **Given** the toolbar, **When** the user navigates entirely with keyboard (Tab, Enter, Escape, Arrow keys), **Then** all dropdowns and buttons are fully accessible.
7. **Given** the Transcript tab, **When** a completed meeting has segments, **Then** the existing Download PDF button remains unchanged (no toolbar on Transcript tab).

---

### User Story 2 - Component Migration (Priority: P2)

A developer or user interacts with any part of the app — login page, dashboard, meeting list, upload modal, profile menu — and all interactive elements (buttons, inputs, modals, badges, dropdowns) are consistent components from the shared library. The custom Button, StatusBadge, SocialButton, and ProfileMenu components have been replaced. All existing functionality is preserved — no feature regressions.

**Why this priority**: Once the foundation is set (US1), migrating all remaining custom components ensures design consistency across the entire app. This is lower priority than the toolbar because it's incremental polish, not new functionality.

**Independent Test**: Navigate through every page (login, register, forgot-password, dashboard, meeting list, meeting detail, templates) and verify all interactive elements render correctly, respond to interactions, and maintain keyboard accessibility. Verify no visual regressions (no shadows, borders-only depth, stone palette).

**Acceptance Scenarios**:

1. **Given** the login page, **When** it renders, **Then** OAuth buttons and form inputs use the component library with consistent styling.
2. **Given** the meeting list, **When** meetings are displayed, **Then** status badges use the Badge component with appropriate color variants per status.
3. **Given** the sidebar profile area, **When** the user clicks their profile, **Then** a dropdown menu appears with account options and logout (with confirmation dialog).
4. **Given** the upload modal, **When** it opens, **Then** buttons and progress elements use the component library.
5. **Given** any page, **When** inspecting the rendered output, **Then** no shadow classes (`shadow`, `shadow-sm`, `shadow-lg`) appear — borders-only depth rule is maintained.

---

### User Story 3 - Design System Documentation Update (Priority: P3)

A developer opening the design system documentation finds updated guidance reflecting the component library as the standard. The documentation covers which components to use, how the rose theme maps to the existing stone/indigo palette, and the borders-only depth rule. Custom component documentation is removed since those components no longer exist.

**Why this priority**: Documentation supports long-term maintainability but delivers no direct user value. It should be done after all components are migrated.

**Independent Test**: Read the design system file and verify it accurately describes the current component library, color tokens, and usage patterns. Verify no references to deleted custom components remain.

**Acceptance Scenarios**:

1. **Given** the design system file, **When** a developer reads it, **Then** it documents the component library with rose theme configuration.
2. **Given** the design system file, **When** searching for custom component references (old Button variants, StatusBadge, SocialButton), **Then** none are found — only standard library equivalents are documented.

---

### Edge Cases

- What happens when the summary toolbar renders on a meeting that is still processing? The toolbar MUST be hidden or all actions disabled — only shown for completed meetings.
- What happens when template fetch fails while the Templates dropdown is open? A user-friendly error message appears inside the dropdown.
- What happens when the PDF export fails from the Exports dropdown? An error alert is shown to the user (existing behavior preserved).
- What happens on narrow mobile viewports? The toolbar MUST remain usable — dropdowns stack or overflow gracefully.
- What happens when a user has no custom templates? The "My Templates" section is hidden in the dropdown, only built-in templates show.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST use a shared accessible component library for all interactive UI elements (buttons, dropdowns, dialogs, inputs, badges, tabs).
- **FR-002**: The component library MUST use the rose theme with stone neutral colors for backgrounds, borders, and text hierarchy.
- **FR-003**: The Summary tab of a completed meeting MUST display a horizontal toolbar between the tab bar and content area containing: Edit button, Exports dropdown, and Templates dropdown.
- **FR-004**: The Exports dropdown MUST contain three options: "Copy summary" (copies markdown to clipboard), "Download as .txt" (downloads plain text file), and "Download as PDF" (calls server-side PDF export endpoint).
- **FR-005**: The Templates dropdown MUST display built-in templates and custom templates (if any) with the current template indicated, and MUST include links to create and manage templates.
- **FR-006**: Selecting a different template MUST trigger a confirmation dialog before re-summarizing.
- **FR-007**: When the summary has been edited, the toolbar MUST show an "Edited" badge and controls to "View Original" and "Restore Original".
- **FR-008**: The toolbar MUST only appear on the Summary tab for meetings with status "completed".
- **FR-009**: The Transcript tab MUST retain its existing "Download PDF" button without changes.
- **FR-010**: All custom UI components (Button, StatusBadge, SocialButton, ProfileMenu dropdown, modal/dialog patterns, input fields) MUST be replaced with component library equivalents.
- **FR-011**: The old custom component files MUST be removed after migration.
- **FR-012**: All existing PostHog analytics events MUST continue to fire with the same event names and properties after migration.
- **FR-013**: All components MUST follow the borders-only depth rule — no shadow classes anywhere.
- **FR-014**: All interactive components MUST be keyboard accessible (Tab navigation, Enter/Space activation, Escape to close, Arrow keys in menus).
- **FR-015**: The design system documentation MUST be updated to reflect the component library as the standard.
- **FR-016**: No backend changes — this feature is purely frontend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of interactive UI elements (buttons, dropdowns, dialogs, inputs, badges) use the component library — zero custom hand-built equivalents remain in the codebase.
- **SC-002**: All existing user workflows (login, upload meeting, view summary, edit summary, export PDF, manage templates, logout) complete successfully without regressions.
- **SC-003**: All toolbar actions (edit, copy, download txt, download PDF, change template) complete within 2 seconds of user interaction (excluding network time for PDF generation/re-summarization).
- **SC-004**: All dropdown menus and dialogs are fully operable using only keyboard — 100% of actions reachable without a mouse.
- **SC-005**: Zero shadow-related CSS classes exist in the rendered output across all pages.
- **SC-006**: Existing end-to-end tests pass without modification (or with only selector updates if element structure changed).
- **SC-007**: The frontend builds and deploys without errors after the migration.

## Assumptions

- The component library CLI supports the project's current setup (Next.js 16, Tailwind CSS 4, React 19). If not, manual installation of components is an acceptable alternative.
- The rose theme provides a suitable base that can be customized with the existing stone neutral palette — no custom theme from scratch is needed.
- ProgressSteps has no direct library equivalent — it will remain as a custom component but may use library primitives internally.
- The SocialButton component is OAuth-specific with branded provider icons — it will be rebuilt using the library Button as a base but retains custom icon SVGs.
- The Tiptap-based SummaryEditor is independent of this migration and does not need to be replaced (it's a rich text editor, not a generic UI component).
- Mobile responsiveness of the toolbar follows standard responsive patterns — no special mobile-specific design is required beyond what the components provide.

## Out of Scope

- Backend changes or new API endpoints
- Changing the Tiptap-based summary editor
- Redesigning page layouts (sidebar, app shell, right panel structure)
- Adding new features beyond the toolbar consolidation
- Dark mode support (can be added later via theming)
- Redesigning the transcript viewer or media player
