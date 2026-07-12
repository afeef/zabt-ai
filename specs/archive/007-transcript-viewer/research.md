# Research & Technical Decisions: Transcript Viewer

## 1. High-Performance State Management for Word-Level Synchronization

**Decision**: Use React `useRef` for tracking the current playback time combined with a localized `requestAnimationFrame` loop (or a high-frequency `timeupdate` event listener) that updates a highly localized state context or zustand store. We will NOT store the `currentTime` in a global React state that wraps the entire list, as that would cause re-renders of the entire DOM tree 60 times a second.
**Rationale**: The primary requirement is that "word-level highlighting must sync precisely with the media player" without causing "excessive re-renders of the entire transcript list." By decoupling the fast-changing time state from the large transcript list rendering, we ensure 60fps performance. Individual word components can subscribe to a lightweight context or use a ref-checking mechanism to determine if they are the "active" word.
**Alternatives considered**: Pure React state passed down via props. Rejected as it forces the entire `TranscriptViewer` array to reconcile every millisecond.

## 2. Virtualized List for the Transcript Viewer

**Decision**: Use `react-virtuoso` or `@tanstack/react-virtual` to render the transcript feed.
**Rationale**: Transcripts for 60-minute meetings can contain thousands of DOM nodes. Rendering them all at once destroys browser memory and scroll performance. A virtualized list only renders the items currently visible in the viewport. It will be configured to automatically scroll to the active index when the media seeks or progresses.
**Alternatives considered**: Standard mapping of arrays. Rejected due to the risk of "DOM bloat" mentioned in the spec.

## 3. Media Player Architecture

**Decision**: Build a custom `StickyPlayer` component at the bottom of the screen wrapping the native HTML5 `<audio>` / `<video>` APIs. The progress bar will be a custom SVG or multi-colored `div` track that maps the speaker talk-time segments over the total duration.
**Rationale**: Native audio/video `controls` do not support multi-colored segmenting for speakers. By wrapping the native API, we can build the requested UI features (10s rewind, 1x speed toggle, speaker segmented progress line) while still utilizing the browser's optimized media engine.
**Alternatives considered**: Heavy lifting libraries like Video.js. Rejected in favor of native HTML5 APIs mapped to `shadcn/ui` aesthetic elements to keep the bundle size small.

## 4. UI/UX: 30-Minute Free Tier Paywall

**Decision**: Implement a conditional CSS blur (`blur-sm backdrop-blur-sm`) and an absolute positioned modal overlay inside the transcript container for free-tier users when the `currentTime` or transcript lines extend past 1800 seconds (30 minutes). Overflow will be set to `hidden` to prevent scrolling past the veil.
**Rationale**: Fulfills the requirement to prevent viewing the rest of the text and prompting for an upgrade.
**Alternatives considered**: Truncating the JSON payload directly on the backend. This would prevent seeking or playing the media entirely past 30 minutes, which is a safer approach security-wise, but requires backend changes. We will proceed with frontend UI masking as specified, but note it is bypassable via dev tools.
