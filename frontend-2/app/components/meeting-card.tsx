"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import type { Meeting } from "@/app/lib/api";
import { StatusBadge } from "@/app/components/status-badge";
import { Button } from "@/app/components/ui/button";

interface MeetingCardProps {
  meeting: Meeting;
  onDelete: (id: number) => void;
}

export function MeetingCard({ meeting, onDelete }: MeetingCardProps) {
  const date = new Date(meeting.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  const handleDelete = async () => {
    if (!confirm(`Delete "${meeting.title}"? This cannot be undone.`)) return;
    onDelete(meeting.id);
  };

  return (
    <div
      className="bg-white rounded-lg border border-stone-200 p-4 flex items-center justify-between gap-4"
    >
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-stone-900 truncate">{meeting.title}</p>
        <p className="text-xs text-stone-400 mt-1">{date}</p>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <StatusBadge status={meeting.status} subStatus={meeting.sub_status} />
        <Link href={`/meetings/${meeting.id}`}>
          <Button variant="secondary" size="sm">
            View
          </Button>
        </Link>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDelete}
          className="text-stone-300 hover:text-red-500 size-8"
          title="Delete meeting"
        >
          <Trash2 className="size-4" />
        </Button>
      </div>
    </div>
  );
}
