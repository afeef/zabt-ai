// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { Meeting } from "@zabt/shared";

export type UserStage =
  | "uploaded"
  | "transcribing"
  | "aligning"
  | "diarizing"
  | "summarizing"
  | "done"
  | "failed";

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

export function getUserStage(
  meeting: Pick<Meeting, "status" | "sub_status">
): UserStage {
  if (meeting.status === "failed") return "failed";
  if (meeting.status === "completed") return "done";
  if (meeting.status === "pending_upload" || meeting.status === "queued") {
    return "uploaded";
  }
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

export function isActiveMeeting(
  meeting: Pick<Meeting, "status">
): boolean {
  return (
    meeting.status === "pending_upload" ||
    meeting.status === "queued" ||
    meeting.status === "processing"
  );
}
