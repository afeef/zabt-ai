"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { FaqItem } from "@/content/types";

function FaqAccordionItem({ item }: { item: FaqItem }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-stone-200">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full py-4 text-left"
      >
        <span className="text-base font-medium text-stone-900">
          {item.question}
        </span>
        <ChevronDown
          className={`size-5 text-stone-400 flex-shrink-0 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      {open && (
        <div className="pb-4 text-sm text-stone-600 leading-relaxed">
          {item.answer}
        </div>
      )}
    </div>
  );
}

export function Faq({ items }: { items: FaqItem[] }) {
  return (
    <section className="py-20 md:py-28 bg-stone-50/50">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-stone-900 text-center mb-12">
          Frequently asked questions
        </h2>

        <div>
          {items.map((item) => (
            <FaqAccordionItem key={item.question} item={item} />
          ))}
        </div>
      </div>
    </section>
  );
}
