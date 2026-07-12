# Research & Decisions: Meeting Delete Option

## 1. UI Integration (Three-Dot Menu)

**Decision**: Implement a native-styled Tailwind dropdown menu or utilize standard `<details>`/`<summary>` patterned dropdown to avoid introducing new heavy Radix/shadcn dependencies if they don't already exist for dropdowns.
**Rationale**: In the previous upload feature, we discovered the project uses `shadcn/ui` lightly but was missing the actual primitive installations (like `Dialog`). To maintain velocity and strictly adhere to `.interface-design/system.md`, building a simple accessible CSS-driven or React-state-driven dropdown is safer and perfectly aligns with the required utility classes (`bg-white border-stone-200 rounded-lg`).
**Alternatives considered**: Running `npx shadcn@latest add dropdown-menu`. Rejected as it installs Radix primitives over the network which caused issues previously.

## 2. API Endpoint Architecture

**Decision**: Introduce `DELETE /api/v1/meetings/{meeting_id}` in `backend/app/api/v1/endpoints/meetings.py`.
**Rationale**: Follows standard RESTful patterns. The endpoint must first fetch the meeting to verify ownership (Supabase JWT matching `meeting.user_id`), ensure it is not actively `processing` (FR-007), capture the `file_path`, delete the database record, and then delete the physical file from storage.
**Alternatives considered**: A generic `/bulk-delete` endpoint. Rejected as the requirement is for individual contextual deletion.

## 3. Storage Deletion Mechanism

**Decision**: Use `os.remove()` (or async `aiofiles.os.remove()`) if using local storage, or the corresponding Supabase Storage SDK method if files are stored in Supabase buckets.
**Rationale**: We must extract the actual storage adapter being used by the FastAPI backend to ensure the physical media is garbage collected (FR-005). Based on typical `zabt-ai` local deployments, it uses local volume mounts for audio files. We will inspect the backend before final implementation.

## 4. Frontend State Management

**Decision**: Optimistic UI update or seamless state filtering within `frontend-2/app/components/meeting-feed.tsx`.
**Rationale**: When the user clicks exactly one meeting's delete button, the `apiClient.delete()` function is called. On success (204 or 200), we filter that meeting out of the local `meetings` React state array (`setMeetings(prev => prev.filter(m => m.id !== deletedId))`) to instantly update the UI without reloading the page (FR-006).
