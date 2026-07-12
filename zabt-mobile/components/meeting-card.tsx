// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { memo } from "react";
import { Pressable, Text, View } from "react-native";
import { router } from "expo-router";
import type { Meeting } from "@zabt/shared";
import { stripMarkdown } from "@/lib/markdown";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const mins = Math.floor(seconds / 60);
  return `${mins} min`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

interface Props {
  meeting: Meeting;
}

export const MeetingCard = memo(function MeetingCard({ meeting }: Props) {
  const isProcessing =
    meeting.status !== "completed" && meeting.status !== "failed";
  return (
    <Pressable
      onPress={() => router.push(`/meeting/${meeting.id}`)}
      className="bg-background border border-border rounded-lg p-4 active:bg-muted"
    >
      <View className="flex-row justify-between items-start">
        <Text
          className="text-base font-semibold text-foreground flex-1"
          numberOfLines={2}
        >
          {meeting.title}
        </Text>
        {isProcessing && (
          <Text className="text-xs text-primary ml-2">Processing…</Text>
        )}
      </View>
      <Text className="text-xs text-muted-foreground mt-1">
        {formatDate(meeting.created_at)} ·{" "}
        {formatDuration(meeting.duration_seconds)}
      </Text>
      {meeting.summary_text && (
        <Text
          className="text-sm text-muted-foreground mt-2"
          numberOfLines={2}
        >
          {stripMarkdown(meeting.summary_text)}
        </Text>
      )}
    </Pressable>
  );
}, (prev, next) => {
  const a = prev.meeting;
  const b = next.meeting;
  return (
    a.id === b.id &&
    a.title === b.title &&
    a.status === b.status &&
    a.duration_seconds === b.duration_seconds &&
    a.summary_text === b.summary_text
  );
});
