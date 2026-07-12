import { Text, View } from "react-native";
import Markdown from "react-native-markdown-display";
import type { Meeting } from "@zabt/shared";

interface Props {
  meeting: Meeting;
}

const markdownStyles = {
  body: { color: "#1a1510", fontSize: 14, lineHeight: 22 },
  heading1: { fontSize: 22, fontWeight: "700" as const, marginTop: 16, marginBottom: 8, color: "#1a1510" },
  heading2: { fontSize: 18, fontWeight: "600" as const, marginTop: 14, marginBottom: 6, color: "#1a1510" },
  heading3: { fontSize: 16, fontWeight: "600" as const, marginTop: 12, marginBottom: 4, color: "#1a1510" },
  strong: { fontWeight: "600" as const },
  em: { fontStyle: "italic" as const },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2 },
  paragraph: { marginVertical: 6 },
  code_inline: { backgroundColor: "#f4f2ee", paddingHorizontal: 4, borderRadius: 4, fontFamily: "Courier" },
  code_block: { backgroundColor: "#f4f2ee", padding: 12, borderRadius: 8, fontFamily: "Courier" },
  link: { color: "#e11d74", textDecorationLine: "underline" as const },
  blockquote: { borderLeftWidth: 3, borderLeftColor: "#e5e3de", paddingLeft: 12, marginVertical: 8 },
};

export function SummaryTab({ meeting }: Props) {
  if (!meeting.summary_text) {
    return (
      <View className="py-8 items-center">
        <Text className="text-sm text-muted-foreground text-center">
          {meeting.status === "processing"
            ? "Summary is being generated…"
            : meeting.status === "failed"
            ? "Summary generation failed."
            : "No summary available"}
        </Text>
      </View>
    );
  }

  return <Markdown style={markdownStyles}>{meeting.summary_text}</Markdown>;
}
