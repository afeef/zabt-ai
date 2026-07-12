# FAQ

## Licensing & usage

### Can my company use zabt.ai internally? Do we have to open-source anything?

**Yes, you can use it internally, freely — and no, you don't have to publish anything for
internal use.** The AGPL-3.0's source-sharing requirement is triggered by *conveying* the
software or making a *modified* version available **to users over a network**. Running an
**unmodified** zabt.ai for your own employees is fine with no obligations.

If you **modify** zabt.ai and let people **outside your organization** use that modified
version over a network (e.g. you offer it as a public service), then you must offer those users
the corresponding source of your modified version. Modifying it and keeping it strictly
internal does not trigger the obligation in practice, but if you're unsure, the safe reading is:
publish your changes or keep them internal.

### We want to embed zabt.ai in a proprietary product / SaaS without AGPL obligations.

That's what the **commercial license** is for. Email **licensing@zabt.ai**. The CLA every
contributor signs is what makes dual-licensing possible.

### Do I have to share my configuration or my meeting data?

No. The AGPL covers the **software source code**, not your data, your `.env`, your prompts, or
your transcripts. Those are yours.

### Can I fork it and rename it?

Yes, under the AGPL — but you must remove the "zabt" / "zabt.ai" names and logo, which are
trademarks (see [NOTICE](../NOTICE)). The license grants copyright rights, not trademark rights.

## Models & data

### Why do I need a Hugging Face token?

Speaker diarization uses **pyannote** models that are *gated* on Hugging Face. We do not (and
legally should not) redistribute those weights. You accept the model's terms and download them
yourself with your `HF_TOKEN`. See the [self-hosting guide](self-hosting.md#pyannote-hugging-face-gate).

### Does my audio leave my server?

Transcription and diarization run on your infrastructure (local GPU or your RunPod account).
The one thing that leaves is the **transcript text sent to your chosen LLM** for
summarization — and you control which LLM. Point `OPENAI_BASE_URL` at a **local** model
(Ollama/vLLM/LM Studio) to keep everything on-prem.

### Which Whisper model should I use?

`large-v3` for best accuracy (needs ~10-12 GB VRAM). On CPU or small GPUs use `base`/`small`.
See [hardware requirements](../README.md#hardware-requirements).

## Deployment

### Do I need a GPU?

No — a CPU-only path exists (`docker-compose.cpu.yml`), just slower. A GPU is strongly
recommended for `large-v3` and for reasonable throughput.

### Do I need Kong?

No. Kong is only in the optional cloud/production topology as a TLS gateway. The default
single-machine stack does not use it.

### Do I need Supabase? Can I self-host auth?

zabt.ai delegates authentication to Supabase. The easiest path is a **free Supabase cloud
project**. You can also run **self-hosted Supabase** separately and point the `SUPABASE_*`
variables at it — the app only needs the auth endpoints and the JWT secret.

### Can I use S3 / Cloudflare R2 instead of MinIO?

Yes — set `STORAGE_PROVIDER=s3` and the `S3_*` variables. See
[configuration](configuration.md#object-storage).

## Contributing

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md). You'll sign a quick [CLA](../CLA.md) on your first
PR (automated).

### I found a security issue.

Do **not** open a public issue — see [SECURITY.md](../SECURITY.md) (email security@zabt.ai).
