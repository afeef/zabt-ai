// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { Metadata } from "next";
import { Hero } from "@/components/landing/hero";
import { FeatureShowcase } from "@/components/landing/feature-showcase";
import { UseCaseTabs } from "@/components/landing/use-case-tabs";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Integrations } from "@/components/landing/integrations";
import { Testimonials } from "@/components/landing/testimonials";
import { CtaBanner } from "@/components/layout/cta-banner";
import {
  hero,
  features,
  useCases,
  steps,
  integrations,
  testimonials,
} from "@/content/landing";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default function LandingPage() {
  return (
    <>
      <Hero content={hero} />
      <FeatureShowcase features={features} />
      <UseCaseTabs useCases={useCases} />
      <HowItWorks steps={steps} />
      <Integrations integrations={integrations} />
      <Testimonials testimonials={testimonials} />
      <CtaBanner />
    </>
  );
}
