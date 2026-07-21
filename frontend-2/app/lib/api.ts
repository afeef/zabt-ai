// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import axios from "axios";
import { createApiClient } from "@zabt/shared";
import type {
  AuthToken,
  Meeting,
  MeetingHighlight,
  MeetingList,
  MeetingType,
  OAuthProvider,
  SSOLookupRequest,
  SSOLookupResponse,
  SpeakerBreakdown,
  SummaryTemplate,
  SummaryTemplateListItem,
  TranscriptSegment,
  TranscriptWord,
  User,
} from "@zabt/shared";
import { createClient } from "@/app/lib/supabase/client";

// Re-export for internal consumers that import from @/app/lib/api
export type {
  AuthToken,
  Meeting,
  MeetingHighlight,
  MeetingList,
  MeetingType,
  OAuthProvider,
  SSOLookupRequest,
  SSOLookupResponse,
  SpeakerBreakdown,
  SummaryTemplate,
  SummaryTemplateListItem,
  TranscriptSegment,
  TranscriptWord,
  User,
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ── Token helpers (Supabase manages sessions; these read from its session) ────

export const getToken = async (): Promise<string | null> => {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
};

export const clearToken = async (): Promise<void> => {
  const supabase = createClient();
  await supabase.auth.signOut();
};

// ── Axios client ──────────────────────────────────────────────────────────────

const apiClient = createApiClient({
  baseURL: API_URL,
  getAuthToken: async () => {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  },
  onUnauthorized: async () => {
    if (typeof window !== "undefined") {
      const supabase = createClient();
      await supabase.auth.signOut();
      window.location.href = "/login";
    }
  },
});

// ── Auth (all via Supabase — no backend auth routes) ─────────────────────────

const FRONTEND_URL =
  process.env.NEXT_PUBLIC_FRONTEND_URL || "http://localhost:3000";

export const socialLoginUrl = (
  provider: OAuthProvider,
  _state: string
): string => {
  // Supabase OAuth redirects are initiated imperatively via signInWithOAuth.
  // This helper now returns a dummy string; prefer calling socialLogin() directly.
  return `#oauth-${provider}`;
};

/** Trigger Supabase OAuth sign-in for a given provider (redirect flow). */
export const socialLogin = async (provider: OAuthProvider): Promise<void> => {
  const supabase = createClient();
  const providerMap: Record<OAuthProvider, "google" | "azure"> = {
    google: "google",
    microsoft: "azure",
  };
  const scopesMap: Record<OAuthProvider, string | undefined> = {
    google: undefined,
    microsoft: "openid email profile",
  };
  await supabase.auth.signInWithOAuth({
    provider: providerMap[provider],
    options: {
      redirectTo: `${FRONTEND_URL}/auth/callback/${provider}`,
      scopes: scopesMap[provider],
    },
  });
};

/** SSO lookup — Supabase handles SSO via OAuth providers natively. */
export const ssoLookup = async (_email: string): Promise<SSOLookupResponse> => {
  return { sso_enabled: false, redirect_url: null, organisation_name: null };
};

export const loginWithRememberMe = async (
  email: string,
  password: string,
  _rememberMe: boolean  // Supabase manages session persistence automatically
): Promise<void> => {
  const supabase = createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
};

export const register = async (
  email: string,
  password: string,
  fullName: string
): Promise<void> => {
  const supabase = createClient();
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { full_name: fullName } },
  });
  if (error) throw error;
};

export const login = async (email: string, password: string): Promise<void> => {
  const supabase = createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
};

// ── Styles ────────────────────────────────────────────────────────────────────

