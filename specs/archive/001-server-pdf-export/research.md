# Research: Server-Side PDF Export

## Decision 1: PDF Generation Library

**Decision**: WeasyPrint (v68.1)
**Rationale**: HTML/CSS → PDF approach leverages familiar web styling, provides gold-standard multilingual support via Pango/HarfBuzz text stack, and handles Arabic/Urdu RTL + Devanagari natively. The primary reason for migrating from client-side pdfmake is multilingual rendering — WeasyPrint solves this by design.
**Alternatives considered**:
- **fpdf2**: Pure Python, zero system deps, fast — but requires programmatic layout (no CSS), and complex script support needs manual `uharfbuzz` setup. More work for equivalent output.
- **ReportLab**: Mature but Arabic/Devanagari bidi/shaping support is less reliable than Pango/HarfBuzz. Programmatic API, no HTML templates.
- **pdfkit/wkhtmltopdf**: Archived project (Jan 2023), dead, +200-400 MB Docker overhead.
- **Playwright PDF**: Full Chromium (+400-600 MB), overkill for 12 GB VPS.
- **borb**: AGPL license incompatible with SaaS.

## Decision 2: System Dependencies in Docker

**Decision**: Minimal runtime libs + Noto fonts
```
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libharfbuzz0b fonts-noto-core
```
**Rationale**: WeasyPrint v53+ dropped the Cairo dependency — only Pango/HarfBuzz runtime libs needed (~5-15 MB). `fonts-noto-core` covers 65+ Unicode scripts including Arabic, Urdu Nastaliq, Devanagari, and Latin (~42.5 MB). No need for `fonts-noto-cjk` (CJK adds 100+ MB).
**Total Docker image size impact**: ~50-60 MB additional.

## Decision 3: Markdown-to-HTML Library

**Decision**: `mistune` (v3.x)
**Rationale**: Fastest pure-Python markdown parser, zero dependencies, handles headings, bold, italic, lists, fenced code blocks, and tables out of the box. CommonMark compliant. Meeting summaries use standard markdown — no need for the stricter `markdown-it-py`.
**Alternatives considered**:
- **Python-Markdown**: ~60x slower than mistune, partial CommonMark support.
- **markdown-it-py**: ~10x slower, has external deps (mdurl), stricter CommonMark — unnecessary for this use case.

## Decision 4: FastAPI Response Pattern

**Decision**: `Response` with raw bytes, not `StreamingResponse`
**Rationale**: WeasyPrint's `write_pdf()` returns complete PDF bytes in memory — no streaming generation available. `StreamingResponse(io.BytesIO(...))` adds overhead without benefit. Use `Response(content=pdf_bytes, media_type="application/pdf")` with `Content-Disposition: attachment` header.

## Decision 5: RTL/Bidi Handling

**Decision**: Explicit `dir="rtl"` HTML attributes + CSS `direction: rtl; text-align: right`
**Rationale**: WeasyPrint's Unicode Bidi Algorithm is partially implemented. Simple block-level RTL works well, but complex mixed-direction inline text may not reorder perfectly. For our use case (meeting summaries and transcripts), block-level RTL is sufficient. Script detection determines when to apply RTL styling. Pango handles Arabic glyph shaping correctly — the limitations are in CSS-level bidi layout, not text rendering.

## Decision 6: Script Detection Strategy

**Decision**: Server-side Unicode range detection, same approach as the client-side `detectFont()` but applied to HTML `dir` attributes instead of font selection.
**Rationale**: Check if text contains Arabic/Urdu range characters (U+0600–U+06FF, U+0750–U+077F, U+FB50–U+FDFF, U+FE70–U+FEFF) to set `dir="rtl"`. Devanagari and Latin are LTR by default. Pango + Noto fonts handle font selection automatically — no manual font-per-script needed on the server.

## Decision 7: Frontend Integration Pattern

**Decision**: Authenticated API call via Axios with blob response, then trigger download via object URL.
**Rationale**: The endpoint requires Supabase JWT authentication. A simple `window.open(url)` won't carry the auth token. Instead, use `axios.get(url, { responseType: 'blob' })` with the existing auth interceptor, then create a temporary object URL and trigger download via an anchor element. This matches the existing Axios-based API pattern in the frontend.
