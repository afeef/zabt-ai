"use client";

import { MeetingType } from "@/app/lib/api";
import { LayoutList, Users, RotateCcw, MessageSquare, FileText, ChevronDown } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu";

const MEETING_TYPES: { value: MeetingType; label: string; icon: typeof FileText }[] = [
  { value: "generic", label: "General", icon: FileText },
  { value: "grooming", label: "Grooming", icon: LayoutList },
  { value: "standup", label: "Standup", icon: Users },
  { value: "retro", label: "Retro", icon: RotateCcw },
  { value: "one_on_one", label: "1:1", icon: MessageSquare },
];

interface MeetingTypeSelectorProps {
  value: MeetingType;
  onChange: (type: MeetingType) => void;
  disabled?: boolean;
  size?: "sm" | "md";
  variant?: "buttons" | "dropdown";
}

export function MeetingTypeSelector({
  value,
  onChange,
  disabled,
  size = "md",
  variant = "dropdown",
}: MeetingTypeSelectorProps) {
  const current = MEETING_TYPES.find((t) => t.value === value) || MEETING_TYPES[0];
  const CurrentIcon = current.icon;

  if (variant === "buttons") {
    const sizeClasses = size === "sm"
      ? "px-2 py-1 text-xs gap-1"
      : "px-3 py-2 text-sm gap-2";

    return (
      <div className="flex gap-2 flex-wrap">
        {MEETING_TYPES.map(({ value: typeValue, label, icon: Icon }) => (
          <button
            key={typeValue}
            type="button"
            disabled={disabled}
            onClick={() => onChange(typeValue)}
            className={`flex items-center justify-center rounded-lg border transition-colors ${sizeClasses} ${
              value === typeValue
                ? "border-primary bg-primary/10 text-primary font-medium"
                : "border-border bg-background text-muted-foreground hover:bg-accent"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            <Icon className="size-4" />
            {label}
          </button>
        ))}
      </div>
    );
  }

  // Dropdown variant (default) — compact, single button
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            className="h-7 text-xs gap-1.5"
          />
        }
      >
        <CurrentIcon className="size-3" />
        {current.label}
        <ChevronDown className="size-3 text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {MEETING_TYPES.map(({ value: typeValue, label, icon: Icon }) => (
          <DropdownMenuItem
            key={typeValue}
            onClick={() => onChange(typeValue)}
            className={typeValue === value ? "text-primary font-medium" : ""}
          >
            <Icon className="size-4" />
            {label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
