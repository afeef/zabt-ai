// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
export const siteConfig = {
  name: "zabt.ai",
  url: "https://zabt.ai",
  appUrl: "https://app.zabt.ai",
  title: "zabt.ai — Self-Hosted AI Meeting Notes & Transcription",
  description:
    "Self-hosted AI meeting intelligence. Transcribe, diarize, and summarize meetings on infrastructure you control — a private alternative to Otter.ai and Fireflies.",
  ogImageAlt: "zabt.ai — self-hosted AI meeting notes",
  contactEmail: "hello@zabt.ai",
  // Fill with real profile URLs as they exist; empty is valid.
  sameAs: [] as string[],
} as const;

export const SITE_URL = siteConfig.url;
export const APP_URL = siteConfig.appUrl;
