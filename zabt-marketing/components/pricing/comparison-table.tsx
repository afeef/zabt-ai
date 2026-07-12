import { Check, Minus } from "lucide-react";
import type { FeatureCategory, PricingTier } from "@/content/types";

function CellValue({ value }: { value: string | boolean }) {
  if (value === true) return <Check className="size-4 text-primary mx-auto" />;
  if (value === false) return <Minus className="size-4 text-stone-300 mx-auto" />;
  return <span className="text-sm text-stone-600">{value}</span>;
}

export function ComparisonTable({
  matrix,
  tiers,
}: {
  matrix: FeatureCategory[];
  tiers: PricingTier[];
}) {
  const tierNames = tiers.map((t) => t.name);
  const highlightedName = tiers.find((t) => t.highlighted)?.name;

  return (
    <section className="py-20 md:py-28">
      <div className="max-w-6xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-stone-900 text-center mb-12">
          Compare plans
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            {/* Header */}
            <thead>
              <tr className="border-b border-stone-200">
                <th className="text-left py-4 pr-4 w-1/3" />
                {tierNames.map((name) => (
                  <th
                    key={name}
                    className={`text-center py-4 px-4 text-sm font-semibold text-stone-900 ${
                      name === highlightedName ? "bg-primary/5 rounded-t-lg" : ""
                    }`}
                  >
                    {name}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {matrix.map((category) => (
                <>
                  {/* Category header */}
                  <tr key={`cat-${category.name}`}>
                    <td
                      colSpan={tierNames.length + 1}
                      className="text-sm font-semibold text-stone-900 bg-stone-50 px-4 py-3 border-y border-stone-200"
                    >
                      {category.name}
                    </td>
                  </tr>

                  {/* Feature rows */}
                  {category.rows.map((row) => (
                    <tr
                      key={row.name}
                      className="border-b border-stone-100 hover:bg-stone-50/50"
                    >
                      <td className="py-3 pr-4 text-sm text-stone-600">
                        {row.name}
                      </td>
                      {tierNames.map((tier) => (
                        <td
                          key={tier}
                          className={`py-3 px-4 text-center ${
                            tier === highlightedName ? "bg-primary/5" : ""
                          }`}
                        >
                          <CellValue value={row.values[tier]} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
