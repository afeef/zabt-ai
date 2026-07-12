# Third-Party Licenses

zabt.ai is distributed under the **AGPL-3.0-only** license. It depends on third-party
open-source components, each under its own license. This document summarizes those licenses
and flags anything requiring attention.

**Bottom line:** all bundled dependencies are under AGPL-3.0-compatible licenses (MIT, BSD,
ISC, Apache-2.0, MPL-2.0, LGPL). No GPL-incompatible, SSPL, or proprietary code is linked or
redistributed. The only items needing user action are **model weights** and the **ffmpeg
binary**, which are NOT redistributed by this project (see Flags).

> Regenerate the JavaScript side with `npx license-checker --summary` (install
> `license-checker` first) and the Python side with `uvx pip-licenses` inside each service's
> environment. The summary below was produced during OSS prep.

## JavaScript / TypeScript (npm)

879 packages across the root workspace (`frontend-2`, `packages/*`) resolved to:

| License | Count | AGPL-compatible? |
|---------|-------|------------------|
| MIT | 752 | ✅ |
| Apache-2.0 | 38 | ✅ |
| ISC | 35 | ✅ |
| BSD-2-Clause | 16 | ✅ |
| BSD-3-Clause | 8 | ✅ |
| BlueOak-1.0.0 | 8 | ✅ |
| MPL-2.0 (incl. dual) | ~7 | ✅ (MPL-2.0 is explicitly GPL/AGPL-compatible) |
| FSL-1.1-MIT | 2 | ⚠️ build tool only — see Flags |
| LGPL-3.0-or-later | 1 | ✅ (dynamically linked native lib) |
| 0BSD / CC0 / Python-2.0 / CC-BY-4.0 | 4 | ✅ |
| "UNKNOWN" | 7 | first-party workspace packages (this repo) — not third-party |

The 7 "UNKNOWN" are this project's own workspace packages (`@zabt/shared`, `zabt-web`,
`posthog-js-*` local shims) and carry the repo's AGPL-3.0 license.

## Python (uv) — direct dependencies

All direct dependencies resolve to permissive or AGPL-compatible licenses:

| Area | Packages (license) |
|------|--------------------|
| Web/API | fastapi (MIT), uvicorn (BSD-3), starlette (BSD-3), pydantic / pydantic-settings (MIT), python-multipart (Apache-2.0) |
| Data/DB | sqlmodel (MIT), alembic (MIT), asyncpg (Apache-2.0), **psycopg2-binary (LGPL-3.0)** ✅, redis (MIT) |
| Tasks | celery (BSD-3) |
| Auth/crypto | python-jose (MIT), passlib (BSD), cryptography (Apache-2.0 / BSD) |
| Storage/media | boto3 (Apache-2.0), ffmpeg-python (Apache-2.0 wrapper — see Flags re: ffmpeg binary), weasyprint (BSD-3), pypdf (BSD-3), yt-dlp (Unlicense / public domain), Pillow (HPND, permissive), imagehash (BSD-2) |
| AI/LLM | openai (Apache-2.0), ollama (MIT), transformers (Apache-2.0), mistune (BSD-3) |
| Speech/GPU | **whisperx (BSD-family)**, **pyannote-audio (MIT code / gated weights)** — see Flags, librosa (ISC) |
| Observability | sentry-sdk (MIT), logfire (MIT), langfuse (MIT), posthog (MIT) |
| Integrations | resend (MIT), runpod (MIT), httpx (BSD-3), playwright (Apache-2.0), typer (MIT), rich (MIT), jsonschema (MIT) |

Transitive Python deps (torch, ctranslate2, faster-whisper, numpy, etc.) are BSD/MIT/Apache
family. Run `uvx pip-licenses` per service for the exhaustive transitive list.

## Flags (require attention)

### 1. 🔴 Model weights are NOT redistributed (user must accept gates)
- **pyannote speaker-diarization** models (`pyannote/speaker-diarization-3.1`, etc.) are
  **gated on Hugging Face** under pyannote's own terms. This repo ships only the *code* that
  loads them (MIT). **Weights are never included in this repository.** Each operator must
  accept the model's HF gate and provide their own `HF_TOKEN`. See README + `.env.example`.
- **Whisper / faster-whisper / MedASR** and any Qwen-VL vision model weights are likewise
  downloaded at runtime under their respective model licenses — not redistributed here.

### 2. 🟠 ffmpeg binary (runtime system dependency)
`ffmpeg-python` is a thin Apache-2.0 wrapper that shells out to the **ffmpeg binary**, which
is a separate program (LGPL or GPL depending on how it was built/packaged). zabt.ai invokes
ffmpeg as an external subprocess and does **not** link it or bundle it. Operators install
ffmpeg themselves (via their OS package manager or the container base image). No license
contamination results from subprocess invocation.

### 3. 🟡 FSL-1.1-MIT — `@sentry/cli` (build-time only)
`@sentry/cli` (used to upload source maps at build time) is under the Functional Source
License 1.1 (MIT future). It is **not** shipped in the running application and is **not**
linked into distributed code — it is a developer/CI build tool. It does not affect the
AGPL-3.0 licensing of zabt.ai. (FSL converts to MIT two years after each release.)

### 4. 🟢 LGPL dependencies (compatible)
`psycopg2-binary` (LGPL-3.0) and `@img/sharp-libvips` (LGPL-3.0-or-later) are LGPL. LGPL is
compatible with AGPL-3.0; both are used as dynamically-linked libraries / native bindings.
No action needed.

## Conclusion

No unresolved license incompatibilities. All redistributed code is AGPL-3.0-compatible. The
only non-redistributed components (ML model weights, the ffmpeg binary) are obtained by the
operator under their own terms, as documented in the README and `.env.example`.
