import "react-native-url-polyfill/auto";
import "../global.css";
import "react-native-reanimated";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Constants from "expo-constants";
import * as Notifications from "expo-notifications";
import { router, Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import * as Sentry from "@sentry/react-native";

// Sentry init — DSN optional, guards against missing env in dev.
const sentryDsn = process.env.EXPO_PUBLIC_SENTRY_DSN;
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    tracesSampleRate: 1.0,
    release: `zabt-mobile@${Constants.expoConfig?.version ?? "0.1.0"}`,
  });
}

const defaultClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      gcTime: 5 * 60 * 1000,
      retry: 2,
    },
  },
});

function RootLayout() {
  const [client] = useState(() => defaultClient);

  useEffect(() => {
    // Deep-link to the meeting when a push notification is tapped.
    const sub = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        const meetingId =
          response.notification.request.content.data?.meeting_id;
        if (meetingId !== undefined && meetingId !== null) {
          router.push(`/meeting/${meetingId}`);
        }
      }
    );
    return () => sub.remove();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={client}>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="record"
            options={{ presentation: "modal", headerShown: false }}
          />
          <Stack.Screen name="meeting/[id]" options={{ headerShown: false }} />
        </Stack>
        <StatusBar style="dark" />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}

export default Sentry.wrap(RootLayout);
