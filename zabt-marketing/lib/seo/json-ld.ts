// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { siteConfig } from "./config";
import type { FaqItem, PricingTier } from "@/content/types";

const CONTEXT = "https://schema.org" as const;

export function organizationSchema() {
  return {
    "@context": CONTEXT,
    "@type": "Organization",
    name: siteConfig.name,
    url: siteConfig.url,
    logo: `${siteConfig.url}/icon.png`,
    email: siteConfig.contactEmail,
    sameAs: siteConfig.sameAs,
  };
}

export function softwareApplicationSchema(tiers: PricingTier[]) {
  const offers = tiers
    .filter((t) => t.price.monthly !== null)
    .map((t) => ({
      "@type": "Offer",
      name: t.name,
      price: String(t.price.monthly),
      priceCurrency: "USD",
    }));
  return {
    "@context": CONTEXT,
    "@type": "SoftwareApplication",
    name: siteConfig.name,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web, Docker, Linux, macOS",
    url: siteConfig.appUrl,
    description: siteConfig.description,
    offers,
  };
}

export function faqPageSchema(items: FaqItem[]) {
  return {
    "@context": CONTEXT,
    "@type": "FAQPage",
    mainEntity: items.map((i) => ({
      "@type": "Question",
      name: i.question,
      acceptedAnswer: { "@type": "Answer", text: i.answer },
    })),
  };
}

export function breadcrumbSchema(crumbs: { name: string; path: string }[]) {
  return {
    "@context": CONTEXT,
    "@type": "BreadcrumbList",
    itemListElement: crumbs.map((c, idx) => ({
      "@type": "ListItem",
      position: idx + 1,
      name: c.name,
      item: `${siteConfig.url}${c.path}`,
    })),
  };
}
