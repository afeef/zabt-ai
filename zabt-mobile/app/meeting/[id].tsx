// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { useEffect, useState } from "react";
import type { ComponentType } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { ArrowLeft } from "lucide-react-native";
import { AiChatTab } from "@/components/meeting/ai-chat-tab";
import { SummaryTab } from "@/components/meeting/summary-tab";
import { TranscriptTab } from "@/components/meeting/transcript-tab";
import { StatusBanner } from "@/components/status-banner";
import { track } from "@/lib/analytics";
import { useMeeting } from "@/lib/queries";

type IconComponent = ComponentType<{ size?: number; color?: string }>;
const ArrowLeftIcon = ArrowLeft as unknown as IconComponent;

type Tab = "summary" | "transcript" | "chat";

interface TabButtonProps {
  label: string;
  active: boolean;
  onPress: () => void;
}

function TabButton({ label, active, onPress }: TabButtonProps) {
  return (
    <Pressable onPress={onPress} className="flex-1 py-3 items-center">
      <Text
        className={
          active
            ? "text-primary font-semibold text-sm"
            : "text-muted-foreground text-sm"
        }
      >
        {label}
      </Text>
      {active && (
        <View className="absolute bottom-0 h-0.5 bg-primary w-full" />
      )}
    </Pressable>
  );
}

export default function MeetingDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: meeting, isLoading } = useMeeting(id);
  const [tab, setTab] = useState<Tab>("summary");

  useEffect(() => {
    if (meeting?.id) {
      track("mobile_meeting_viewed", { meeting_id: meeting.id });
    }
  }, [meeting?.id]);

  if (isLoading) {
    return (
      <SafeAreaView className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator color="#e11d74" />
      </SafeAreaView>
    );
  }

  if (!meeting) {
    return (
      <SafeAreaView className="flex-1 bg-background">
        <View className="flex-row items-center px-4 py-3 border-b border-border">
          <Pressable onPress={() => router.back()} hitSlop={12}>
            <ArrowLeftIcon size={24} color="#1a1510" />
          </Pressable>
        </View>
        <Text className="text-center mt-10 text-muted-foreground">
          Meeting not found
        </Text>
      </SafeAreaView>
    );
  }

  const durationMinutes = Math.floor((meeting.duration_seconds ?? 0) / 60);

  return (
    <SafeAreaView className="flex-1 bg-background" edges={["top"]}>
      <View className="flex-row items-center gap-3 px-4 py-3 border-b border-border">
        <Pressable onPress={() => router.back()} hitSlop={12}>
          <ArrowLeftIcon size={24} color="#1a1510" />
        </Pressable>
        <View className="flex-1">
          <Text
            className="text-base font-semibold text-foreground"
            numberOfLines={1}
          >
            {meeting.title}
          </Text>
          <Text className="text-xs text-muted-foreground">
            {new Date(meeting.created_at).toLocaleDateString()} ·{" "}
            {durationMinutes} min
          </Text>
        </View>
      </View>

      <StatusBanner meeting={meeting} />

      <View className="flex-row border-b border-border">
        <TabButton
          label="Summary"
          active={tab === "summary"}
          onPress={() => setTab("summary")}
        />
        <TabButton
          label="Transcript"
          active={tab === "transcript"}
          onPress={() => setTab("transcript")}
        />
        <TabButton
          label="AI Chat"
          active={tab === "chat"}
          onPress={() => setTab("chat")}
        />
      </View>

      <ScrollView className="flex-1" contentContainerStyle={{ padding: 16 }}>
        {tab === "summary" && <SummaryTab meeting={meeting} />}
        {tab === "transcript" && <TranscriptTab meeting={meeting} />}
        {tab === "chat" && <AiChatTab />}
      </ScrollView>
    </SafeAreaView>
  );
}
