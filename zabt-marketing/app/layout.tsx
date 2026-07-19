// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { AlphaBanner } from "@/components/layout/alpha-banner";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { GoogleAnalytics } from "@/components/analytics/google-analytics";
import { ClarityProvider } from "@/components/analytics/clarity-provider";
import { siteConfig } from "@/lib/seo/config";
import { JsonLd } from "@/components/seo/json-ld";
import { organizationSchema, softwareApplicationSchema } from "@/lib/seo/json-ld";
import { tiers } from "@/content/pricing";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: siteConfig.title,
    template: "%s — zabt.ai",
  },
  description: siteConfig.description,
  applicationName: siteConfig.name,
  alternates: { canonical: "/" },
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    siteName: siteConfig.name,
    url: siteConfig.url,
    title: siteConfig.title,
    description: siteConfig.description,
  },
  twitter: {
    card: "summary_large_image",
    title: siteConfig.title,
    description: siteConfig.description,
  },
  // Fill tokens when GSC / Bing are verified:
  // verification: { google: "GSC_TOKEN", other: { "msvalidate.01": "BING_TOKEN" } },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
      >
        <JsonLd data={organizationSchema()} />
        <JsonLd data={softwareApplicationSchema(tiers)} />
        <GoogleAnalytics />
        <ClarityProvider />
        <AlphaBanner />
        <Navbar />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
