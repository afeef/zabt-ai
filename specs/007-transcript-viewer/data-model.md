# Data Model: Transcript Viewer

## Entities

### `TranscriptSegment`

The fundamental block of dialogue returned by the backend to power the viewer. 

**Attributes:**
- `id` (Integer): Unique segment ID.
- `meeting_id` (Integer): Foreign key to the parent Meeting.
- `speaker` (String): The diarized speaker label (e.g., `SPEAKER_00`).
- `start` (Float): Start time of the segment in seconds.
- `end` (Float): End time of the segment in seconds.
- `text` (String): The full text of the segment.
- `words` (Array of `TranscriptWord`): The word-level timestamps.

### `TranscriptWord`

Nested within `TranscriptSegment` to enable the high-performance 60fps highlighting.

**Attributes:**
- `word` (String): The specific token/word.
- `start` (Float): Precise start time in seconds.
- `end` (Float): Precise end time in seconds.

## Client-Side State (Frontend)

### `useTranscriptSync` (Zustand or Context)

To maintain 60FPS parsing without DOM bloat, the frontend must maintain decoupled state outside of the main virtualized React tree.

- `currentTime: number`: Updated constantly via `requestAnimationFrame` bound to the `<audio>/<video>` HTML5 ref.
- `activeWordIndex: number`: Computed by finding the word where `word.start <= currentTime && word.end >= currentTime`.
- `isPlaying: boolean`: State of the native media player.
