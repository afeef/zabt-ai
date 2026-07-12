# Research: Logout Button

**Feature**: 015-logout-button | **Date**: 2026-03-01

## Research Tasks

### R1: Logout mechanism in existing codebase

**Decision**: Use the existing `clearToken()` function from `frontend-2/app/lib/api.ts` (line 83-86), which wraps `supabase.auth.signOut()`. After sign-out, the `onAuthStateChange` listener in `(dashboard)/layout.tsx` automatically detects session loss and calls `router.replace("/login")`.

**Rationale**: The logout infrastructure is already fully implemented. `clearToken()` calls `supabase.auth.signOut()` which clears all session cookies and tokens. The dashboard layout's auth state listener handles the redirect. No new auth logic is needed.

**Alternatives considered**:
- Direct `supabase.auth.signOut()` call in the component — rejected because `clearToken()` already exists as the canonical wrapper and keeps auth logic centralized in `api.ts`.
- Server-side sign-out via API route — rejected because Supabase session is client-side (cookies managed by `@supabase/ssr`); server-side endpoint adds unnecessary complexity.

### R2: UI pattern — profile dropdown menu (reference: Otter.ai screenshot)

**Decision**: Implement a profile dropdown menu that opens when the user clicks the profile section in the sidebar. The dropdown anchors below the profile area and includes menu items with icons. The "Logout" item is placed at the bottom, separated by a divider. This matches the Otter.ai reference screenshot's pattern.

**Rationale**: The reference screenshot shows a clean, familiar pattern:
1. Profile section is clickable (shows user name + email + chevron indicator)
2. Dropdown appears with grouped menu items
3. "Logout" is the last item, visually separated by a divider
4. Clicking outside the dropdown closes it

This pattern is widely recognized, discoverable, and leaves room for future menu items (Account Settings, Help Center, etc.) without sidebar clutter.

**Alternatives considered**:
- Standalone logout button at sidebar bottom — rejected because the reference screenshot shows a dropdown pattern, and a standalone button wastes vertical space in the already dense sidebar.
- Logout in a settings page only — rejected because it requires navigation to find; the spec requires logout to be accessible "under 5 seconds from any page."

### R3: Dropdown implementation approach

**Decision**: Build a lightweight custom dropdown using React state (`useState` for open/close) and a click-outside handler (`useEffect` with `mousedown` listener). No external library needed.

**Rationale**: The dropdown is simple (one trigger, one menu panel, click-outside-to-close). The codebase already uses this pattern implicitly (mobile sidebar uses backdrop click to close). Adding a headless UI library (Radix, Headless UI) for a single dropdown is over-engineering.

**Alternatives considered**:
- Radix UI Dropdown Menu — offers accessible dropdown with keyboard nav and focus management. Rejected because it adds a dependency for one component; can be adopted later if more dropdowns are needed.
- HTML `<details>/<summary>` — native but lacks click-outside behavior and has inconsistent styling across browsers.

### R4: Confirmation dialog pattern

**Decision**: Use a lightweight inline confirmation within the dropdown. When "Logout" is clicked, the item transforms into a "Confirm logout?" state with Confirm/Cancel buttons. This avoids a modal overlay for a low-stakes action.

**Rationale**: The Otter.ai reference doesn't show a confirmation dialog, but the spec (FR-005/P2) requires one. An inline confirmation within the dropdown is the lightest-weight approach — no modal component needed, no overlay, no portal. It keeps the user in context and is fast to dismiss.

**Alternatives considered**:
- Modal dialog overlay — rejected as over-engineering for a low-risk action (user can always log back in). Modals interrupt flow and feel heavy.
- Browser `window.confirm()` — rejected because it breaks the design language and can't be styled.

### R5: Design system compliance

**Decision**: The profile dropdown menu will use existing design tokens:
- Container: `bg-white border border-stone-200 rounded-lg` (standard card pattern, no shadow)
- Menu items: `px-3 py-2 text-sm text-stone-700 hover:bg-stone-100 rounded-lg` (matches nav link inactive style)
- Icons: `w-4 h-4 text-stone-400` (consistent with sidebar nav icons)
- Logout item: `text-red-600 hover:bg-red-50` (uses danger color from system.md)
- Divider: `border-t border-stone-100` (matches sidebar section dividers)

**Rationale**: All tokens come directly from `.interface-design/system.md`. The dropdown is essentially a floating card with nav-link-styled items. "Logout" uses the danger color (`red-600`) to signal destructiveness, consistent with the existing danger button variant.

### R6: Mobile behavior

**Decision**: On mobile, the dropdown works identically — it opens inside the off-canvas sidebar drawer. No special mobile handling needed since the sidebar already manages its own open/close state via `AppShell`.

**Rationale**: The sidebar on mobile is a full-height drawer with the same 220px width. The dropdown menu has plenty of room within this drawer. When the user taps logout and confirms, the sidebar closes automatically as part of the page redirect.

### R7: Error handling during logout

**Decision**: Wrap `clearToken()` in a try/catch. On error, still redirect to `/login` — a failed server-side sign-out shouldn't trap the user in the app. The `onAuthStateChange` listener provides a safety net regardless.

**Rationale**: The most common failure case is network error. Even if `supabase.auth.signOut()` fails to reach the Supabase server, the local session state is cleared. Redirecting to `/login` is always the correct outcome.
