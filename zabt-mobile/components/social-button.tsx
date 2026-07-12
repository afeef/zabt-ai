// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { ComponentType } from "react";
import { Pressable, Text, View } from "react-native";
import { Mail, Building2 } from "lucide-react-native";
import { cn } from "@/lib/utils";

interface Props {
  provider: "google" | "microsoft";
  label: string;
  onPress: () => void;
  disabled?: boolean;
}

type IconComponent = ComponentType<{ size?: number; color?: string }>;

const ICONS: Record<"google" | "microsoft", IconComponent> = {
  google: Mail as unknown as IconComponent,         // placeholder — swap with brand SVG in Phase K polish
  microsoft: Building2 as unknown as IconComponent, // placeholder — swap with brand SVG in Phase K polish
};

export function SocialButton({ provider, label, onPress, disabled }: Props) {
  const Icon = ICONS[provider];
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      className={cn(
        "h-12 flex-row items-center justify-center gap-3 rounded-lg border border-border bg-background active:bg-muted",
        disabled && "opacity-50"
      )}
    >
      <View className="w-5 h-5">
        <Icon size={20} color="#1a1510" />
      </View>
      <Text className="text-sm font-medium text-foreground">{label}</Text>
    </Pressable>
  );
}
