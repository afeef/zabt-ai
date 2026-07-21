// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import Link from "next/link";

export function RightPanel() {
    return (
        <div className="flex flex-col h-full px-4 py-5 gap-6">
            {/* Get started checklist */}
            <section>
                <h3 className="text-xs font-medium uppercase tracking-wide text-stone-400 mb-3">
                    Get Started
                </h3>
                <div className="space-y-2">
                    {[
                        { label: "Import your first meeting", done: false, href: "/" },
                        { label: "Invite a teammate", done: false, href: "#" },
                    ].map(({ label, done, href }) => (
                        <Link
                            key={label}
                            href={href}
                            className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 transition-colors"
                        >
                            <span
                                className={`w-4 h-4 rounded-full border flex-shrink-0 ${done ? "border-primary bg-primary" : "border-stone-300"
                                    }`}
                            />
                            <span className={`text-xs ${done ? "line-through text-stone-400" : "text-stone-500"}`}>
                                {label}
                            </span>
                        </Link>
                    ))}
                </div>
                <p className="mt-2 text-xs text-stone-400 text-right">0/2 complete</p>
            </section>
        </div>
    );
}
