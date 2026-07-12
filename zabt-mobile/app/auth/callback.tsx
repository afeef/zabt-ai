// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { router, useLocalSearchParams } from "expo-router";
import { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";
import { supabase } from "@/lib/supabase";

export default function AuthCallback() {
  const { code, error: oauthError } = useLocalSearchParams<{
    code?: string;
    error?: string;
  }>();

  useEffect(() => {
    (async () => {
      // If signInWithProvider() already exchanged the code via the WebBrowser
      // callback, a session exists and we just route home. Otherwise the OS
      // deep-linked us here first; do the exchange ourselves.
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        router.replace("/(tabs)");
        return;
      }
      if (oauthError || !code) {
        router.replace("/(auth)/login");
        return;
      }
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      router.replace(error ? "/(auth)/login" : "/(tabs)");
    })();
  }, [code, oauthError]);

  return (
    <View className="flex-1 items-center justify-center bg-background">
      <ActivityIndicator />
    </View>
  );
}
