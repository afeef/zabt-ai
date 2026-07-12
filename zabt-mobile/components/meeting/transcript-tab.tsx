// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { Text, View } from "react-native";
import type { Meeting } from "@zabt/shared";

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface Props {
  meeting: Meeting;
}

export function TranscriptTab({ meeting }: Props) {
  const segments = meeting.segments ?? [];

  if (segments.length === 0) {
    return (
      <View className="py-8 items-center">
        <Text className="text-sm text-muted-foreground text-center">
          {meeting.status === "processing"
            ? "Transcription in progress…"
            : meeting.status === "failed"
            ? "Transcription failed."
            : "No transcript available"}
        </Text>
      </View>
    );
  }

  return (
    <View className="gap-4">
      {segments.map((seg, idx) => (
        <View key={idx}>
          <View className="flex-row items-center gap-2 mb-1">
            <Text className="text-xs font-semibold text-foreground">
              {seg.speaker || "Unknown"}
            </Text>
            <Text className="font-mono text-xs text-muted-foreground">
              {fmt(seg.start)}
            </Text>
          </View>
          <Text className="text-sm text-foreground leading-5">{seg.text}</Text>
        </View>
      ))}
    </View>
  );
}
