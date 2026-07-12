import { TextInput, type TextInputProps } from "react-native";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: TextInputProps) {
  return (
    <TextInput
      placeholderTextColor="#9a9288"
      className={cn(
        "h-10 border border-input rounded-lg px-3 text-sm text-foreground bg-background",
        className
      )}
      {...props}
    />
  );
}
