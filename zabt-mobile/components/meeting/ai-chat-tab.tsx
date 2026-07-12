// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { Text, View } from "react-native";
import { Sparkles } from "lucide-react-native";
import type { ComponentType } from "react";

type IconComponent = ComponentType<{ size?: number; color?: string }>;
const SparklesIcon = Sparkles as unknown as IconComponent;

/**
 * AI Chat is not yet wired — backend doesn't expose a /meetings/{id}/chat
 * endpoint. Showing a clean "coming soon" state rather than a non-functional
 * prompt input. Wire up when the backend ships the endpoint.
 */
export function AiChatTab() {
  return (
    <View className="py-12 items-center">
      <View className="w-16 h-16 rounded-full bg-muted items-center justify-center mb-4">
        <SparklesIcon size={28} color="#e11d74" />
      </View>
      <Text className="text-lg font-semibold text-foreground">AI Chat</Text>
      <Text className="text-sm text-muted-foreground text-center mt-2 max-w-xs">
        Ask questions about this meeting. Coming in a future release.
      </Text>
    </View>
  );
}
