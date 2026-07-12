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

export const metadata: Metadata = {
  title: "Pricing — Zabt AI",
  description: "Choose the plan that fits your needs. Start free, scale as you grow.",
};

export default function PricingPage() {
  return (
    <PricingProvider>
      <PricingHeader />
      <PricingCards tiers={tiers} />
      <ComparisonTable matrix={featureMatrix} tiers={tiers} />
      <Faq items={faqItems} />
      <CtaBanner />
    </PricingProvider>
  );
}
