"use client";

import { memo } from "react";
import { TranscriptSegment, TranscriptWord } from "@/app/lib/api";
import { useTranscriptStore } from "@/app/lib/use-transcript-store";

const formatTime = (seconds: number) => {
    if (isNaN(seconds) || seconds < 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
};

const SPEAKER_COLORS: Record<string, string> = {
    SPEAKER_00: "bg-stone-500 text-white",
    SPEAKER_01: "bg-amber-500 text-white",
    SPEAKER_02: "bg-teal-500 text-white",
    SPEAKER_03: "bg-emerald-500 text-white",
};

const getSpeakerColor = (speaker: string) =>
    SPEAKER_COLORS[speaker] ?? "bg-stone-200 text-stone-500";

const getSpeakerLabel = (speaker: string) => {
    if (speaker === "SPEAKER_UNKNOWN") return "Unknown Speaker";
    const num = speaker.split("_")[1];
    return num !== undefined ? `Speaker ${parseInt(num) + 1}` : speaker;
};

const WordSpan = memo(({ word }: { word: TranscriptWord }) => {
    const isHighlighted = useTranscriptStore((state) =>
        state.currentTime >= word.start && state.currentTime <= word.end
    );
    const { setSeekRequest } = useTranscriptStore();

    return (
        <span
            className={`cursor-pointer rounded px-0.5 -mx-0.5 transition-colors duration-75 ${
                isHighlighted ? "bg-primary text-primary-foreground" : "hover:bg-stone-100"
            }`}
            onClick={() => setSeekRequest(word.start)}
        >
            {word.word}{" "}
        </span>
    );
});

WordSpan.displayName = "WordSpan";

function SegmentRow({
    segment,
    isPaywalled,
}: {
    segment: TranscriptSegment;
    isPaywalled: boolean;
}) {
    const { setSeekRequest } = useTranscriptStore();
    const words = Array.isArray(segment.words) ? segment.words : [];
    const isUnknown = segment.speaker === "SPEAKER_UNKNOWN";

    return (
        <div
            className={`flex gap-4 py-4 border-b border-stone-100 last:border-none group ${
                isPaywalled ? "blur-sm opacity-50 select-none pointer-events-none" : ""
            }`}
        >
            {/* Avatar */}
            <div className="flex-shrink-0 pt-0.5">
                <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${getSpeakerColor(segment.speaker)}`}
                >
                    {isUnknown ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                        </svg>
                    ) : (
                        getSpeakerLabel(segment.speaker).charAt(getSpeakerLabel(segment.speaker).indexOf(" ") + 1)
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-sm font-medium text-stone-900">
                        {getSpeakerLabel(segment.speaker)}
                    </span>
                    <button
                        className="text-xs text-stone-400 hover:text-primary transition-colors tabular-nums cursor-pointer"
                        onClick={() => setSeekRequest(segment.start)}
                    >
                        {formatTime(segment.start)}
                    </button>
                </div>
                <p className="text-sm leading-relaxed text-stone-700">
                    {words.length > 0 ? (
                        words.map((w, i) => <WordSpan key={i} word={w} />)
                    ) : (
                        segment.text
                    )}
                </p>
            </div>
        </div>
    );
}

export function TranscriptViewer({
    segments,
    isFreeTier = false,
}: {
    segments: TranscriptSegment[];
    isFreeTier?: boolean;
}) {
    if (!segments || segments.length === 0) {
        return <p className="text-sm text-stone-400 py-4">No transcript available.</p>;
    }

    return (
        <div className="divide-y divide-stone-100">
            {[...segments].sort((a, b) => a.start - b.start).map((segment, index) => (
                <SegmentRow
                    key={index}
                    segment={segment}
                    isPaywalled={isFreeTier && segment.start >= 1800}
                />
            ))}
        </div>
    );
}
