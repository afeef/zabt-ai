"use client";

import { MeetingHighlight } from "@/app/lib/api";
import { BookOpen } from "lucide-react";

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

interface ChaptersListProps {
  highlights: MeetingHighlight[];
  onTimestampClick?: (seconds: number) => void;
}

export function ChaptersList({ highlights, onTimestampClick }: ChaptersListProps) {
  const chapters = highlights.filter((h) => h.highlight_type === "chapter");

  if (chapters.length === 0) return null;

  return (
    <div className="space-y-1">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
        <BookOpen className="size-4 text-primary" />
        Chapters &amp; Topics
      </h3>
      <div className="space-y-0">
        {chapters.map((item) => {
          const meta = item.metadata as { description?: string; tags?: string[] } | null;
          return (
            <div key={item.id} className="py-3 border-b border-border last:border-b-0">
              <div className="flex items-start gap-2 mb-1">
                <button
                  onClick={() => onTimestampClick?.(item.timestamp_start)}
                  className="text-xs font-medium text-primary hover:underline min-w-[40px] pt-0.5 text-left"
                >
                  {formatTimestamp(item.timestamp_start)}
                </button>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{item.content}</p>
                  {meta?.description && (
                    <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                      {meta.description}
                    </p>
                  )}
                  {meta?.tags && meta.tags.length > 0 && (
                    <div className="flex gap-1.5 mt-1.5 flex-wrap">
                      {meta.tags.map((tag: string) => (
                        <span
                          key={tag}
                          className="text-[10px] bg-secondary text-secondary-foreground px-2 py-0.5 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
