// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { useBilling } from "./pricing-header";
import type { PricingTier } from "@/content/types";

export function PricingCards({ tiers }: { tiers: PricingTier[] }) {
  const { billing } = useBilling();

  return (
    <section className="pb-20 md:pb-28">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {tiers.map((tier) => {
            const price = billing === "monthly" ? tier.price.monthly : tier.price.yearly;

            return (
              <div
                key={tier.name}
                className={`rounded-xl p-6 bg-white ${
                  tier.highlighted
                    ? "border-2 border-primary relative"
                    : "border border-stone-200"
                }`}
              >
                {tier.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </div>
                )}

                <h2 className="text-lg font-semibold text-stone-900 mb-1">
                  {tier.name}
                </h2>
                <p className="text-sm text-stone-500 mb-4">{tier.description}</p>

                {/* Price */}
                <div className="mb-6">
                  {price !== null ? (
                    <div className="flex items-baseline gap-1">
                      <span className="text-5xl font-bold text-stone-900">
                        ${price}
                      </span>
                      <span className="text-base text-stone-500">
                        /{billing === "monthly" ? "mo" : "mo"}
                      </span>
                    </div>
                  ) : (
                    <div className="text-3xl font-bold text-stone-900">
                      Custom
                    </div>
                  )}
                </div>

                {/* CTA */}
                <Link
                  href={tier.cta.href}
                  className={`flex items-center justify-center w-full rounded-lg h-11 text-sm font-medium transition-colors mb-6 ${
                    tier.highlighted
                      ? "bg-primary text-white hover:opacity-90"
                      : "border border-stone-300 text-stone-700 hover:bg-stone-50"
                  }`}
                >
                  {tier.cta.label}
                </Link>

                {/* Features */}
                <ul className="space-y-2.5">
                  {tier.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-start gap-2 text-sm text-stone-600"
                    >
                      <Check className="size-4 text-primary flex-shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
