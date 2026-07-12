// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // Zabt warm stone + pink accent (oklch → HEX approximations for RN)
        background: "#fafaf8",
        foreground: "#1a1510",
        primary: "#e11d74",
        "primary-foreground": "#ffffff",
        secondary: "#f5f4f1",
        "secondary-foreground": "#2c2822",
        muted: "#f5f4f1",
        "muted-foreground": "#6b655c",
        accent: "#f5f4f1",
        "accent-foreground": "#2c2822",
        border: "#e5e3de",
        input: "#e5e3de",
        ring: "#e11d74",
        destructive: "#dc2626",
        stone: {
          50: "#fafaf8",
          100: "#f5f4f1",
          200: "#e5e3de",
          300: "#d1cdc5",
          400: "#9a9288",
          500: "#6b655c",
          600: "#4a4540",
          700: "#2c2822",
          800: "#1a1510",
          900: "#0f0c09",
        },
      },
      borderRadius: {
        lg: "10px",
        "4xl": "9999px",
      },
      fontFamily: {
        sans: ["Inter", "System"],
        mono: ["JetBrainsMono", "Menlo"],
      },
    },
  },
  plugins: [],
};
