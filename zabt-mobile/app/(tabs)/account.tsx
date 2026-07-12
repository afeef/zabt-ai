import type { ComponentType } from "react";
import { ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LogOut } from "lucide-react-native";
import { router } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { UsageMeter } from "@/components/usage-meter";
import { useCurrentUser } from "@/lib/queries";
import { signOut } from "@/lib/auth";

type IconComponent = ComponentType<{ size?: number; color?: string }>;
const LogOutIcon = LogOut as unknown as IconComponent;

const QUOTA_BY_TIER: Record<string, number> = {
  free: 300,
  pro: 1200,
  enterprise: 10000,
};

export default function Account() {
  const { data: user } = useCurrentUser();
  const qc = useQueryClient();

  async function handleSignOut() {
    await signOut();
    qc.clear();
    router.replace("/(auth)/login");
  }

  return (
    <SafeAreaView className="flex-1 bg-background" edges={["top"]}>
      <ScrollView contentContainerStyle={{ padding: 16 }}>
        <View className="mb-6">
          <Text className="text-2xl font-bold text-foreground">
            {user?.full_name ?? "Welcome"}
          </Text>
          <Text className="text-sm text-muted-foreground">{user?.email}</Text>
        </View>

        {user && (
          <UsageMeter
            used={user.minutes_used_this_month}
            total={QUOTA_BY_TIER[user.tier] ?? 300}
          />
        )}

        <View className="mt-6">
          <Button variant="outline" onPress={handleSignOut}>
            <View className="flex-row items-center gap-2">
              <LogOutIcon size={16} color="#1a1510" />
              <Text className="text-sm font-medium text-foreground">
                Sign out
              </Text>
            </View>
          </Button>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
