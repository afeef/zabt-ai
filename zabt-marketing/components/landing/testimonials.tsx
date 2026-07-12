import type { Testimonial } from "@/content/types";

export function Testimonials({
  testimonials,
}: {
  testimonials: Testimonial[];
}) {
  return (
    <section className="py-20 md:py-28">
      <div className="max-w-6xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-stone-900 text-center mb-12">
          Loved by professionals
        </h2>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="border border-stone-200 rounded-xl p-6 bg-white"
            >
              <p className="text-base text-stone-600 italic mb-4">
                &ldquo;{t.quote}&rdquo;
              </p>
              <div className="flex items-center gap-3">
                {/* Placeholder avatar */}
                <div className="w-10 h-10 rounded-full bg-stone-200 flex items-center justify-center text-sm font-medium text-stone-500">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <div className="text-sm font-medium text-stone-900">
                    {t.name}
                  </div>
                  <div className="text-sm text-stone-500">{t.title}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
