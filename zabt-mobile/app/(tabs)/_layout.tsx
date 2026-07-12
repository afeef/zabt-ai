// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { useEffect, type ComponentType } from "react";
import { Tabs } from "expo-router";
import { Home, User } from "lucide-react-native";
import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { RecordFab } from "@/components/record-fab";
import { registerForPushNotifications } from "@/lib/push";

type TabIconProps = { color?: string; size?: number };
type IconComponent = ComponentType<TabIconProps>;

const HomeIcon = Home as unknown as IconComponent;
const UserIcon = User as unknown as IconComponent;

export default function TabsLayout() {
  const insets = useSafeAreaInsets();

  useEffect(() => {
    // Register for push notifications once the user is authenticated + in-app.
    // Backend upsert is idempotent, so calling this on every mount is safe.
    registerForPushNotifications().catch(() => {});
  }, []);

  return (
    <View className="flex-1 relative">
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: "#e11d74",
          tabBarInactiveTintColor: "#6b655c",
          tabBarStyle: {
            borderTopColor: "#e5e3de",
            borderTopWidth: 1,
            backgroundColor: "#fafaf8",
            height: 64 + insets.bottom,
            paddingBottom: 8 + insets.bottom,
            paddingTop: 8,
          },
          tabBarLabelStyle: { fontSize: 11, fontWeight: "500" },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Home",
            tabBarIcon: ({ color, size }: TabIconProps) => (
              <HomeIcon color={color} size={size} />
            ),
          }}
        />
        <Tabs.Screen
          name="account"
          options={{
            title: "Account",
            tabBarIcon: ({ color, size }: TabIconProps) => (
              <UserIcon color={color} size={size} />
            ),
          }}
        />
      </Tabs>
      <RecordFab />
    </View>
  );
}
