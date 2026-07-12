// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { Session } from "@supabase/supabase-js";
import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import { useEffect, useState } from "react";
import { supabase } from "./supabase";

WebBrowser.maybeCompleteAuthSession();

const redirectTo = AuthSession.makeRedirectUri({
  scheme: "zabt",
  path: "auth/callback",
});

/**
 * useAuth — subscribes to Supabase auth state changes.
 * Returns the current session, the user (if authenticated), and a loading flag
 * that's only true during the initial session restore from secure storage.
 */
export function useAuth() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const { data } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  return { session, user: session?.user ?? null, loading };
}

/**
 * signInWithProvider — kicks off the Supabase PKCE OAuth flow in an in-app browser.
 * Caller should `await` this; on success, the auth state listener fires automatically
 * (no need to navigate manually — the auth gate at /index handles routing).
 */
export async function signInWithProvider(
  provider: "google" | "azure"
): Promise<void> {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo,
      scopes: provider === "azure" ? "openid email profile" : undefined,
      skipBrowserRedirect: true,
    },
  });
  if (error) throw error;
  if (!data.url) throw new Error("No OAuth URL returned");

  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
  if (result.type !== "success") {
    throw new Error(`OAuth cancelled: ${result.type}`);
  }

  const url = new URL(result.url);
  const code = url.searchParams.get("code");
  if (!code) throw new Error("No code in OAuth callback");

  const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(
    code
  );
  if (exchangeError) throw exchangeError;
}

export async function signOut(): Promise<void> {
  await supabase.auth.signOut();
}
