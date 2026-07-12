import Image from "next/image";
import type { Integration } from "@/content/types";

export function Integrations({
  integrations,
}: {
  integrations: Integration[];
}) {
  return (
    <section id="integrations" className="py-20 md:py-28 bg-stone-50/50">
      <div className="max-w-6xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-stone-900 text-center mb-4">
          Works with your tools
        </h2>
        <p className="text-lg text-stone-500 text-center max-w-2xl mx-auto mb-12">
          Connect Zabt to the tools your team already uses.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
          {integrations.map((integration) => (
            <div
              key={integration.name}
              className="flex flex-col items-center gap-3 p-4 rounded-xl border border-stone-200 bg-white hover:border-stone-300 transition-colors"
            >
              <Image
                src={integration.logo}
                alt={integration.name}
                width={48}
                height={48}
                className={integration.available ? "" : "opacity-40"}
              />
              <span className="text-sm font-medium text-stone-700">
                {integration.name}
              </span>
              {!integration.available && (
                <span className="text-xs text-stone-400">Coming soon</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
