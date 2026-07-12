"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface AiQueryBarProps {
    onSubmit?: (query: string) => void;
}

export function AiQueryBar({ onSubmit }: AiQueryBarProps) {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [advanced, setAdvanced] = useState(false);

    const handleSubmit = () => {
        const trimmed = query.trim();
        if (!trimmed) return;
        if (onSubmit) {
            onSubmit(trimmed);
        } else {
            router.push(`/meetings?q=${encodeURIComponent(trimmed)}`);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") handleSubmit();
    };

    return (
        <div className="bg-white border border-stone-200 rounded-lg flex items-center gap-2 px-4 py-3">
            {/* Sparkle icon */}
            <svg
                className="w-4 h-4 text-primary/60 flex-shrink-0"
                viewBox="0 0 20 20"
                fill="currentColor"
            >
                <path
                    fillRule="evenodd"
                    d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z"
                    clipRule="evenodd"
                />
            </svg>

            {/* Input */}
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask Zabt anything about your meetings…"
                className="flex-1 text-sm text-stone-700 placeholder-stone-400 bg-transparent focus:outline-none"
            />

            {/* Advanced toggle */}
            <button
                onClick={() => setAdvanced((v) => !v)}
                className={`text-xs font-medium transition-colors px-2 py-1 rounded-lg ${advanced
                        ? "text-primary bg-primary/10"
                        : "text-stone-400 hover:text-stone-500"
                    }`}
            >
                Advanced
            </button>

            {/* Submit */}
            <button
                onClick={handleSubmit}
                disabled={!query.trim()}
                className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:bg-stone-200 disabled:text-stone-400 transition-colors flex-shrink-0"
                aria-label="Submit"
            >
                <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                        fillRule="evenodd"
                        d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                        clipRule="evenodd"
                    />
                </svg>
            </button>
        </div>
    );
}
