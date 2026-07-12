// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
// Transcript primitives

export interface TranscriptWord {
  word: string;
  start: number;
  end: number;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  speaker: string;
  text: string;
  words: TranscriptWord[];
}

export interface SpeakerBreakdown {
  percentage: number;
  name: string;
}

// Meeting

export interface Meeting {
  id: number;
  title: string;
  description: string | null;
  file_path: string;
  duration_seconds: number | null;
  created_at: string;
  status: MeetingStatus;
  sub_status: string | null;
  transcript_text: string | null;
  summary_text: string | null;
  original_summary_text: string | null;
  summary_edited: boolean;
  action_items_text: string | null;
  template_id: number | null;
  template_name: string | null;
  transcription_type: TranscriptionType;
  source_type: MeetingSource;
  source_url: string | null;
  youtube_title: string | null;
  youtube_duration_seconds: number | null;
  youtube_thumbnail_url: string | null;
  youtube_channel: string | null;
  audio_url: string | null;
  speakers?: Record<string, SpeakerBreakdown>;
  segments?: TranscriptSegment[];
  meeting_type: MeetingType;
  structured_output: Record<string, unknown> | null;
  structured_output_status: StructuredOutputStatus;
  highlights: MeetingHighlight[];
  layout_hint: LayoutHint;
  requested_language: string | null;
  transliterated_text: string | null;
}

export interface MeetingList {
  items: Meeting[];
  total: number;
  skip: number;
  limit: number;
}

export interface MeetingHighlight {
  id: number;
  meeting_id: number;
  highlight_type: HighlightType;
  content: string;
  speaker: string | null;
  timestamp_start: number;
  timestamp_end: number | null;
  ai_answer: string | null;
  metadata: Record<string, unknown> | null;
  sort_order: number;
}

// Summary templates

export interface SummaryTemplate {
  id: number;
  name: string;
  body: string;
  template_type: TemplateType;
  is_system_default: boolean;
  owner_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SummaryTemplateListItem {
  id: number;
  name: string;
  template_type: TemplateType;
  is_system_default: boolean;
}

// User + Auth

export interface User {
  email: string;
  full_name: string | null;
  tier: UserTier;
  is_active: boolean;
  minutes_used_this_month: number;
}

export interface AuthToken {
  access_token: string;
  token_type: "bearer";
}

export interface SSOLookupRequest {
  email: string;
}

export interface SSOLookupResponse {
  sso_enabled: boolean;
  redirect_url: string | null;
  organisation_name: string | null;
}

// Forward references — string literal types defined in enums.ts
import type {
  MeetingStatus,
  TranscriptionType,
  MeetingSource,
  MeetingType,
  StructuredOutputStatus,
  LayoutHint,
  HighlightType,
  TemplateType,
  UserTier,
} from "./enums";
