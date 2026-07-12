import { clsx } from "clsx";
import { Loader2 } from "lucide-react";
import { type UserStage, STAGE_ORDER, STAGE_LABELS, getStageIndex } from "@/app/lib/stage-utils";

interface ProgressStepsProps {
  currentStage: UserStage;
}

export function ProgressSteps({ currentStage }: ProgressStepsProps) {
  const currentIdx = getStageIndex(currentStage);
  const isFailed = currentStage === "failed";

  return (
    <div className="flex items-center w-full gap-0">
      {STAGE_ORDER.map((stage, idx) => {
        const isLast = idx === STAGE_ORDER.length - 1;
        const isCompleted = !isFailed && (currentIdx > idx || (isLast && currentIdx === idx));
        const isActive = !isFailed && currentIdx === idx && !isLast;
        const isPending = isFailed || currentIdx < idx;

        return (
          <div key={stage} className="flex items-center flex-1 last:flex-none">
            {/* Step circle + label */}
            <div className="flex flex-col items-center gap-1">
              <div
                className={clsx(
                  "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-all",
                  isCompleted && "bg-primary text-white",
                  isActive && "ring-2 ring-primary bg-white text-primary",
                  isPending && "border border-stone-200 bg-white text-stone-400"
                )}
              >
                {isCompleted ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : isActive ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>
              <span
                className={clsx(
                  "text-[10px] font-medium whitespace-nowrap",
                  isCompleted && "text-primary",
                  isActive && "text-primary",
                  isPending && "text-stone-400"
                )}
              >
                {STAGE_LABELS[stage].replace("…", "")}
              </span>
            </div>

            {/* Connecting line (not after last item) */}
            {idx < STAGE_ORDER.length - 1 && (
              <div
                className={clsx(
                  "flex-1 h-0.5 mx-1",
                  !isFailed && currentIdx > idx ? "bg-primary" : "bg-stone-200"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
