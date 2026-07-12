import { Redirect, Stack } from "expo-router";
import { useAuth } from "@/lib/auth";

export default function AuthLayout() {
  const { session, loading } = useAuth();
  // Once a session lands (e.g., after OAuth callback completes), bounce out of
  // the auth group. Without this the user stays on /login and has to tap
  // sign-in twice.
  if (!loading && session) return <Redirect href="/(tabs)" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
