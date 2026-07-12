"use client";

import { useEffect, useState } from "react";
import { X, Plus, ChevronUp, ChevronDown } from "lucide-react";
import {
  listLanguages,
  getLanguagePreferences,
  setLanguagePreferences,
  type LanguageEntry,
} from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";

export function LanguagePreferencesEditor() {
  const [catalog, setCatalog] = useState<LanguageEntry[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [picker, setPicker] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.all([listLanguages(), getLanguagePreferences()])
      .then(([all, prefs]) => {
        setCatalog(all);
        setSelected(prefs);
      })
      .finally(() => setLoaded(true));
  }, []);

  const byCode = (code: string) => catalog.find((e) => e.code === code);
  const available = catalog.filter((e) => !selected.includes(e.code));

  async function persist(codes: string[]) {
    setSaving(true);
    try {
      const saved = await setLanguagePreferences(codes);
      setSelected(saved);
    } finally {
      setSaving(false);
    }
  }

  function move(code: string, dir: -1 | 1) {
    const i = selected.indexOf(code);
    if (i < 0) return;
    const j = i + dir;
    if (j < 0 || j >= selected.length) return;
    const next = [...selected];
    [next[i], next[j]] = [next[j], next[i]];
    persist(next);
  }

  function remove(code: string) {
    if (selected.length === 1) return;
    persist(selected.filter((c) => c !== code));
  }

  function add() {
    if (!picker) return;
    persist([...selected, picker]);
    setPicker("");
  }

  if (!loaded) {
    return <p className="text-sm text-stone-500">Loading…</p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-stone-600">
        We&apos;ll auto-detect language. If detection picks something outside
        this list, we&apos;ll force the primary.
      </p>

      <ul className="space-y-2">
        {selected.map((code, i) => {
          const e = byCode(code);
          if (!e) return null;
          return (
            <li
              key={code}
              className="flex items-center justify-between rounded-lg border border-stone-200 bg-white p-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-stone-800">{e.display_name}</span>
                {i === 0 && (
                  <span className="rounded-4xl bg-stone-100 px-2 py-0.5 text-xs text-stone-500 font-medium">
                    Primary
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  disabled={i === 0 || saving}
                  onClick={() => move(code, -1)}
                  aria-label="Move up"
                >
                  <ChevronUp className="size-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  disabled={i === selected.length - 1 || saving}
                  onClick={() => move(code, 1)}
                  aria-label="Move down"
                >
                  <ChevronDown className="size-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  disabled={selected.length === 1 || saving}
                  onClick={() => remove(code)}
                  aria-label={`Remove ${e.display_name}`}
                  className="ml-1 text-stone-400 hover:text-stone-700"
                >
                  <X className="size-3.5" />
                </Button>
              </div>
            </li>
          );
        })}
      </ul>

      {available.length > 0 && (
        <div className="flex items-center gap-2">
          <select
            className="flex-1 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-800 outline-none focus:border-stone-400 transition-colors"
            value={picker}
            onChange={(e) => setPicker(e.target.value)}
            disabled={saving}
          >
            <option value="">Add a language…</option>
            {available.map((e) => (
              <option key={e.code} value={e.code}>
                {e.display_name}
              </option>
            ))}
          </select>
          <Button
            type="button"
            variant="outline"
            disabled={!picker || saving}
            onClick={add}
          >
            <Plus className="size-4" />
            Add
          </Button>
        </div>
      )}
    </div>
  );
}
