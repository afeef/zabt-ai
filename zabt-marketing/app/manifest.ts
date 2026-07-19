// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/seo/config";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: siteConfig.title,
    short_name: "zabt.ai",
    description: siteConfig.description,
    start_url: "/",
    display: "standalone",
    background_color: "#1c1917",
    theme_color: "#1c1917",
    icons: [{ src: "/icon.png", sizes: "any", type: "image/png" }],
  };
}
