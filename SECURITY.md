# Security Policy

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or
pull requests.**

Instead, email **security@zabt.ai** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept if possible)
- Affected version / commit and deployment topology (single-machine vs cloud/RunPod split)
- Any suggested remediation

You can also use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository ("Security" tab → "Report a vulnerability").

## What to expect

- **Acknowledgement** within 3 business days.
- A validation and severity assessment, with an estimated fix timeline.
- **Coordinated disclosure:** we ask that you give us up to **90 days** to release a fix
  before any public disclosure. We're happy to credit you in the advisory unless you prefer to
  remain anonymous.

## Scope note

zabt.ai processes **meeting audio, transcripts, and summaries** — inherently sensitive data.
Self-hosted deployments should be treated as sensitive systems:

- Keep `.env` secret; never commit it. Rotate any credential you suspect was exposed.
- Put the API/UI behind TLS and authentication for any non-localhost deployment.
- Restrict network access to Postgres, Redis, and object storage.
- Model weights and the ffmpeg binary are obtained by the operator; keep them patched.

We especially welcome reports concerning authentication/authorization, tenant isolation,
presigned-URL handling, SSRF, and secret exposure.

## Supported versions

This is a young project; security fixes are applied to the latest `main`. Please run a recent
version before reporting.
