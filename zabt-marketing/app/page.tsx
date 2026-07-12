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
