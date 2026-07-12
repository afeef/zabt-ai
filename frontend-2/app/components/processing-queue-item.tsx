"use client";

import { useRouter } from "next/navigation";
import { Upload, CheckCircle, XCircle } from "lucide-react";
import { STAGE_LABELS, STAGE_ORDER, getStageIndex } from "@/app/lib/stage-utils";
import { Spinner } from "@/app/components/ui/spinner";
import type { QueueItem } from "@/app/contexts/processing-queue-context";

function YouTubeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1c.5-1.9.5-5.8.5-5.8s0-3.9-.5-5.8zM9.5 15.5V8.5l6.3 3.5-6.3 3.5z" />
    </svg>
  );
}

function CompactProgress({ item }: { item: QueueItem }) {
  const currentIdx = getStageIndex(item.stage);
  const totalSteps = STAGE_ORDER.length;

  return (
    <div className="flex gap-0.5 mt-2">
      {STAGE_ORDER.map((stage, idx) => {
        const isCompleted = currentIdx > idx || (idx === totalSteps - 1 && currentIdx === idx);
        const isActive = currentIdx === idx && idx < totalSteps - 1;
        return (
          <div
            key={stage}
            title={STAGE_LABELS[stage].replace("…", "")}
            className={`h-1 flex-1 rounded-full transition-colors ${
              isCompleted
                ? "bg-emerald-500"
                : isActive
                  ? "bg-primary animate-pulse"
                  : "bg-stone-100"
            }`}
          />
        );
      })}
    </div>
  );
}

interface ProcessingQueueItemProps {
  item: QueueItem;
}

export function ProcessingQueueItem({ item }: ProcessingQueueItemProps) {
  const router = useRouter();

  const isDone = item.status === "done";
  const isFailed = item.status === "failed";
  const isProcessing = item.status === "processing";

  const handleClick = () => {
    if (isDone) {
      router.push(`/meetings/${item.meetingId}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`px-4 py-3 ${
        isDone ? "cursor-pointer hover:bg-stone-50 active:bg-stone-100 transition-colors" : ""
      }`}
    >
      <div className="flex items-start gap-2.5">
        {/* Source icon */}
        <div className="mt-0.5 flex-shrink-0">
          {item.sourceType === "youtube" ? (
            <YouTubeIcon className="w-4 h-4 text-red-500" />
          ) : (
            <Upload className="w-4 h-4 text-stone-400" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-stone-900 truncate flex-1">
              {item.displayName}
            </span>
            {isDone && <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />}
            {isFailed && <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
            {isProcessing && <Spinner className="size-4 flex-shrink-0" />}
          </div>

          <p className={`text-xs mt-0.5 ${isFailed ? "text-red-500" : "text-stone-400"}`}>
            {isFailed ? (item.errorMessage || "Processing failed") : STAGE_LABELS[item.stage]}
          </p>

          {isProcessing && <CompactProgress item={item} />}
        </div>
      </div>
    </div>
  );
}
