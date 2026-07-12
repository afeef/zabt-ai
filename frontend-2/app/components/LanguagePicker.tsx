// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useEffect, useState } from "react";
import {
  listLanguages,
  getLanguagePreferences,
  type LanguageEntry,
} from "@/app/lib/api";

type Props = {
  value: string | null;
  onChange: (code: string) => void;
  className?: string;
};

export function LanguagePicker({ value, onChange, className }: Props) {
  const [catalog, setCatalog] = useState<LanguageEntry[]>([]);

  useEffect(() => {
    let mounted = true;
    Promise.all([listLanguages(), getLanguagePreferences()]).then(
      ([all, prefs]) => {
        if (!mounted) return;
        setCatalog(all);
        if (!value && prefs.length > 0) onChange(prefs[0]);
      },
    );
    return () => {
      mounted = false;
    };
  }, [value, onChange]);

  return (
    <select
      className={
        className ??
        "rounded-lg border border-stone-200 px-3 py-2 text-sm bg-white text-stone-700 focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
      }
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    >
      {catalog.map((e) => (
        <option key={e.code} value={e.code}>
          {e.display_name}
        </option>
      ))}
    </select>
  );
}
