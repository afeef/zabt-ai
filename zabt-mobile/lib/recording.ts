// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import {
  AudioQuality,
  IOSOutputFormat,
  RecordingPresets,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
  type RecordingOptions,
} from "expo-audio";

/**
 * Voice-optimized recording preset — mono 64kbps AAC.
 * Meetings are speech, not music. Halving the channel count + bitrate roughly
 * quarters the file size without impacting transcription quality.
 */
export const ZABT_VOICE_PRESET: RecordingOptions = {
  ...RecordingPresets.HIGH_QUALITY,
  isMeteringEnabled: true,
  numberOfChannels: 1,
  bitRate: 64_000,
  sampleRate: 44_100,
  android: {
    ...RecordingPresets.HIGH_QUALITY.android,
    outputFormat: "mpeg4",
    audioEncoder: "aac",
  },
  ios: {
    ...RecordingPresets.HIGH_QUALITY.ios,
    outputFormat: IOSOutputFormat.MPEG4AAC,
    audioQuality: AudioQuality.HIGH,
  },
};

/**
 * Configure the global audio session for foreground + background recording.
 * Call once at record-screen mount before starting the recorder.
 */
export async function configureAudioSession(): Promise<void> {
  await setAudioModeAsync({
    allowsRecording: true,
    playsInSilentMode: true,
    shouldRouteThroughEarpiece: false,
    interruptionMode: "doNotMix",
    shouldPlayInBackground: true,
  });
}

/**
 * Request microphone permission. Returns true if granted.
 */
export async function requestMicPermission(): Promise<boolean> {
  const { granted } = await requestRecordingPermissionsAsync();
  return granted;
}

export { useAudioRecorder, useAudioRecorderState };
