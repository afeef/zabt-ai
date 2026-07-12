"use client";

import { MeetingHighlight } from "@/app/lib/api";
import { CheckCircle2 } from "lucide-react";

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

interface ActionItemsListProps {
  highlights: MeetingHighlight[];
  onTimestampClick?: (seconds: number) => void;
}

export function ActionItemsList({ highlights, onTimestampClick }: ActionItemsListProps) {
  const actionItems = highlights.filter((h) => h.highlight_type === "action_item");

  if (actionItems.length === 0) return null;

  return (
    <div className="space-y-1">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
        <CheckCircle2 className="size-4 text-primary" />
        Action Items
      </h3>
      <div className="space-y-0">
        {actionItems.map((item) => (
          <div key={item.id} className="flex gap-3 py-2.5 border-b border-border last:border-b-0">
            <button
              onClick={() => onTimestampClick?.(item.timestamp_start)}
              className="text-xs font-medium text-primary hover:underline min-w-[40px] pt-0.5 text-left"
            >
              {formatTimestamp(item.timestamp_start)}
            </button>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground leading-relaxed">{item.content}</p>
              {(() => {
                const assignee = (item.metadata as { assignee?: string } | null)?.assignee;
                return assignee ? (
                  <p className="text-xs text-muted-foreground font-medium mt-0.5">
                    → {assignee}
                  </p>
                ) : null;
              })()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
