import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, Pressable, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router } from "expo-router";
import * as Linking from "expo-linking";
import { Pause, Play, Square, X } from "lucide-react-native";
import type { ComponentType } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Waveform } from "@/components/waveform";
import { track } from "@/lib/analytics";
import {
  ZABT_VOICE_PRESET,
  configureAudioSession,
  requestMicPermission,
  useAudioRecorder,
  useAudioRecorderState,
} from "@/lib/recording";
import { uploadMeetingRecording } from "@/lib/upload";

type IconComponent = ComponentType<{
  size?: number;
  color?: string;
  fill?: string;
}>;
const XIcon = X as unknown as IconComponent;
const PauseIcon = Pause as unknown as IconComponent;
const PlayIcon = Play as unknown as IconComponent;
const SquareIcon = Square as unknown as IconComponent;

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/**
 * expo-audio `metering` is dBFS (-160..0). Normalise to 0..1 for the waveform.
 * -60dB ≈ quiet room, 0dB = clipping. Clamp for sanity.
 */
function normaliseMetering(dbfs: number | undefined): number {
  if (dbfs === undefined || !Number.isFinite(dbfs)) return 0.1;
  const clamped = Math.max(-60, Math.min(0, dbfs));
  return (clamped + 60) / 60;
}

export default function Record() {
  const recorder = useAudioRecorder(ZABT_VOICE_PRESET);
  const state = useAudioRecorderState(recorder, 100); // 10Hz metering
  const [isPaused, setIsPaused] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFraction, setUploadFraction] = useState(0);
  const started = useRef(false);
  const qc = useQueryClient();

  useEffect(() => {
    (async () => {
      const granted = await requestMicPermission();
      if (!granted) {
        Alert.alert(
          "Microphone access required",
          "Enable mic access in Settings to record meetings.",
          [
            { text: "Cancel", style: "cancel", onPress: () => router.back() },
            { text: "Open Settings", onPress: () => Linking.openSettings() },
          ]
        );
        return;
      }
      await configureAudioSession();
      await recorder.prepareToRecordAsync();
      await recorder.record();
      started.current = true;
      track("mobile_record_started");
    })();
    return () => {
      if (started.current) {
        recorder.stop().catch(() => {});
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handlePauseResume() {
    if (isPaused) {
      await recorder.record();
      setIsPaused(false);
    } else {
      await recorder.pause();
      setIsPaused(true);
    }
  }

  async function handleStop() {
    await recorder.stop();
    const uri = recorder.uri;
    if (!uri) {
      Alert.alert("Recording failed", "No audio captured.");
      router.back();
      return;
    }

    const durationSec = Math.floor(state.durationMillis / 1000);
    track("mobile_record_completed", { duration_seconds: durationSec });

    setUploading(true);
    try {
      const { meetingId } = await uploadMeetingRecording(
        uri,
        setUploadFraction
      );
      track("mobile_upload_completed", { meeting_id: meetingId });
      // Invalidate the meetings list so Home shows the new meeting on return.
      qc.invalidateQueries({ queryKey: ["meetings"] });
      router.replace(`/meeting/${meetingId}`);
    } catch (error) {
      track("mobile_upload_failed", {
        error: error instanceof Error ? error.message : "unknown",
      });
      Alert.alert(
        "Upload failed",
        error instanceof Error
          ? error.message
          : "Try again from the home screen."
      );
      router.back();
    } finally {
      setUploading(false);
    }
  }

  function handleCancel() {
    recorder.stop().catch(() => {});
    router.back();
  }

  const durationSeconds = state.durationMillis / 1000;
  const level = normaliseMetering(state.metering);

  if (uploading) {
    const pct = Math.round(uploadFraction * 100);
    return (
      <SafeAreaView className="flex-1 bg-background" edges={["top", "bottom"]}>
        <View className="flex-1 items-center justify-center px-8">
          <ActivityIndicator size="large" color="#e11d74" />
          <Text className="font-mono text-6xl font-bold text-foreground mt-8">
            {pct}%
          </Text>
          <Text className="text-base font-medium text-foreground mt-6">
            Uploading recording…
          </Text>
          <View className="w-full h-2 bg-muted rounded-full overflow-hidden mt-4 max-w-xs">
            <View
              className="h-full bg-primary"
              style={{ width: `${pct}%` }}
            />
          </View>
          <Text className="text-sm text-muted-foreground text-center mt-6">
            Keep the app open until this finishes.{"\n"}
            We'll take you to your meeting when it's done.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-background" edges={["top", "bottom"]}>
      <View className="flex-row justify-between items-center px-6 pt-4">
        <Pressable onPress={handleCancel} hitSlop={12} disabled={uploading}>
          <XIcon size={24} color="#1a1510" />
        </Pressable>
        <Text className="text-sm text-muted-foreground">
          {uploading
            ? "Uploading"
            : isPaused
            ? "Paused"
            : state.isRecording
            ? "Recording"
            : "Preparing"}
        </Text>
        <View className="w-6" />
      </View>

      <View className="flex-1 items-center justify-center px-6">
        <Text className="font-mono text-5xl font-bold text-foreground mb-8">
          {formatDuration(durationSeconds)}
        </Text>
        <Waveform isRecording={state.isRecording && !isPaused} level={level} />
      </View>

      <View className="flex-row items-center justify-center gap-6 pb-8">
        <Pressable
          onPress={handlePauseResume}
          disabled={uploading}
          className="w-16 h-16 rounded-full border border-border items-center justify-center active:bg-muted disabled:opacity-50"
        >
          {isPaused ? (
            <PlayIcon size={24} color="#1a1510" />
          ) : (
            <PauseIcon size={24} color="#1a1510" />
          )}
        </Pressable>
        <Pressable
          onPress={handleStop}
          disabled={uploading}
          className="w-20 h-20 rounded-full bg-destructive items-center justify-center active:opacity-90 disabled:opacity-50"
        >
          <SquareIcon size={28} color="#ffffff" fill="#ffffff" />
        </Pressable>
      </View>
    </SafeAreaView>
  );
}
