// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { SummaryTemplate, getTemplates, resummarizeMeeting } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";

interface SummaryMenuProps {
  currentTemplateId: number | null;
  currentTemplateName: string | null;
  meetingId: number;
  onResummarizeStarted: () => void;
  disabled?: boolean;
  // Export actions
  hasSummary?: boolean;
  onCopySummary?: () => void;
  onDownloadTxt?: () => void;
  onDownloadPdf?: () => void;
}

export function SummaryMenu({
  currentTemplateId,
  currentTemplateName,
  meetingId,
  onResummarizeStarted,
  disabled = false,
  hasSummary = false,
  onCopySummary,
  onDownloadTxt,
  onDownloadPdf,
}: SummaryMenuProps) {
  const [open, setOpen] = useState(false);
  const [templates, setTemplates] = useState<SummaryTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<SummaryTemplate | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    setLoadingTemplates(true);
    getTemplates()
      .then(setTemplates)
      .finally(() => setLoadingTemplates(false));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
        setPendingTemplate(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        setPendingTemplate(null);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const handleSelect = (tmpl: SummaryTemplate) => {
    setOpen(false);
    if (tmpl.id === currentTemplateId) return;
    setPendingTemplate(tmpl);
  };

  const handleConfirm = async () => {
    if (!pendingTemplate) return;
    setSubmitting(true);
    try {
      await resummarizeMeeting(meetingId, pendingTemplate.id);
      setOpen(false);
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
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => !disabled && setOpen((v) => !v)}
        disabled={disabled}
        className="flex items-center gap-1 text-sm font-medium text-stone-500 hover:text-stone-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span>Template: <span className="text-stone-700">{displayName}</span></span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-px">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-stone-200 rounded-lg z-30 py-1 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-stone-100">
            <p className="text-xs font-semibold text-stone-400 uppercase tracking-wide">Templates</p>
            <div className="flex items-center gap-2">
              <Link
                href="/templates?new=1"
                onClick={() => setOpen(false)}
                className="text-stone-400 hover:text-stone-500 transition-colors"
                title="New template"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </Link>
              <Link
                href="/templates"
                onClick={() => setOpen(false)}
                className="text-stone-400 hover:text-stone-500 transition-colors"
                title="Manage templates"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              </Link>
            </div>
          </div>

          {loadingTemplates ? (
            <div className="px-3 py-3 text-xs text-stone-400">Loading…</div>
          ) : (
            <>
              {builtIns.map((tmpl) => (
                <button
                  key={tmpl.id}
                  onClick={() => handleSelect(tmpl)}
                  className="w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 transition-colors"
                >
                  <span>{tmpl.name}</span>
                  {tmpl.id === currentTemplateId && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary flex-shrink-0"><polyline points="20 6 9 17 4 12"/></svg>
                  )}
                </button>
              ))}

              {customs.length > 0 && (
                <>
                  <div className="px-3 pt-2 pb-1">
                    <p className="text-xs font-semibold text-stone-400 uppercase tracking-wide">My Templates</p>
                  </div>
                  {customs.map((tmpl) => (
                    <button
                      key={tmpl.id}
                      onClick={() => handleSelect(tmpl)}
                      className="w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 transition-colors"
                    >
                      <span>{tmpl.name}</span>
                      {tmpl.id === currentTemplateId && (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-primary flex-shrink-0"><polyline points="20 6 9 17 4 12"/></svg>
                      )}
                    </button>
                  ))}
                </>
              )}

              {(onCopySummary || onDownloadTxt || onDownloadPdf) && (
                <>
                  <div className="border-t border-stone-100 mt-1 pt-1">
                    <div className="px-3 py-1.5">
                      <p className="text-xs font-semibold text-stone-400 uppercase tracking-wide">Export</p>
                    </div>
                    {onCopySummary && (
                      <button
                        onClick={() => { onCopySummary(); setOpen(false); }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        Copy summary
                      </button>
                    )}
                    {onDownloadTxt && (
                      <button
                        onClick={() => { onDownloadTxt(); setOpen(false); }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Download as .txt
                      </button>
                    )}
                    {hasSummary && onDownloadPdf && (
                      <button
                        onClick={() => { onDownloadPdf(); setOpen(false); }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
                        Download as PDF
                      </button>
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}

      {pendingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40">
          <div className="bg-white rounded-lg border border-stone-200 w-full max-w-sm p-5">
            <p className="text-sm font-semibold text-stone-900 mb-1">
              Re-summarize with &ldquo;{pendingTemplate.name}&rdquo;?
            </p>
            <p className="text-sm text-stone-500 mb-4">This will replace the current summary.</p>
            <div className="flex items-center justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setPendingTemplate(null)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleConfirm} loading={submitting}>
                Confirm
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
