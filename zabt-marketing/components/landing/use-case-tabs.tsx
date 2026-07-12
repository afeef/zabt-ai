// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState } from "react";
import Image from "next/image";
import type { UseCase } from "@/content/types";

export function UseCaseTabs({ useCases }: { useCases: UseCase[] }) {
  const [active, setActive] = useState(0);
  const current = useCases[active];

  return (
    <section className="py-20 md:py-28 bg-stone-50/50">
      <div className="max-w-6xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-stone-900 text-center mb-4">
          Built for every meeting
        </h2>
        <p className="text-lg text-stone-500 text-center max-w-2xl mx-auto mb-12">
          From team standups to medical consultations, Zabt adapts to your workflow.
        </p>

        {/* Tab triggers */}
        <div className="flex flex-wrap justify-center gap-2 mb-12">
          {useCases.map((uc, i) => (
            <button
              key={uc.tab}
              onClick={() => setActive(i)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                i === active
                  ? "bg-primary text-white"
                  : "bg-stone-100 text-stone-600 hover:bg-stone-200"
              }`}
            >
              {uc.tab}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h3 className="text-xl font-semibold text-stone-900 mb-3">
              {current.title}
            </h3>
            <p className="text-base text-stone-600 leading-relaxed">
              {current.description}
            </p>
          </div>
          <div className="relative aspect-[4/3] rounded-xl border border-stone-200 bg-stone-50 overflow-hidden">
            <Image
              src={current.image}
              alt={current.title}
              fill
              sizes="(max-width: 768px) 100vw, 50vw"
              className="object-contain"
              unoptimized={current.image.endsWith(".gif")}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
