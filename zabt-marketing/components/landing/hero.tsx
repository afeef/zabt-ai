import Image from "next/image";
import Link from "next/link";
import type { HeroContent } from "@/content/types";

export function Hero({ content }: { content: HeroContent }) {
  return (
    <section className="relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[oklch(0.95_0.02_17)] to-[oklch(0.985_0.001_106.423)]" />

      <div className="relative max-w-6xl mx-auto px-6 py-20 md:py-28 text-center">
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-stone-900 mb-6">
          {content.headline}
        </h1>

        <p className="text-lg md:text-xl text-stone-500 max-w-2xl mx-auto mb-10">
          {content.subheadline}
        </p>

        <div className="flex items-center justify-center gap-4 mb-16">
          <Link
            href={content.primaryCta.href}
            className="inline-flex items-center bg-primary text-white text-base font-medium rounded-lg h-12 px-8 hover:opacity-90 transition-opacity"
          >
            {content.primaryCta.label}
          </Link>
          <Link
            href={content.secondaryCta.href}
            className="inline-flex items-center border border-stone-300 text-stone-700 text-base font-medium rounded-lg h-12 px-8 hover:bg-stone-50 transition-colors"
          >
            {content.secondaryCta.label}
          </Link>
        </div>

        {/* Product screenshot */}
        <div className="max-w-4xl mx-auto">
          <div className="relative aspect-[3/2] rounded-2xl border border-stone-200 bg-stone-50 overflow-hidden">
            <Image
              src={content.image}
              alt="Zabt AI dashboard"
              fill
              sizes="(max-width: 768px) 100vw, 896px"
              className="object-contain"
              priority
            />
          </div>
        </div>
      </div>
    </section>
  );
}
