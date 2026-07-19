// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua

export interface DetectionInput {
  text: string;
  brandTerms: string[];
  brandDomain: string;
  competitors: string[];
}

export interface Detection {
  mentioned: boolean;
  cited: boolean;
  competitorsMentioned: string[];
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function wordPresent(haystack: string, term: string): boolean {
  const re = new RegExp(`(^|[^a-z0-9])${escapeRegExp(term.toLowerCase())}([^a-z0-9]|$)`);
  return re.test(haystack);
}

export function detect(input: DetectionInput): Detection {
  const text = input.text.toLowerCase();

  const mentioned = input.brandTerms.some((t) => wordPresent(text, t));

  const domain = escapeRegExp(input.brandDomain.toLowerCase());
  // Match the brand domain as a real host (exact or a subdomain of it), optionally
  // with protocol/path/port/query — but NOT as a suffix of a longer label
  // (e.g. "notzabt.ai") nor as a prefix label of another domain ("zabt.ai.evil.com").
  const host = `(?:[a-z0-9-]+\\.)*${domain}`;
  const cited = new RegExp(
    `(?:^|[\\s/@(])(?:https?://)?${host}(?=[/:?#)]|\\.?(?:\\s|$))`,
  ).test(text);

  const competitorsMentioned = Array.from(
    new Set(input.competitors.filter((c) => wordPresent(text, c))),
  );

  return { mentioned, cited: mentioned && cited, competitorsMentioned };
}