export const uploadStyle = async (file: File): Promise<string[]> => {
  const formData = new FormData();
  formData.append("files", file);
  const res = await apiClient.post<string[]>("/styles/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const getStyles = async (): Promise<string[]> => {
  try {
    const res = await apiClient.get<string[]>("/styles/");
    return res.data;
  } catch {
    return [];
  }
};

// ── Meetings ──────────────────────────────────────────────────────────────────

interface PresignedUploadResponse {
  upload_url: string;
  file_key: string;
  storage_provider: string;
}

export const uploadMeeting = async (
  file: File,
  title: string = "Untitled Meeting",
  description?: string
): Promise<Meeting> => {
  // 1. Get Presigned URL
  const { data: presignedData } = await apiClient.post<PresignedUploadResponse>("/meetings/presigned-upload", {
    filename: file.name,
    content_type: file.type || "audio/mpeg"
  });

  // 2. Create the meeting record (before upload so webhook can find it)
  const { data: meeting } = await apiClient.post<Meeting>("/meetings/", {
    title,
    description,
    file_key: presignedData.file_key
  });

  // 3. Upload directly to S3/MinIO
  await axios.put(presignedData.upload_url, file, {
    headers: {
      "Content-Type": file.type || "audio/mpeg"
    }
  });

  // 4. For S3/R2: confirm upload to trigger pipeline (MinIO uses webhooks instead)
  if (presignedData.storage_provider === "s3") {
    await apiClient.post(`/meetings/${meeting.id}/confirm-upload`);
  }

  return meeting;
};

export const submitYoutubeUrl = async (url: string, transcriptionType: string = "general"): Promise<Meeting> => {
  const res = await apiClient.post<Meeting>("/meetings/youtube", { url, transcription_type: transcriptionType });
  return res.data;
};

export const getMeetings = async (
  skip = 0,
  limit = 20
): Promise<Meeting[]> => {
  const res = await apiClient.get<Meeting[]>(
    `/meetings/?skip=${skip}&limit=${limit}`
  );
  return res.data;
};


export const getMeeting = async (id: number): Promise<Meeting> => {
  const res = await apiClient.get<Meeting>(`/meetings/${id}`);
  return res.data;
};

export const deleteMeeting = async (id: number): Promise<void> => {
  await apiClient.delete(`/meetings/${id}`);
};

export const updateMeetingSummary = async (
  meetingId: number,
  summaryText: string
): Promise<{ id: number; summary_text: string; original_summary_text: string | null; summary_edited: boolean }> => {
  const res = await apiClient.patch(`/meetings/${meetingId}/summary`, {
    summary_text: summaryText,
  });
  return res.data;
};

export const restoreMeetingSummary = async (
  meetingId: number
): Promise<{ id: number; summary_text: string; original_summary_text: string | null; summary_edited: boolean }> => {
  const res = await apiClient.post(`/meetings/${meetingId}/summary/restore`);
  return res.data;
};

export const resummarizeMeeting = async (
  meetingId: number,
  templateId?: number
): Promise<void> => {
  await apiClient.post(`/meetings/${meetingId}/summarize`, {
    template_id: templateId ?? null,
  });
};

// ── Templates ─────────────────────────────────────────────────────────────────

export const getTemplates = async (): Promise<SummaryTemplate[]> => {
  const res = await apiClient.get<SummaryTemplate[]>("/templates/");
  return res.data;
};

export const getTemplate = async (id: number): Promise<SummaryTemplate> => {
  const res = await apiClient.get<SummaryTemplate>(`/templates/${id}`);
  return res.data;
};

export const createTemplate = async (
  name: string,
  body: string
): Promise<SummaryTemplate> => {
  const res = await apiClient.post<SummaryTemplate>("/templates/", { name, body });
  return res.data;
};

export const updateTemplate = async (
  id: number,
  name: string,
  body: string
): Promise<SummaryTemplate> => {
  const res = await apiClient.put<SummaryTemplate>(`/templates/${id}`, { name, body });
  return res.data;
};

export const deleteTemplate = async (id: number): Promise<void> => {
  await apiClient.delete(`/templates/${id}`);
};

export const setDefaultTemplate = async (
  id: number
): Promise<{ default_template_id: number; default_template_name: string }> => {
  const res = await apiClient.post(`/templates/${id}/set-default`);
  return res.data;
};

// ── PDF Export ───────────────────────────────────────────────────────────────

export const exportPdf = async (
  meetingId: number,
  type: "summary" | "transcript"
): Promise<void> => {
  const res = await apiClient.get(`/meetings/${meetingId}/export/pdf`, {
    params: { type },
    responseType: "blob",
  });

  // Parse filename from Content-Disposition header, fallback to default
  const disposition = res.headers["content-disposition"] || "";
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch?.[1] || `meeting-${type}.pdf`;

  // Create a temporary object URL and trigger download
  const blob = new Blob([res.data], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// ── Integrations ────────────────────────────────────────────────────────────

export interface IntegrationRead {
  id: number;
  provider: "microsoft" | "google";
  provider_email: string | null;
  status: "active" | "expired" | "revoked";
  connected_at: string;
  scopes: string[];
}

export const getIntegrations = async (): Promise<IntegrationRead[]> => {
  const { data } = await apiClient.get("/integrations/");
  return data;
};

export const connectProvider = async (provider: string): Promise<{ auth_url: string }> => {
  const { data } = await apiClient.post(`/integrations/${provider}/connect`);
  return data;
};

export const disconnectProvider = async (provider: string): Promise<void> => {
  await apiClient.delete(`/integrations/${provider}`);
};

// ── Email Sharing ───────────────────────────────────────────────────────────

export interface EmailShareRead {
  id: number;
  meeting_id: number;
  recipients: { email: string; name: string; status: string }[];
  status: "pending" | "sent" | "partially_failed" | "failed";
  sent_at: string | null;
  created_at: string;
}

export const shareMeetingViaEmail = async (
  meetingId: number,
  recipientEmails: string[]
): Promise<EmailShareRead> => {
  const { data } = await apiClient.post(`/meetings/${meetingId}/share-email`, {
    recipient_emails: recipientEmails,
  });
  return data;
};

export const getMeetingShares = async (
  meetingId: number
): Promise<EmailShareRead[]> => {
  const { data } = await apiClient.get(`/meetings/${meetingId}/shares`);
  return data;
};

// ── Meeting Intelligence ──────────────────────────────────────────────────────

export async function updateMeetingType(meetingId: number, meetingType: MeetingType) {
  return apiClient.patch(`/meetings/${meetingId}/meeting-type`, { meeting_type: meetingType });
}

export async function reExtractIntelligence(meetingId: number) {
  return apiClient.post(`/meetings/${meetingId}/re-extract`);
}

export async function getMeetingHighlights(meetingId: number, highlightType?: string) {
  const params = highlightType ? { highlight_type: highlightType } : {};
  return apiClient.get<MeetingHighlight[]>(`/meetings/${meetingId}/highlights`, { params });
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/users/me");
  return data;
}

// ── Languages ─────────────────────────────────────────────────────────────────

export type LanguageEntry = {
  code: string;
  display_name: string;
  whisper_lang: string;
  script: string;
  transliterate_from: string | null;
  is_default: boolean;
};

export async function listLanguages(): Promise<LanguageEntry[]> {
  const { data } = await apiClient.get<LanguageEntry[]>("/languages");
  return data;
}

export async function getLanguagePreferences(): Promise<string[]> {
  const { data } = await apiClient.get<{ codes: string[] }>(
    "/users/me/language-preferences"
  );
  return data.codes;
}

export async function setLanguagePreferences(codes: string[]): Promise<string[]> {
  const { data } = await apiClient.put<{ codes: string[] }>(
    "/users/me/language-preferences",
    { codes }
  );
  return data.codes;
}

export async function reTranscribeMeeting(
  meetingId: number,
  language: string
): Promise<void> {
  await apiClient.post(`/meetings/${meetingId}/re-transcribe`, { language });
}

export default apiClient;
