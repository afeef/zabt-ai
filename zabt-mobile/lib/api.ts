// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { createApiClient } from "@zabt/shared";
import { router } from "expo-router";
import { supabase } from "./supabase";

const API_URL = process.env.EXPO_PUBLIC_API_URL!;

if (!API_URL) {
  throw new Error("EXPO_PUBLIC_API_URL must be set.");
}

export const api = createApiClient({
  baseURL: API_URL,
  getAuthToken: async () => {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  },
  onUnauthorized: async () => {
    await supabase.auth.signOut();
    router.replace("/(auth)/login");
  },
});
