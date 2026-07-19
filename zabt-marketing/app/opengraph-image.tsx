// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { ImageResponse } from "next/og";
import { siteConfig } from "@/lib/seo/config";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = siteConfig.ogImageAlt;

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "#1c1917", // stone-900
          color: "#fafaf9", // stone-50
        }}
      >
        <div style={{ display: "flex", alignItems: "center", fontSize: 72, fontWeight: 700 }}>
          <span style={{ color: "#f43f5e" }}>zabt</span>
          <span>.ai</span>
        </div>
        <div style={{ marginTop: 24, fontSize: 40, fontWeight: 500, lineHeight: 1.2 }}>
          Self-hosted AI meeting notes
        </div>
        <div style={{ marginTop: 16, fontSize: 28, color: "#a8a29e" /* stone-400 */ }}>
          Transcribe, diarize & summarize — on infrastructure you control.
        </div>
      </div>
    ),
    { ...size },
  );
}
