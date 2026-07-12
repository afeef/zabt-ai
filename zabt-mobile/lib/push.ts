// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import Constants from "expo-constants";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
import { api } from "./api";

/**
 * Global display behavior for incoming push notifications.
 * - Show banner + play sound even when app is foregrounded.
 * - Skip badge count (we don't track unread).
 */
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

function getProjectId(): string | undefined {
  return (
    Constants.expoConfig?.extra?.eas?.projectId ??
    Constants.easConfig?.projectId
  );
}

/**
 * Request permission, obtain the Expo push token, and register it with the
 * backend (`POST /api/v1/devices`). Returns the token, or null if the user
 * denies permission or the device doesn't support push (e.g., simulator).
 *
 * Safe to call on every authenticated app launch — device registration is
 * idempotent on the backend side.
 */
export async function registerForPushNotifications(): Promise<string | null> {
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "Zabt",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#e11d74",
    });
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== "granted") {
    return null;
  }

  const projectId = getProjectId();
  const { data: token } = await Notifications.getExpoPushTokenAsync({
    projectId,
  });

  // Register with backend. Non-fatal on failure — token can be re-registered
  // on next launch.
  try {
    await api.post("/devices", {
      expo_push_token: token,
      platform: Platform.OS,
    });
  } catch (error) {
    console.warn("Failed to register device with backend", error);
  }

  return token;
}
