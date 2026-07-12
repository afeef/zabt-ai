import type { ComponentType } from "react";
import { Pressable, View } from "react-native";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Mic } from "lucide-react-native";

type IconComponent = ComponentType<{ size?: number; color?: string }>;
const MicIcon = Mic as unknown as IconComponent;

export function RecordFab() {
  const insets = useSafeAreaInsets();
  return (
    <View
      className="absolute left-1/2 -ml-7 z-10"
      style={{ bottom: 40 + insets.bottom }}
    >
      <Pressable
        onPress={() => router.push("/record")}
        className="w-14 h-14 rounded-full bg-primary items-center justify-center active:opacity-90"
      >
        <MicIcon size={24} color="#ffffff" />
      </Pressable>
    </View>
  );
}
