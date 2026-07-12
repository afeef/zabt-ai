# Data Model: Meeting Delete Feature

## Entities

### `Meeting` (Existing Backend SQLModel)

The existing `Meeting` model will be modified or queried to handle deletion.

**Attributes relevant to deletion:**
- `id` (Integer, Primary Key): Target identifier for deletion.
- `owner_id` (UUID): Foreign key to the User. *Required for authorization.*
- `status` (String): Must NOT be `processing` or `queued`. Can only delete if `completed` or `failed`.
- `file_path` (String): The physical storage path that needs to be passed to the storage engine for file deletion.

## Client-Side State

### `MeetingFeed` Component State

The frontend `MeetingFeed` component currently maintains:
- `meetings: Meeting[]`: The list of meetings rendered in the UI.

**State Transition**:
- On successful API deletion (200/204), the deleted meeting's `id` is filtered out of the `meetings` array to instantly update the UI without reloading.
