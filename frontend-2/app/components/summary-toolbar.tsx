// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
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
import {
  Pencil,
  ChevronDown,
  Copy,
  FileText,
  FileDown,
  Eye,
  RotateCcw,
  Check,
  Plus,
  Settings,
} from "lucide-react";
import {
  SummaryTemplate,
  getTemplates,
  resummarizeMeeting,
  Meeting,
} from "@/app/lib/api";

interface SummaryToolbarProps {
  meeting: Meeting;
  isEditing: boolean;
  showOriginal: boolean;
  onEdit: () => void;
  onCopySummary: () => void;
  onDownloadTxt: () => void;
  onDownloadPdf: () => Promise<void>;
  onViewOriginal: () => void;
  onRestoreOriginal: () => Promise<void>;
  currentTemplateId: number | null;
  currentTemplateName: string | null;
  onResummarizeStarted: () => void;
  disabled?: boolean;
}

export function SummaryToolbar({
  meeting,
  isEditing,
  showOriginal,
  onEdit,
  onCopySummary,
  onDownloadTxt,
  onDownloadPdf,
  onViewOriginal,
  onRestoreOriginal,
  currentTemplateId,
  currentTemplateName,
  onResummarizeStarted,
  disabled = false,
}: SummaryToolbarProps) {
  const router = useRouter();
  const [templates, setTemplates] = useState<SummaryTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [templatesFetched, setTemplatesFetched] = useState(false);
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<SummaryTemplate | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);

  // Fetch templates once when component mounts (tab is active)
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
      await resummarizeMeeting(meeting.id, pendingTemplate.id);
      setPendingTemplate(null);
      onResummarizeStarted();
    } finally {
      setSubmitting(false);
    }
  };

  const displayName = currentTemplateName ?? "General Summary";
  const builtIns = templates.filter((t) => t.template_type === "built_in");
  const customs = templates.filter((t) => t.template_type === "custom");
  const hasSummary = !!meeting.summary_text;

  if (isEditing) return null;

  // When viewing original, show only View Current + Restore
  if (showOriginal) {
    return (
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onViewOriginal}>
          <Eye className="size-3.5" />
          View Current
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-primary"
          onClick={() => setRestoreDialogOpen(true)}
        >
          <RotateCcw className="size-3.5" />
          Restore Original
        </Button>

        <AlertDialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Restore original summary?</AlertDialogTitle>
              <AlertDialogDescription>
                This will discard your edits and restore the original AI-generated summary.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={async () => {
                  await onRestoreOriginal();
                  setRestoreDialogOpen(false);
                }}
              >
                Restore
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between">
      {/* Left side: Edit + Edited badge + View Original */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onEdit} disabled={disabled}>
          <Pencil className="size-3.5" />
          Edit
        </Button>

        {meeting.summary_edited && (
          <Badge variant="secondary">Edited</Badge>
        )}

        {meeting.summary_edited && meeting.original_summary_text && (
          <Button variant="ghost" size="sm" onClick={onViewOriginal}>
            <Eye className="size-3.5" />
            View Original
          </Button>
        )}
      </div>

      {/* Right side: Exports + Templates */}
      <div className="flex items-center gap-2">
        {/* Exports Dropdown */}
        {hasSummary && (
          <DropdownMenu>
            <DropdownMenuTrigger
              render={<Button variant="outline" size="sm" disabled={disabled} />}
            >
              Export
              <ChevronDown className="size-3.5" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onCopySummary}>
                <Copy />
                Copy
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onDownloadTxt}>
                <FileText />
                Download Text
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onDownloadPdf()}>
                <FileDown />
                Download PDF
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Templates Dropdown */}
        <DropdownMenu open={templatesOpen} onOpenChange={setTemplatesOpen}>
          <DropdownMenuTrigger
            render={<Button variant="outline" size="sm" disabled={disabled} />}
          >
            Template: {displayName}
            <ChevronDown className="size-3.5" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            {loadingTemplates ? (
              <DropdownMenuItem disabled>
                <span className="text-xs text-muted-foreground">Loading…</span>
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
                      {tmpl.id === currentTemplateId && (
                        <Check className="size-3.5 text-primary" />
                      )}
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
                          {tmpl.id === currentTemplateId && (
                            <Check className="size-3.5 text-primary" />
                          )}
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
      </div>

      {/* Re-summarize Confirmation Dialog */}
      <AlertDialog
        open={!!pendingTemplate}
        onOpenChange={(open) => !open && setPendingTemplate(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Re-summarize with &ldquo;{pendingTemplate?.name}&rdquo;?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will replace the current summary.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmResummarize}
              disabled={submitting}
            >
              {submitting ? "Starting…" : "Confirm"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
