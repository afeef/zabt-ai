// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { SummaryTemplate, getTemplates, setDefaultTemplate } from "@/app/lib/api";
import { Plus } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import { TemplateEditorModal } from "@/app/components/template-editor-modal";
import { TemplatePickerModal } from "@/app/components/template-picker-modal";

export default function TemplatesPage() {
  const searchParams = useSearchParams();
  const [templates, setTemplates] = useState<SummaryTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [userDefaultId, setUserDefaultId] = useState<number | null>(null);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [pickerTemplate, setPickerTemplate] = useState<SummaryTemplate | null>(null);

  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getTemplates();
      setTemplates(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setShowCreateModal(true);
    }
  }, [searchParams]);

  const handleSetDefault = async (tmpl: SummaryTemplate) => {
    await setDefaultTemplate(tmpl.id);
    setUserDefaultId(tmpl.id);
  };

  const isDefault = (tmpl: SummaryTemplate) => {
    if (userDefaultId !== null) return tmpl.id === userDefaultId;
    return tmpl.is_system_default;
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

  const builtIns = templates.filter((t) => t.template_type === "built_in");
  const customs = templates.filter((t) => t.template_type === "custom");

  return (
    <div className="px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-bold text-stone-900">Templates</h1>
          <p className="text-sm text-stone-400 mt-0.5">Manage summary templates used for your meetings</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="size-4" />
          New Template
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-stone-400">Loading templates…</p>
      ) : templates.length === 0 ? (
        <p className="text-sm text-stone-400 italic">No templates found.</p>
      ) : (
        <div className="bg-white rounded-lg border border-stone-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-stone-100 bg-stone-50/60">
                <th className="px-5 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide">Template</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide w-32">Type</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide w-44">Last edited</th>
                <th className="px-5 py-3 w-32" />
              </tr>
            </thead>
            <tbody>
              {builtIns.length > 0 && (
                <>
                  <tr>
                    <td colSpan={4} className="px-5 pt-4 pb-1.5">
                      <span className="text-xs font-semibold text-stone-400 uppercase tracking-wide">Built-in</span>
                    </td>
                  </tr>
                  {builtIns.map((tmpl) => (
                    <tr
                      key={tmpl.id}
                      onClick={() => setPickerTemplate(tmpl)}
                      className="border-t border-stone-50 hover:bg-stone-50 transition-colors cursor-pointer"
                    >
                      <td className="px-5 py-3.5 font-medium text-stone-800">
                        <span className="flex items-center gap-2.5">
                          {tmpl.name}
                          {isDefault(tmpl) && (
                            <Badge variant="secondary" className="text-primary">★ Default</Badge>
                          )}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-stone-400 text-xs">Built-in</td>
                      <td className="px-5 py-3.5 text-stone-400">—</td>
                      <td className="px-5 py-3.5 text-right">
                        {!isDefault(tmpl) && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); handleSetDefault(tmpl); }}
                            className="text-xs h-auto p-0"
                          >
                            Set default
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </>
              )}

              {customs.length > 0 && (
                <>
                  <tr>
                    <td colSpan={4} className="px-5 pt-5 pb-1.5 border-t border-stone-100">
                      <span className="text-xs font-semibold text-stone-400 uppercase tracking-wide">My Templates</span>
                    </td>
                  </tr>
                  {customs.map((tmpl) => (
                    <tr
                      key={tmpl.id}
                      onClick={() => setPickerTemplate(tmpl)}
                      className="border-t border-stone-50 hover:bg-stone-50 transition-colors cursor-pointer"
                    >
                      <td className="px-5 py-3.5 font-medium text-stone-800">
                        <span className="flex items-center gap-2.5">
                          {tmpl.name}
                          {isDefault(tmpl) && (
                            <Badge variant="secondary" className="text-primary">★ Default</Badge>
                          )}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-stone-400 text-xs">Custom</td>
                      <td className="px-5 py-3.5 text-stone-400">{formatDate(tmpl.updated_at)}</td>
                      <td className="px-5 py-3.5 text-right">
                        {!isDefault(tmpl) && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); handleSetDefault(tmpl); }}
                            className="text-xs h-auto p-0"
                          >
                            Set default
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showCreateModal && (
        <TemplateEditorModal
          mode="create"
          onSaved={(saved) => {
            setTemplates((prev) => [...prev, saved]);
            setShowCreateModal(false);
          }}
          onClose={() => setShowCreateModal(false)}
        />
      )}

      {pickerTemplate && (
        <TemplatePickerModal
          templates={templates}
          initialSelected={pickerTemplate}
          userDefaultId={userDefaultId}
          onClose={() => setPickerTemplate(null)}
          onDefaultChanged={(id) => setUserDefaultId(id)}
          onTemplateUpdated={(updated) => {
            setTemplates((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
            setPickerTemplate(updated);
          }}
          onTemplateDeleted={(id) => {
            setTemplates((prev) => prev.filter((t) => t.id !== id));
            setPickerTemplate(null);
          }}
        />
      )}
    </div>
  );
}
