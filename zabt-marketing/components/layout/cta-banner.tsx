import Link from "next/link";
import { ctaBanner } from "@/content/navigation";

export function CtaBanner() {
  return (
    <section className="bg-stone-900 py-16 md:py-20">
      <div className="max-w-6xl mx-auto px-6 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
          {ctaBanner.headline}
        </h2>
        <p className="text-lg text-stone-400 mb-8">{ctaBanner.subheadline}</p>
        <Link
          href={ctaBanner.cta.href}
          className="inline-flex items-center bg-primary text-white text-base font-medium rounded-lg h-12 px-8 hover:opacity-90 transition-opacity"
        >
          {ctaBanner.cta.label}
        </Link>
      </div>
    </section>
  );
}
