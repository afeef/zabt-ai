// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { MeetingHighlight } from "@/app/lib/api";
import { HelpCircle } from "lucide-react";

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

interface KeyQuestionsListProps {
  highlights: MeetingHighlight[];
  onTimestampClick?: (seconds: number) => void;
}

export function KeyQuestionsList({ highlights, onTimestampClick }: KeyQuestionsListProps) {
  const questions = highlights.filter((h) => h.highlight_type === "key_question");

  if (questions.length === 0) return null;

  return (
    <div className="space-y-1">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
        <HelpCircle className="size-4 text-orange-500" />
        Key Questions
      </h3>
      <div className="space-y-3">
        {questions.map((item) => (
          <div key={item.id} className="space-y-1.5">
            <div className="flex items-start gap-2">
              <button
                onClick={() => onTimestampClick?.(item.timestamp_start)}
                className="text-xs font-medium text-primary hover:underline min-w-[40px] pt-0.5 text-left"
              >
                {formatTimestamp(item.timestamp_start)}
              </button>
              <p className="text-sm font-medium text-foreground">{item.content}</p>
            </div>
            {item.ai_answer && (
              <div className="ml-[52px] text-sm text-muted-foreground bg-accent/50 px-3 py-2 rounded-md border-l-2 border-primary">
                <span className="text-xs font-medium text-primary">AI Proposed: </span>
                {item.ai_answer}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
