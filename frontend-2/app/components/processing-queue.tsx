"use client";

import { usePostHog } from "posthog-js/react";
import { useProcessingQueue } from "@/app/contexts/processing-queue-context";
import { ProcessingQueueItem } from "@/app/components/processing-queue-item";
import { ChevronDown, ChevronUp, X } from "lucide-react";

export function ProcessingQueue() {
  const posthog = usePostHog();
  const { items, isCollapsed, isVisible, setCollapsed, clearQueue } = useProcessingQueue();

  if (!isVisible || items.length === 0) return null;

  const activeCount = items.filter((i) => i.status === "processing").length;
  const allDone = activeCount === 0;

  if (isCollapsed) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => { setCollapsed(false); posthog?.capture("processing_queue_expanded"); }}
          className="flex items-center gap-2.5 bg-white border border-stone-200 rounded-lg px-4 py-2.5 text-sm font-medium text-stone-700 hover:bg-stone-50 active:bg-stone-100 transition-colors"
        >
          {allDone ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              All done
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              {activeCount} processing
            </>
          )}
          <ChevronUp className="w-3.5 h-3.5 text-stone-400" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 bg-white border border-stone-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-stone-100">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-stone-900">Processing</h3>
          {!allDone && (
            <span className="text-xs tabular-nums text-stone-400">{activeCount} active</span>
          )}
        </div>
        <div className="flex items-center">
          {allDone && (
            <button
              onClick={clearQueue}
              className="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-50 active:bg-stone-100 transition-colors"
              aria-label="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={() => { setCollapsed(true); posthog?.capture("processing_queue_collapsed"); }}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-50 active:bg-stone-100 transition-colors"
            aria-label="Minimize"
          >
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Items */}
      <div className="max-h-64 overflow-y-auto divide-y divide-stone-100">
        {items.map((item) => (
          <ProcessingQueueItem key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
