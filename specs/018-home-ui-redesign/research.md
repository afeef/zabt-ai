# Research: Home Page UI Redesign

**Feature**: 018-home-ui-redesign
**Date**: 2026-03-04

## Summary

This is a frontend-only UI redesign with no technical unknowns. All technologies are already in use in the project (Next.js 16, React 19, Tailwind CSS 4, lucide-react). No new dependencies or integrations required.

## Decisions

### 1. Card Layout Pattern

**Decision**: Use a content-rich card with title heading, metadata subtitle, and truncated summary preview.
**Rationale**: Matches the Otter.ai reference design and provides at-a-glance meeting context. The current card layout wastes vertical space by showing minimal information.
**Alternatives considered**: Compact list view (rejected — less scannable for meeting context), table view (rejected — doesn't match the reference design or existing design system).

### 2. Action Bar Placement

**Decision**: Place the action bar between the AI query bar and the meeting feed, aligned right.
**Rationale**: Matches Otter.ai's top-bar placement. Keeps actions visible without scrolling. The current "Upload a meeting" button is hidden in the right panel (desktop only) and not discoverable on mobile.
**Alternatives considered**: Floating action button (rejected — not in design system), sidebar action buttons (rejected — sidebar is for navigation, not actions).

### 3. Meetings Page Removal Strategy

**Decision**: Replace the meetings list page with a Next.js redirect to `/`. Keep the meeting detail page `/meetings/[id]` intact.
**Rationale**: The meetings list page duplicates the home page content. Redirecting preserves any bookmarks or shared links while consolidating the experience.
**Alternatives considered**: 404 page (rejected — breaks existing links), keeping as alias (rejected — maintains confusing duplicate views).

### 4. "Coming Soon" Pattern for Unimplemented Buttons

**Decision**: Use `title` attribute tooltip with "Coming soon" text + slightly muted visual style (reduced opacity or outlined) for Meeting URL and Record buttons.
**Rationale**: Simple, no extra dependencies, signals to users that functionality is planned. Avoids building a toast/notification system just for placeholder buttons.
**Alternatives considered**: Disabled buttons (rejected — less informative), modal popup (rejected — over-engineered for a placeholder).
