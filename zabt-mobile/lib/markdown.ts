// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
/**
 * Strip common markdown syntax for short list previews. Not exhaustive — just
 * removes the noise so a card snippet reads naturally without rendering.
 */
export function stripMarkdown(md: string): string {
  return md
    .replace(/^#{1,6}\s+/gm, "")           // headings
    .replace(/\*\*(.+?)\*\*/g, "$1")       // bold
    .replace(/\*(.+?)\*/g, "$1")           // italic
    .replace(/`(.+?)`/g, "$1")             // inline code
    .replace(/^\s*[-*+]\s+/gm, "")         // list bullets
    .replace(/^\s*\d+\.\s+/gm, "")         // ordered list
    .replace(/\[(.+?)\]\(.+?\)/g, "$1")    // links → text
    .replace(/\n{2,}/g, " ")               // collapse blank lines
    .trim();
}
