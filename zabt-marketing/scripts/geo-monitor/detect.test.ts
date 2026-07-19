// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { describe, expect, it } from "vitest";
import { detect } from "./detect";

const base = {
  brandTerms: ["zabt", "zabt.ai"],
  brandDomain: "zabt.ai",
  competitors: ["otter", "fireflies", "fathom", "tldv", "read.ai", "granola"],
};

describe("detect", () => {
  it("finds a plain brand mention (word boundary, case-insensitive)", () => {
    const r = detect({ ...base, text: "You could try Zabt for that." });
    expect(r.mentioned).toBe(true);
    expect(r.cited).toBe(false);
  });

  it("does not match brand as a substring of another word", () => {
    const r = detect({ ...base, text: "The zabtastic tool is unrelated." });
    expect(r.mentioned).toBe(false);
  });

  it("detects a citation when the brand domain appears as a URL", () => {
    const r = detect({ ...base, text: "See https://zabt.ai/pricing for details." });
    expect(r.mentioned).toBe(true);
    expect(r.cited).toBe(true);
  });

  it("lists competitors mentioned, de-duplicated", () => {
    const r = detect({
      ...base,
      text: "Otter and Fireflies are popular; Otter is the biggest.",
    });
    expect(r.competitorsMentioned.sort()).toEqual(["fireflies", "otter"]);
  });

  it("reports no mention when brand absent", () => {
    const r = detect({ ...base, text: "Granola is a local-first notepad." });
    expect(r.mentioned).toBe(false);
    expect(r.competitorsMentioned).toEqual(["granola"]);
  });

  it("does not count a look-alike/decoy domain as a citation", () => {
    const r = detect({ ...base, text: "Zabt is great. Full review at https://notzabt.ai/review123" });
    expect(r.mentioned).toBe(true);
    expect(r.cited).toBe(false);
  });

  it("does not count the brand domain used as a prefix label of another domain", () => {
    const r = detect({ ...base, text: "Beware https://zabt.ai.phishing.com/deal — Zabt lookalikes exist." });
    expect(r.cited).toBe(false);
  });

  it("counts a real subdomain of the brand as a citation", () => {
    const r = detect({ ...base, text: "Sign in at https://app.zabt.ai/login" });
    expect(r.mentioned).toBe(true);
    expect(r.cited).toBe(true);
  });

  it("counts a bare brand-domain mention (no protocol) as a citation", () => {
    const r = detect({ ...base, text: "Just go to zabt.ai for details." });
    expect(r.cited).toBe(true);
  });
});
