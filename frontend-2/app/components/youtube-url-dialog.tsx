// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState } from "react";
import { usePostHog } from "posthog-js/react";
import { Stethoscope, AudioLines } from "lucide-react";
import { isValidYoutubeUrl, isPlaylistUrl } from "@/app/lib/youtube-utils";
import { submitYoutubeUrl } from "@/app/lib/api";
import type { Meeting } from "@/app/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { useProcessingQueue } from "@/app/contexts/processing-queue-context";

interface YouTubeUrlDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (meeting: Meeting) => void;
}

export function YouTubeUrlDialog({ isOpen, onOpenChange, onSuccess }: YouTubeUrlDialogProps) {
  const posthog = usePostHog();
  const { addItem } = useProcessingQueue();
  const [url, setUrl] = useState("");
  const [transcriptionType, setTranscriptionType] = useState<"general" | "medical">("general");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    const trimmed = url.trim();

    if (!trimmed) return;

    if (isPlaylistUrl(trimmed)) {
      setError("Playlist URLs are not supported. Please paste a single video URL.");
      posthog?.capture("youtube_url_error", { error_type: "playlist" });
      return;
    }

    if (!isValidYoutubeUrl(trimmed)) {
      setError("Please enter a valid YouTube video URL");
      posthog?.capture("youtube_url_error", { error_type: "invalid_url" });
      return;
    }

    posthog?.capture("youtube_url_submitted");
    setLoading(true);
    try {
      const meeting = await submitYoutubeUrl(trimmed, transcriptionType);
      addItem(meeting.id, meeting.youtube_title || trimmed, "youtube");
      setUrl("");
      onOpenChange(false);
      onSuccess(meeting);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? "Something went wrong. Please try again.";
      setError(detail);
      posthog?.capture("youtube_url_error", { error_type: "api_error", detail });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (open) {
      posthog?.capture("youtube_dialog_opened");
    } else {
      setUrl("");
      setError(null);
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Paste YouTube URL</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Input
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) setError(null);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && url.trim() && !loading) handleSubmit();
              }}
            />
            {error && (
              <p className="text-sm text-destructive mt-2">{error}</p>
            )}
          </div>
          {/* Transcription Type Selector */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setTranscriptionType("general")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                transcriptionType === "general"
                  ? "border-primary bg-primary/10 text-primary font-medium"
                  : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50"
              }`}
            >
              <AudioLines className="size-4" />
              General
            </button>
            <button
              type="button"
              onClick={() => setTranscriptionType("medical")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                transcriptionType === "medical"
                  ? "border-primary bg-primary/10 text-primary font-medium"
                  : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50"
              }`}
            >
              <Stethoscope className="size-4" />
              Medical
            </button>
          </div>
          <div className="flex justify-end">
            <Button
              onClick={handleSubmit}
              disabled={!url.trim() || loading}
              loading={loading}
            >
              Process
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
