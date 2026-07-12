// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { Text, View } from "react-native";

interface Props {
  used: number;
  total: number;
}

export function UsageMeter({ used, total }: Props) {
  const pct = Math.min(100, Math.round((used / total) * 100));
  return (
    <View className="border border-border rounded-lg p-4">
      <View className="flex-row justify-between items-end mb-2">
        <Text className="text-base font-semibold text-foreground">Usage</Text>
        <Text className="text-xs text-muted-foreground">
          {used} of {total} minutes
        </Text>
      </View>
      <View className="h-2 bg-muted rounded-full overflow-hidden">
        <View
          className="h-2 bg-primary rounded-full"
          style={{ width: `${pct}%` }}
        />
      </View>
    </View>
  );
}
