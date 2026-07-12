# Research: Enterprise AI Meeting Assistant

**Status**: Phase 0 Complete
**Feature**: `001-ai-meeting-assistant`

## Technology Decisions

### Transcription Engine
- **Decision**: OpenAI Whisper (Local/Server-side).
- **Rationale**: User Requirement ("OpenAI compatible", "no downloading models to user machine"). Whisper provides state-of-the-art accuracy and can be run on the backend server, keeping data private and avoiding client-side resource drain.
- **Alternatives**: Google Speech-to-Text (Cloud-based, privacy concerns), Mozilla DeepSpeech (Lower accuracy).

### LLM Interface
- **Decision**: OpenAI-compatible API via `pydantic-ai`.
- **Rationale**: Allows swapping backend LLMs (Ollama, vLLM, or proprietary OpenAI/Azure) without code changes. `pydantic-ai` provides structured output validation for Action Items/Minutes.
- **Alternatives**: LangChain (Complexity overhead), Raw OpenAI SDK (Less structured validation).

### Real-time Streaming
- **Decision**: WebSocket (FastAPI) + MediaStream Recording API (Frontend).
- **Rationale**: Low latency requirement (<2s). WebSockets allow bidirectional streaming of audio chunks and transcript updates.
- **Why not Supabase Realtime?**: Supabase is excellent for database synchronization and lightweight messaging, but handling continuous binary audio streams for server-side processing (Whisper) requires a direct, low-latency channel to the inference engine. WebSockets provide this direct pipe without the overhead of database round-trips for ephemeral audio data.
- **Alternatives**: HTTP Polling (High latency), WebRTC (Overkill for one-way audio capability).

### Identity & Access Management (IAM)
- **Decision**: Logto (Open Source / Self-Hosted).
- **Rationale**: User Request + "Enterprise Security" requirement. Logto provides OIDC-compliant authentication, RBAC, and Audit Logs out-of-the-box, saving significant development time compared to rolling custom auth. It is privacy-friendly (self-hostable) and has SDKs for Next.js and Python.
- **Why Logto over Authentik?**:
    - **Target Audience**: Logto is designed for **Customer Identity (CIAM)**, meaning it offers a highly polished, conversion-optimized login experience for end-users out of the box. Authentik is fantastic but leans heavily towards **Workforce Identity** and internal infrastructure (SSO for employees, homelabs), with a more utilitarian UI.
    - **Developer Experience**: Logto's SDKs are more focused on modern web stacks (Next.js/React), whereas Authentik is often configured via complex flows and stages.
    - **UI Polish**: For a commercial SaaS app, Logto's default theme is "production-ready" aesthetic. Authentik would require significant customization to look like a consumer product.
- **Alternatives**: Keycloak (Too heavy/complex), Auth0 (Not open source/privacy-first self-hosted usually implies enterprise tier), Custom JWT (Security risks, maintenance burden).

### Task Queue
- **Decision**: Celery + Redis.
- **Rationale**: Transcribing large uploaded files is blocking. Celery allows offloading this to worker nodes.
- **Alternatives**: ARQ (Simpler but less ecosystem support), RQ (Redis only, Python specific).

## Implementation Strategy

1. **Audio Capture**: Browsers record audio chunks (e.g., every 1s) and send via WebSocket.
2. **Buffering**: Backend buffers chunks until a minimum duration (e.g., 5s) or silence is detected, then processes with Whisper.
3. **Drafting**: Use `Faster-Whisper` or `WhisperCPP` bindings for lower latency inference on CPU/GPU.
4. **Finalization**: Post-meeting, run a full pass for higher accuracy and LLM summarization.
