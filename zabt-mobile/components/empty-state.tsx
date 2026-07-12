import type { ComponentType } from "react";
import { Text, View } from "react-native";
import { Mic } from "lucide-react-native";

type IconComponent = ComponentType<{ size?: number; color?: string }>;
const MicIcon = Mic as unknown as IconComponent;

interface Props {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: Props) {
  return (
    <View className="flex-1 items-center justify-center px-8 py-12">
      <View className="w-16 h-16 rounded-full bg-muted items-center justify-center mb-4">
        <MicIcon size={32} color="#e11d74" />
      </View>
      <Text className="text-lg font-semibold text-foreground">{title}</Text>
      <Text className="text-sm text-muted-foreground text-center mt-2">
        {description}
      </Text>
    </View>
  );
}
