"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

const BillingContext = createContext<{
  billing: "monthly" | "yearly";
  setBilling: (b: "monthly" | "yearly") => void;
}>({ billing: "monthly", setBilling: () => {} });

export function useBilling() {
  return useContext(BillingContext);
}

export function PricingProvider({ children }: { children: ReactNode }) {
  const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");

  return (
    <BillingContext.Provider value={{ billing, setBilling }}>
      {children}
    </BillingContext.Provider>
  );
}

export function PricingHeader() {
  const { billing, setBilling } = useBilling();

  return (
    <section className="py-20 md:py-28">
      <div className="max-w-6xl mx-auto px-6 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-stone-900 mb-4">
          Choose your plan
        </h1>
        <p className="text-lg text-stone-500 max-w-2xl mx-auto mb-10">
          Start free and scale as your team grows. No credit card required.
        </p>

        {/* Billing toggle */}
        <div className="inline-flex items-center bg-stone-100 rounded-lg p-1">
          <button
            onClick={() => setBilling("monthly")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billing === "monthly"
                ? "bg-white text-stone-900"
                : "text-stone-500 hover:text-stone-700"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBilling("yearly")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billing === "yearly"
                ? "bg-white text-stone-900"
                : "text-stone-500 hover:text-stone-700"
            }`}
          >
            Yearly
            <span className="ml-1.5 text-xs text-primary font-semibold">
              Save 20%
            </span>
          </button>
        </div>
      </div>
    </section>
  );
}
