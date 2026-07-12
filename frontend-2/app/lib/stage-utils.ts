import type { Meeting } from "@/app/lib/api";

export type UserStage = "uploaded" | "transcribing" | "aligning" | "diarizing" | "summarizing" | "done" | "failed";

export const STAGE_ORDER: UserStage[] = [
  "uploaded",
  "transcribing",
  "aligning",
  "diarizing",
  "summarizing",
  "done",
];

export const STAGE_LABELS: Record<UserStage, string> = {
  uploaded: "Uploaded",
  transcribing: "Transcribing…",
  aligning: "Aligning…",
  diarizing: "Diarizing…",
  summarizing: "Summarizing…",
  done: "Done",
  failed: "Failed",
};

/**
 * Map a Meeting's `status` + `sub_status` to a user-visible stage.
 */
export function getUserStage(meeting: Pick<Meeting, "status" | "sub_status">): UserStage {
  if (meeting.status === "failed") return "failed";
  if (meeting.status === "completed") return "done";
  if (meeting.status === "pending_upload" || meeting.status === "queued") return "uploaded";

  // status === "processing"
  switch (meeting.sub_status) {
    case "downloading":
    case "downloading_youtube":
    case "validating":
    case "extracting_audio":
      return "uploaded";
    case "uploading":
    case "transcribing":
      return "transcribing";
    case "aligning":
      return "aligning";
    case "diarizing":
    case "parsing":
      return "diarizing";
    case "summarizing":
      return "summarizing";
    case "cleaning_up":
      return "done";
    default:
      return "uploaded";
  }
}

/**
 * Get the index of a stage in the pipeline order (0-based).
 * Returns -1 for "failed" since it's not in the linear pipeline.
 */
export function getStageIndex(stage: UserStage): number {
  const idx = STAGE_ORDER.indexOf(stage);
  return idx;
}

/**
 * Check if a meeting is in an active (processing) state.
 */
export function isActiveMeeting(meeting: Pick<Meeting, "status">): boolean {
  return meeting.status === "pending_upload"
    || meeting.status === "queued"
    || meeting.status === "processing";
}
