// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { Metadata } from "next";
import {
  PricingProvider,
  PricingHeader,
} from "@/components/pricing/pricing-header";
import { PricingCards } from "@/components/pricing/pricing-cards";
import { ComparisonTable } from "@/components/pricing/comparison-table";
import { Faq } from "@/components/pricing/faq";
import { CtaBanner } from "@/components/layout/cta-banner";
import { tiers, featureMatrix, faqItems } from "@/content/pricing";
import { JsonLd } from "@/components/seo/json-ld";
import { faqPageSchema, breadcrumbSchema } from "@/lib/seo/json-ld";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Choose the plan that fits your needs. Start free, scale as you grow.",
  alternates: { canonical: "/pricing" },
};

export default function PricingPage() {
  return (
    <PricingProvider>
      <JsonLd data={faqPageSchema(faqItems)} />
      <JsonLd data={breadcrumbSchema([{ name: "Home", path: "/" }, { name: "Pricing", path: "/pricing" }])} />
      <PricingHeader />
      <PricingCards tiers={tiers} />
      <ComparisonTable matrix={featureMatrix} tiers={tiers} />
      <Faq items={faqItems} />
      <CtaBanner />
    </PricingProvider>
  );
}
