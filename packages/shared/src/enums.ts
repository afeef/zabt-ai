// String literal union types (compile-time only; no runtime cost)

export type MeetingStatus =
  | "pending_upload"
  | "queued"
  | "processing"
  | "completed"
  | "failed";

export type TranscriptionType = "general" | "medical";

export type MeetingSource = "upload" | "youtube" | "record";

export type MeetingType =
  | "generic"
  | "grooming"
  | "standup"
  | "retro"
  | "one_on_one";

export type StructuredOutputStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export type LayoutHint = "cards" | "table" | "columns" | "list";

export type HighlightType =
  | "action_item"
  | "key_question"
  | "topic"
  | "chapter";

export type TemplateType = "built_in" | "custom";

export type UserTier = "free" | "pro" | "enterprise";

export type OAuthProvider = "google" | "microsoft";

// Runtime arrays for validation / iteration (use these when you need a list)

export const MEETING_STATUSES: readonly MeetingStatus[] = [
  "pending_upload",
  "queued",
  "processing",
  "completed",
  "failed",
] as const;

export const TRANSCRIPTION_TYPES: readonly TranscriptionType[] = [
  "general",
  "medical",
] as const;

export const OAUTH_PROVIDERS: readonly OAuthProvider[] = [
  "google",
  "microsoft",
] as const;
