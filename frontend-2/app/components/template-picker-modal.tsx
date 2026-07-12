// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check } from "lucide-react";
import { SummaryTemplate, setDefaultTemplate, deleteTemplate } from "@/app/lib/api";
import { TemplateEditorModal } from "@/app/components/template-editor-modal";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog";
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
import { cn } from "@/app/lib/utils";

interface TemplatePickerModalProps {
  templates: SummaryTemplate[];
  initialSelected?: SummaryTemplate;
  userDefaultId?: number | null;
  onClose: () => void;
  onDefaultChanged: (newDefaultId: number) => void;
  onTemplateUpdated: (tmpl: SummaryTemplate) => void;
  onTemplateDeleted: (id: number) => void;
}

export function TemplatePickerModal({
  templates,
  initialSelected,
  userDefaultId,
  onClose,
  onDefaultChanged,
  onTemplateUpdated,
  onTemplateDeleted,
}: TemplatePickerModalProps) {
  const [selected, setSelected] = useState<SummaryTemplate>(
    initialSelected ?? templates[0]
  );
  const [editMode, setEditMode] = useState(false);
  const [settingDefault, setSettingDefault] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const builtIns = templates.filter((t) => t.template_type === "built_in");
  const customs = templates.filter((t) => t.template_type === "custom");
  const isCustom = selected.template_type === "custom";

  const handleSetDefault = async () => {
    setSettingDefault(true);
    try {
      await setDefaultTemplate(selected.id);
      onDefaultChanged(selected.id);
    } finally {
      setSettingDefault(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteTemplate(selected.id);
      onTemplateDeleted(selected.id);
      onClose();
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  if (editMode) {
    return (
      <TemplateEditorModal
        mode="edit"
        template={selected}
        onSaved={(updated) => {
          setSelected(updated);
          onTemplateUpdated(updated);
          setEditMode(false);
        }}
        onClose={() => setEditMode(false)}
      />
    );
  }

  return (
    <>
      <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
        <DialogContent showCloseButton className="sm:max-w-2xl p-0 flex flex-col" style={{ maxHeight: "90vh" }}>
          <DialogHeader className="px-5 py-4 border-b border-border">
            <DialogTitle>Templates</DialogTitle>
          </DialogHeader>

          {/* Body */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left panel */}
            <div className="w-48 flex-shrink-0 border-r border-border overflow-y-auto py-2">
              {builtIns.length > 0 && (
                <>
                  <p className="px-4 pt-1 pb-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">Available</p>
                  {builtIns.map((tmpl) => (
                    <button
                      key={tmpl.id}
                      onClick={() => setSelected(tmpl)}
                      className={cn(
                        "w-full flex items-center justify-between gap-2 px-4 py-2 text-sm transition-colors",
                        selected.id === tmpl.id
                          ? "bg-primary/10 text-primary font-medium"
                          : "text-foreground hover:bg-muted"
                      )}
                    >
                      <span className="truncate">{tmpl.name}</span>
                      {selected.id === tmpl.id && <Check className="size-3 flex-shrink-0" />}
                    </button>
                  ))}
                </>
              )}
              {customs.length > 0 && (
                <>
                  <p className="px-4 pt-3 pb-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">My Templates</p>
                  {customs.map((tmpl) => (
                    <button
                      key={tmpl.id}
                      onClick={() => setSelected(tmpl)}
                      className={cn(
                        "w-full flex items-center justify-between gap-2 px-4 py-2 text-sm transition-colors",
                        selected.id === tmpl.id
                          ? "bg-primary/10 text-primary font-medium"
                          : "text-foreground hover:bg-muted"
                      )}
                    >
                      <span className="truncate">{tmpl.name}</span>
                      {selected.id === tmpl.id && <Check className="size-3 flex-shrink-0" />}
                    </button>
                  ))}
                </>
              )}
            </div>

            {/* Right panel — preview */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-sm font-semibold text-foreground">{selected.name}</h3>
                <Badge variant="secondary">
                  {selected.template_type === "built_in" ? "Built-in" : "Custom"}
                </Badge>
                {(userDefaultId === selected.id || (userDefaultId == null && selected.is_system_default)) && (
                  <Badge variant="secondary" className="text-primary">
                    ★ Default
                  </Badge>
                )}
              </div>
              <div className="bg-muted rounded-lg border border-border px-4 py-3">
                <div className="prose prose-stone prose-sm max-w-none prose-headings:font-semibold prose-headings:text-foreground prose-p:text-muted-foreground prose-p:text-sm prose-li:text-muted-foreground">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{selected.body}</ReactMarkdown>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between gap-2 px-5 py-4 border-t border-border flex-shrink-0">
            <div className="flex items-center gap-2">
              {isCustom && (
                <>
                  <Button variant="outline" size="sm" onClick={() => setEditMode(true)}>
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setConfirmDelete(true)}
                  >
                    Delete
                  </Button>
                </>
              )}
            </div>
            <Button
              onClick={handleSetDefault}
              loading={settingDefault}
              disabled={(userDefaultId === selected.id) || (userDefaultId == null && selected.is_system_default)}
            >
              Set as Default
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete template?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &ldquo;{selected.name}&rdquo;. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
