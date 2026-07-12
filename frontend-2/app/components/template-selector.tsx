// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/app/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/app/components/ui/alert-dialog";
import { ChevronDown, Check, Plus, Settings } from "lucide-react";
import { SummaryTemplate, getTemplates, resummarizeMeeting } from "@/app/lib/api";

interface TemplateSelectorProps {
  meetingId: number;
  currentTemplateId: number | null;
  currentTemplateName: string | null;
  onResummarizeStarted: () => void;
  disabled?: boolean;
}

export function TemplateSelector({
  meetingId,
  currentTemplateId,
  currentTemplateName,
  onResummarizeStarted,
  disabled = false,
}: TemplateSelectorProps) {
  const router = useRouter();
  const [templates, setTemplates] = useState<SummaryTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [templatesFetched, setTemplatesFetched] = useState(false);
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<SummaryTemplate | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (templatesFetched) return;
    setLoadingTemplates(true);
    setTemplatesFetched(true);
    getTemplates()
      .then(setTemplates)
      .finally(() => setLoadingTemplates(false));
  }, [templatesFetched]);

  const handleTemplateSelect = (tmpl: SummaryTemplate) => {
    if (tmpl.id === currentTemplateId) return;
    setPendingTemplate(tmpl);
  };

  const handleConfirmResummarize = async () => {
    if (!pendingTemplate) return;
    setSubmitting(true);
    try {
      await resummarizeMeeting(meetingId, pendingTemplate.id);
      setPendingTemplate(null);
      onResummarizeStarted();
    } finally {
      setSubmitting(false);
    }
  };

  const displayName = currentTemplateName ?? "General Summary";
  const builtIns = templates.filter((t) => t.template_type === "built_in");
  const customs = templates.filter((t) => t.template_type === "custom");

  return (
    <>
      <DropdownMenu open={templatesOpen} onOpenChange={setTemplatesOpen}>
        <DropdownMenuTrigger render={<Button variant="ghost" size="sm" disabled={disabled} />}>
          Template: {displayName}
          <ChevronDown className="size-3" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          {loadingTemplates ? (
            <DropdownMenuItem disabled>
              <span className="text-xs text-muted-foreground">Loading...</span>
            </DropdownMenuItem>
          ) : (
            <>
              <DropdownMenuGroup>
                <DropdownMenuLabel>Built-in</DropdownMenuLabel>
                {builtIns.map((tmpl) => (
                  <DropdownMenuItem
                    key={tmpl.id}
                    onClick={() => handleTemplateSelect(tmpl)}
                    className="justify-between"
                  >
                    {tmpl.name}
                    {tmpl.id === currentTemplateId && <Check className="size-3.5 text-primary" />}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuGroup>
              {customs.length > 0 && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuGroup>
                    <DropdownMenuLabel>My Templates</DropdownMenuLabel>
                    {customs.map((tmpl) => (
                      <DropdownMenuItem
                        key={tmpl.id}
                        onClick={() => handleTemplateSelect(tmpl)}
                        className="justify-between"
                      >
                        {tmpl.name}
                        {tmpl.id === currentTemplateId && <Check className="size-3.5 text-primary" />}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuGroup>
                </>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/templates?new=1")}>
                <Plus className="size-3.5" />
                New template
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push("/templates")}>
                <Settings className="size-3.5" />
                Manage templates
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={!!pendingTemplate} onOpenChange={(open) => !open && setPendingTemplate(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Re-summarize with &ldquo;{pendingTemplate?.name}&rdquo;?</AlertDialogTitle>
            <AlertDialogDescription>This will replace the current summary.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmResummarize} disabled={submitting}>
              {submitting ? "Starting..." : "Confirm"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
