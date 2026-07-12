// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import PostHog from "posthog-react-native";

const posthogKey = process.env.EXPO_PUBLIC_POSTHOG_KEY;

export const posthog = posthogKey
  ? new PostHog(posthogKey, {
      host: "https://us.i.posthog.com",
      captureAppLifecycleEvents: true,
    })
  : null;

/**
 * PostHog event properties are strictly JSON-serialisable. The `as never` is a
 * cast of convenience — our call sites only pass plain values, so this is safe
 * at runtime.
 */
type EventProps = Record<string, string | number | boolean | null | undefined>;

/** Fire-and-forget analytics event. Silent if PostHog isn't configured. */
export function track(event: string, properties?: EventProps): void {
  try {
    posthog?.capture(event, properties as never);
  } catch {
    // swallow — analytics must never break the app
  }
}
