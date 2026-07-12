import { useState } from "react";
import { Alert, Text, View } from "react-native";
import { SocialButton } from "@/components/social-button";
import { signInWithProvider } from "@/lib/auth";

export default function Login() {
  const [loading, setLoading] = useState<"google" | "microsoft" | null>(null);

  async function handleSignIn(provider: "google" | "microsoft") {
    setLoading(provider);
    try {
      const supabaseProvider = provider === "google" ? "google" : "azure";
      await signInWithProvider(supabaseProvider);
      // Auth state listener in app/index.tsx will route to (tabs) automatically.
    } catch (error) {
      Alert.alert(
        "Sign in failed",
        error instanceof Error ? error.message : "Unknown error"
      );
    } finally {
      setLoading(null);
    }
  }

  return (
    <View className="flex-1 bg-background px-8 justify-center">
      <View className="mb-10">
        <Text className="text-2xl font-bold text-foreground mb-1">
          Welcome to Zabt
        </Text>
        <Text className="text-sm text-muted-foreground">
          Record meetings, get summaries, stay focused.
        </Text>
      </View>

      <View className="gap-3">
        <SocialButton
          provider="google"
          label={loading === "google" ? "Opening Google…" : "Continue with Google"}
          onPress={() => handleSignIn("google")}
          disabled={loading !== null}
        />
        <SocialButton
          provider="microsoft"
          label={
            loading === "microsoft"
              ? "Opening Microsoft…"
              : "Continue with Microsoft"
          }
          onPress={() => handleSignIn("microsoft")}
          disabled={loading !== null}
        />
      </View>
    </View>
  );
}
