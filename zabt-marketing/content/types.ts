// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
export interface HeroContent {
  headline: string;
  subheadline: string;
  primaryCta: { label: string; href: string };
  secondaryCta: { label: string; href: string };
  image: string;
}

export interface Feature {
  title: string;
  description: string;
  bullets?: string[];
  image: string;
  align: "left" | "right";
}

export interface UseCase {
  tab: string;
  title: string;
  description: string;
  image: string;
}

export interface Step {
  icon: string;
  title: string;
  description: string;
}

export interface Integration {
  name: string;
  logo: string;
  available: boolean;
}

export interface Testimonial {
  quote: string;
  name: string;
  title: string;
  avatar?: string;
}

export interface PricingTier {
  name: string;
  price: { monthly: number | null; yearly: number | null };
  description: string;
  cta: { label: string; href: string };
  highlighted: boolean;
  features: string[];
}

export interface FeatureRow {
  name: string;
  values: Record<string, string | boolean>;
}

export interface FeatureCategory {
  name: string;
  rows: FeatureRow[];
}

export interface FaqItem {
  question: string;
  answer: string;
}

export interface NavLink {
  label: string;
  href: string;
}

export interface FooterColumn {
  title: string;
  links: NavLink[];
}
