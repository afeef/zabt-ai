// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { NavLink, FooterColumn } from "./types";

export const navLinks: NavLink[] = [
  { label: "Product", href: "/#features" },
  { label: "Pricing", href: "/pricing" },
];

export const ctaLinks = {
  signIn: { label: "Sign In", href: "https://app.zabt.ai" },
  getStarted: { label: "Get Started", href: "https://app.zabt.ai/register" },
};

export const footerColumns: FooterColumn[] = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "/#features" },
      { label: "Pricing", href: "/pricing" },
      { label: "Integrations", href: "/#integrations" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "#" },
      { label: "Contact", href: "mailto:hello@zabt.ai" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "#" },
      { label: "API", href: "#" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
    ],
  },
];

export const ctaBanner = {
  headline: "Start transcribing your meetings today",
  subheadline: "Free to start. No credit card required.",
  cta: { label: "Get Started Free", href: "https://app.zabt.ai/register" },
};
