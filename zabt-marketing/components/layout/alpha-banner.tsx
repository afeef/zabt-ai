// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import Link from "next/link";

export function AlphaBanner() {
  return (
    <div className="bg-stone-900 text-stone-50">
      <div className="max-w-6xl mx-auto px-6 py-2.5 flex items-center justify-center gap-3 text-center text-sm">
        <span className="inline-flex items-center rounded-4xl bg-primary px-2.5 py-0.5 text-xs font-semibold">
          Alpha
        </span>
        <span className="text-stone-200">
          Zabt is in early access — free to use for a limited time.
        </span>
        <Link
          href="/pricing"
          className="hidden sm:inline font-medium text-white underline-offset-4 hover:underline"
        >
          See pricing
        </Link>
      </div>
    </div>
  );
}
