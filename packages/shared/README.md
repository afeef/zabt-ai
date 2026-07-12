# @zabt/shared

Shared TypeScript types, enums, and API client factory consumed by `frontend-2` (web) and `zabt-mobile` (React Native).

## Install

Workspace dependency — added automatically via npm workspaces.

## Build

```bash
npm run build       # one-time compile to dist/
npm run dev         # watch mode
```

Consumers import from the package name; the workspace symlink handles resolution:

```typescript
import { Meeting, MeetingStatus, createApiClient } from "@zabt/shared";
```

## Exports

- **Types** (`types.ts`) — `Meeting`, `MeetingList`, `User`, `TranscriptSegment`, `SummaryTemplate`, etc.
- **Enums** (`enums.ts`) — string literal unions + `const` arrays for iteration.
- **API client** (`api-client.ts`) — `createApiClient({ baseURL, getAuthToken, onUnauthorized })` returns a configured `axios` instance with auth + 401 interceptors. Each platform provides its own auth adapter.

## Adding new shared code

1. Add to the relevant file (`types.ts`, `enums.ts`, or create a new module).
2. Export it from `src/index.ts`.
3. Run `npm run build`.
4. Both consumers pick it up automatically via the symlink.
