// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { useEffect, useState } from "react";
import { View } from "react-native";

interface Props {
  isRecording: boolean;
  /** Normalised amplitude 0..1 (from expo-audio `metering` dBFS, re-scaled). */
  level: number;
}

const BAR_COUNT = 32;
const MIN_LEVEL = 0.08;

export function Waveform({ isRecording, level }: Props) {
  const [bars, setBars] = useState<number[]>(() =>
    new Array(BAR_COUNT).fill(MIN_LEVEL)
  );

  useEffect(() => {
    if (!isRecording) return;
    setBars((prev) => [...prev.slice(1), Math.max(MIN_LEVEL, level)]);
  }, [level, isRecording]);

  return (
    <View className="flex-row items-end justify-center gap-1 h-24">
      {bars.map((value, i) => (
        <View
          key={i}
          className="w-2 rounded-full bg-primary"
          style={{ height: `${value * 100}%`, minHeight: 4 }}
        />
      ))}
    </View>
  );
}
