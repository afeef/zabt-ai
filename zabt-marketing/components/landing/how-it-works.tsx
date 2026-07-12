import * as Icons from "lucide-react";
import type { Step } from "@/content/types";

export function HowItWorks({ steps }: { steps: Step[] }) {
  return (
    <section id="how-it-works" className="py-20 md:py-28">
      <div className="max-w-6xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-stone-900 text-center mb-4">
          How it works
        </h2>
        <p className="text-lg text-stone-500 text-center max-w-2xl mx-auto mb-16">
          Three simple steps to go from recording to actionable notes.
        </p>

        <div className="grid md:grid-cols-3 gap-8 md:gap-12">
          {steps.map((step, i) => {
            const IconComponent = (Icons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[step.icon] || Icons.FileText;
            return (
              <div key={step.title} className="text-center">
                {/* Icon in pink circle */}
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[oklch(0.97_0.015_17)] mb-5">
                  <IconComponent className="size-6 text-primary" />
                </div>

                {/* Step number + title */}
                <div className="text-xs font-medium text-stone-400 uppercase tracking-wide mb-2">
                  Step {i + 1}
                </div>
                <h3 className="text-lg font-semibold text-stone-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-base text-stone-600">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
