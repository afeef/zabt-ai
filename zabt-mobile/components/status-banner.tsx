import { ActivityIndicator, Text, View } from "react-native";
import type { Meeting } from "@zabt/shared";
import {
  STAGE_LABELS,
  STAGE_ORDER,
  getUserStage,
  isActiveMeeting,
} from "@/lib/stage-utils";

interface Props {
  meeting: Meeting;
}

export function StatusBanner({ meeting }: Props) {
  const stage = getUserStage(meeting);
  const active = isActiveMeeting(meeting);

  if (stage === "done") return null;

  if (stage === "failed") {
    return (
      <View className="mx-4 mt-4 mb-2 px-4 py-3 rounded-lg bg-red-50 border border-red-200">
        <Text className="text-sm font-medium text-red-700">
          Processing failed
        </Text>
        <Text className="text-xs text-red-600 mt-1">
          Something went wrong on the server. Try uploading again.
        </Text>
      </View>
    );
  }

  const currentIdx = STAGE_ORDER.indexOf(stage);
  const totalSteps = STAGE_ORDER.length - 1; // exclude "done" from progress dots

  return (
    <View className="mx-4 mt-4 mb-2 px-4 py-3 rounded-lg bg-amber-50 border border-amber-200">
      <View className="flex-row items-center gap-2">
        {active && <ActivityIndicator size="small" color="#d97706" />}
        <Text className="text-sm font-semibold text-amber-700">
          {STAGE_LABELS[stage]}
        </Text>
      </View>

      <View className="flex-row gap-1.5 mt-3">
        {STAGE_ORDER.slice(0, totalSteps).map((s, i) => (
          <View
            key={s}
            className={
              i <= currentIdx ? "flex-1 h-1 rounded-full bg-amber-500" : "flex-1 h-1 rounded-full bg-amber-200"
            }
          />
        ))}
      </View>

      <Text className="text-xs text-amber-700 mt-2">
        Step {Math.min(currentIdx + 1, totalSteps)} of {totalSteps} · this updates automatically
      </Text>
    </View>
  );
}
