import { View, type ViewProps } from "react-native";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ViewProps) {
  return (
    <View
      className={cn(
        "bg-background border border-border rounded-lg p-4",
        className
      )}
      {...props}
    />
  );
}
