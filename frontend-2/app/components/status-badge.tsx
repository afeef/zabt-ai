import { Badge } from "@/app/components/ui/badge";
import { cn } from "@/app/lib/utils";
import type { Meeting } from "@/app/lib/api";
import { getUserStage, STAGE_LABELS } from "@/app/lib/stage-utils";

interface StatusBadgeProps {
  status: Meeting["status"];
  subStatus?: string | null;
}

const dotColors: Record<Meeting["status"], string> = {
  pending_upload: "bg-stone-300",
  queued: "bg-stone-400",
  processing: "bg-amber-500",
  completed: "bg-emerald-500",
  failed: "bg-red-500",
};

const badgeColors: Record<Meeting["status"], string> = {
  pending_upload: "text-stone-500",
  queued: "text-stone-600",
  processing: "text-amber-600",
  completed: "text-emerald-600",
  failed: "text-red-500",
};

const labels: Record<Meeting["status"], string> = {
  pending_upload: "Pending Upload",
  queued: "Queued",
  processing: "Processing…",
  completed: "Completed",
  failed: "Failed",
};

export function StatusBadge({ status, subStatus }: StatusBadgeProps) {
  let label = labels[status];
  if (status === "processing" && subStatus) {
    const stage = getUserStage({ status, sub_status: subStatus });
    label = STAGE_LABELS[stage];
  }

  return (
    <Badge variant="secondary" className={cn("gap-1.5", badgeColors[status])}>
      <span className={cn("size-1.5 rounded-full shrink-0", dotColors[status])} />
      {label}
    </Badge>
  );
}
