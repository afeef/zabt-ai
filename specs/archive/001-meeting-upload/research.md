# Research: Meeting Upload Progress

**Feature**: 001-meeting-upload  
**Date**: 2026-02-22

---

## Decision: Upload Progress Mechanism — Axios `onUploadProgress`

**Decision**: Using the existing Axios `apiClient` configured in `frontend-2/app/lib/api.ts`, we will implement the upload logic by passing an `onUploadProgress` callback in the request config. 

**Rationale**: Since the backend `POST /api/v1/meetings/upload` endpoint natively accepts standard `multipart/form-data`, Axios can accurately track byte transfer out of the browser. This requires zero backend changes and integrates cleanly with React state `(loaded / total * 100)`.

**Alternatives considered**:
- **Fetch API without Axios**: The native `fetch` API doesn't support upload progress out of the box (requires complex ReadableStream wiring). Axios is already in the project and built for this.
- **WebSocket/SSE**: Over-engineered for a simple HTTP file upload. WebSockets are better for tracking the *server-side* processing (transcription), but for the file upload itself, HTTP progress events are the standard.

---

## Decision: Cancellation Strategy — `AbortController`

**Decision**: We will attach an `AbortController.signal` to the Axios request. When the user clicks "Cancel" or "Cancel all", we will call `.abort()` on the corresponding controller(s).

**Rationale**: This immediately terminates the TCP connection, saving bandwidth and preventing the server from receiving partial garbage data. Fast, standard, and supported natively by Axios.

---

## Decision: Modal Placement and State Management

**Decision**: The state (is open, currently uploading files) and UI for the `UploadModal` will be hosted in the `<HomePage>` (`app/(dashboard)/page.tsx`), and the trigger function `openUploadModal()` will be passed down to the `<RightPanel>` and `<MeetingFeed>` components via props or a simple lightweight context if drilling becomes tedious.

**Rationale**: The user clarified the modal is opened from the dashboard (right panel or feed). By hosting the modal at the dashboard page level, the upload can continue seamlessly even if the user interacts with the query bar or switches tabs *within* the dashboard.

**Alternatives considered**:
- **Global Zustand/Redux Store**: Over-engineered for a single feature.
- **Next.js Parallel Intercepting Routes (`@modal`)**: Elegant but often complex to set up with client-side state like active file uploads, since navigation can sometimes unmount the slot. A standard React portal/dialog is safer for keeping the upload alive.

---

## Decision: Design System Compliance (Modals)

**Decision**: The modal will use existing shadcn/ui components (`Dialog`, `DialogTitle`, etc.) while strictly adhering to the project constitution and `system.md` patterns:
- Backdrop: `bg-stone-900/30`
- Surface: `bg-white`, `rounded-xl`, `border border-stone-200`
- No drop shadows anywhere.
- Action Buttons: Primary `bg-indigo-600 rounded-lg text-white` (or `Button` with variant), Secondary `text-indigo-600 hover:bg-stone-50 rounded-lg`.

**Rationale**: The user confirmed shadcn/ui is the standard component library, avoiding the need to install or build raw Radix primitives from scratch. Mandatory compliance with Zabt UI guidelines still applies.
