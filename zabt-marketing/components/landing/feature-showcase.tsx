// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import Image from "next/image";
import { Check } from "lucide-react";
import type { Feature } from "@/content/types";

function FeatureSection({ feature }: { feature: Feature }) {
  const textSide = (
    <div className="flex flex-col justify-center">
      <h2 className="text-xl font-semibold text-stone-900 mb-3">
        {feature.title}
      </h2>
      <p className="text-base text-stone-600 leading-relaxed mb-4">
        {feature.description}
      </p>
      {feature.bullets && (
        <ul className="space-y-2">
          {feature.bullets.map((bullet) => (
            <li key={bullet} className="flex items-center gap-2 text-sm text-stone-600">
              <Check className="size-4 text-primary flex-shrink-0" />
              {bullet}
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  const isAnimated = feature.image.endsWith(".gif");
  const imageSide = (
    <div className="relative aspect-[4/3] rounded-xl border border-stone-200 bg-stone-50 overflow-hidden">
      <Image
        src={feature.image}
        alt={feature.title}
        fill
        sizes="(max-width: 768px) 100vw, 50vw"
        className="object-contain"
        unoptimized={isAnimated}
      />
    </div>
  );

  return (
    <div className="grid md:grid-cols-2 gap-12 items-center">
      {feature.align === "left" ? (
        <>
          {textSide}
          {imageSide}
        </>
      ) : (
        <>
          {imageSide}
          {textSide}
        </>
      )}
    </div>
  );
}

export function FeatureShowcase({ features }: { features: Feature[] }) {
  return (
    <section id="features" className="py-20 md:py-28">
      <div className="max-w-6xl mx-auto px-6 space-y-20 md:space-y-28">
        {features.map((feature) => (
          <FeatureSection key={feature.title} feature={feature} />
        ))}
      </div>
    </section>
  );
}
