import { Redirect, useLocalSearchParams } from "expo-router";

/**
 * Universal Link entrypoint. `https://app.zabt.ai/m/<id>` opens the app here,
 * we immediately redirect to the full meeting detail screen.
 */
export default function MShortlink() {
  const { id } = useLocalSearchParams<{ id: string }>();
  if (!id) return <Redirect href="/(tabs)" />;
  return <Redirect href={`/meeting/${id}`} />;
}
