// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { describe, expect, it } from "vitest";
import {
  organizationSchema,
  softwareApplicationSchema,
  faqPageSchema,
  breadcrumbSchema,
} from "./json-ld";
import type { PricingTier, FaqItem } from "@/content/types";

const tiers: PricingTier[] = [
  { name: "Basic", price: { monthly: 0, yearly: 0 }, description: "", cta: { label: "", href: "" }, highlighted: false, features: [] },
  { name: "Pro", price: { monthly: 16, yearly: 12 }, description: "", cta: { label: "", href: "" }, highlighted: true, features: [] },
  { name: "Enterprise", price: { monthly: null, yearly: null }, description: "", cta: { label: "", href: "" }, highlighted: false, features: [] },
];
const faqs: FaqItem[] = [{ question: "Q1?", answer: "A1." }];

describe("json-ld builders", () => {
  it("organization has @context, @type, canonical url", () => {
    const s = organizationSchema();
    expect(s["@context"]).toBe("https://schema.org");
    expect(s["@type"]).toBe("Organization");
    expect(s.url).toBe("https://zabt.ai");
  });

  it("softwareApplication drops null-priced tiers from offers", () => {
    const s = softwareApplicationSchema(tiers);
    expect(s["@type"]).toBe("SoftwareApplication");
    expect(s.offers).toHaveLength(2); // Basic + Pro; Enterprise (null) excluded
    expect(s.offers[0]).toMatchObject({ "@type": "Offer", priceCurrency: "USD" });
  });

  it("faqPage maps each item to a Question/Answer pair", () => {
    const s = faqPageSchema(faqs);
    expect(s["@type"]).toBe("FAQPage");
    expect(s.mainEntity).toHaveLength(1);
    expect(s.mainEntity[0]).toMatchObject({
      "@type": "Question",
      name: "Q1?",
      acceptedAnswer: { "@type": "Answer", text: "A1." },
    });
  });

  it("breadcrumb numbers positions from 1 and builds absolute urls", () => {
    const s = breadcrumbSchema([{ name: "Home", path: "/" }, { name: "Pricing", path: "/pricing" }]);
    expect(s.itemListElement[1]).toMatchObject({ position: 2, item: "https://zabt.ai/pricing" });
  });
});
