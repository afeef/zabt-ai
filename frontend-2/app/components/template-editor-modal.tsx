// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState } from "react";
import { SummaryTemplate, createTemplate, updateTemplate } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/app/components/ui/dialog";

interface TemplateEditorModalProps {
  mode: "create" | "edit";
  template?: SummaryTemplate;
  onSaved: (tmpl: SummaryTemplate) => void;
  onClose: () => void;
}

const MAX_BODY = 4000;

export function TemplateEditorModal({
  mode,
  template,
  onSaved,
  onClose,
}: TemplateEditorModalProps) {
  const [name, setName] = useState(template?.name ?? "");
  const [body, setBody] = useState(template?.body ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setError(null);
    if (!name.trim()) { setError("Template name is required."); return; }
    if (!body.trim()) { setError("Template body is required."); return; }
    if (body.length > MAX_BODY) { setError(`Template body must not exceed ${MAX_BODY} characters.`); return; }

    setSaving(true);
    try {
      const saved =
        mode === "edit" && template
          ? await updateTemplate(template.id, name.trim(), body)
          : await createTemplate(name.trim(), body);
      onSaved(saved);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Failed to save template.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent showCloseButton={false} className="sm:max-w-lg p-0 flex flex-col" style={{ maxHeight: "90vh" }}>
        <DialogHeader className="px-5 py-4 border-b border-border">
          <DialogTitle>
            {mode === "create" ? "New Template" : "Edit Template"}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Template name</label>
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Weekly Standup"
              maxLength={100}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-medium text-muted-foreground">Template body (Markdown)</label>
              <span className={`text-xs ${body.length > MAX_BODY ? "text-destructive font-medium" : "text-muted-foreground"}`}>
                {body.length} / {MAX_BODY}
              </span>
            </div>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="## Overview&#10;[Describe the purpose...]&#10;&#10;## Action Items&#10;[List tasks...]"
              rows={12}
              className="flex w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm transition-[color,box-shadow] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 resize-none font-mono"
            />
          </div>

          {error && (
            <p className="text-xs text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>

        <DialogFooter className="px-5 py-4">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} loading={saving}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
