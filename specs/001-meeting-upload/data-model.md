# Data Model: Meeting Upload Progress

**Feature**: 001-meeting-upload  
**Date**: 2026-02-22

---

## Entities

> **Note**: This feature relies primarily on adding UI and client-side state. The backend `Meeting` entity and the `/upload` API endpoint already exist. No new database models are introduced.

### Meeting (Existing)

Used implicitly as the response type from the successful upload.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Primary key of the created meeting |
| `title` | `str` | Defaulted to "Untitled Meeting" or filename |
| `file_path` | `str` | The storage location of the uploaded file |
| `status` | `str` | `"queued"`, `"processing"`, `"completed"`, `"failed"` |

## Client-Side UI State

The core of this feature is managing the React state for active uploads within the `UploadModal` component.

### `UploadItem` State Object

Represents a single file currently in the upload queue or actively transferring.

| Property | Type | Purpose |
|----------|------|---------|
| `id` | `string` | Unique local ID (UUID or timestamp + filename) for the list |
| `file` | `File` | The actual browser File object being read |
| `progress` | `number` | `0` to `100` percentage |
| `loadedBytes` | `number` | Bytes transferred so far (for display) |
| `totalBytes` | `number` | Total file size (for display) |
| `status` | `"uploading" \| "success" \| "error" \| "cancelled"` | Drives the UI visual feedback |
| `abortController` | `AbortController` | Enables cancelling the active Axios request |

### `UploadModal` Container State

| Property | Type | Purpose |
|----------|------|---------|
| `isOpen` | `boolean` | Controls visibility of the modal dialog |
| `uploads` | `UploadItem[]` | Array of all current or recently finished uploads in the session |
| `importsLeft` | `number` | Mocked value (e.g., 3) per clarification |
| `totalImports` | `number` | Mocked value (e.g., 3) per clarification |
