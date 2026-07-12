// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { Text, View } from "react-native";

interface Props {
  visible: boolean;
  fraction: number;
  label?: string;
}

export function UploadBanner({ visible, fraction, label = "Uploading" }: Props) {
  if (!visible) return null;
  const pct = Math.round(fraction * 100);
  return (
    <View className="absolute top-0 left-0 right-0 z-20 bg-primary px-4 py-2">
      <Text className="text-xs text-primary-foreground text-center">
        {label} — {pct}%
      </Text>
      <View className="h-1 bg-primary-foreground/20 rounded mt-1 overflow-hidden">
        <View
          className="h-1 bg-primary-foreground rounded"
          style={{ width: `${pct}%` }}
        />
      </View>
    </View>
  );
}
