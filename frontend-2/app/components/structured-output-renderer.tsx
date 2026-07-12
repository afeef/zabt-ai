// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { MeetingType } from "@/app/lib/api";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/app/components/ui/button";

interface StructuredOutputRendererProps {
  data: Record<string, any> | null;
  status: "pending" | "processing" | "completed" | "failed";
  layoutHint: "cards" | "table" | "columns" | "list";
  meetingType: MeetingType;
  onRetry?: () => void;
}

export function StructuredOutputRenderer({
  data,
  status,
  layoutHint,
  meetingType,
  onRetry,
}: StructuredOutputRendererProps) {
  if (status === "processing" || status === "pending") {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="size-6 animate-spin mb-3" />
        <p className="text-sm">Extracting structured output...</p>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <AlertCircle className="size-6 mb-3 text-destructive" />
        <p className="text-sm mb-3">Extraction failed</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw className="size-3" />
            Retry
          </Button>
        )}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-sm">No structured output available</p>
      </div>
    );
  }

  switch (layoutHint) {
    case "cards":
      return <CardGrid data={data} />;
    case "table":
      return <DataTable data={data} />;
    case "columns":
      return <ColumnLayout data={data} />;
    case "list":
    default:
      return <ItemList data={data} />;
  }
}

// ── Layout: Cards (grooming → user stories) ─────────────────────────────────

function CardGrid({ data }: { data: Record<string, any> }) {
  // Handle both old format (bare list) and new format ({items: [...]})
  const items = Array.isArray(data) ? data : (data.items || []);

  // Detect field names (LLM may return "title" or "user_story" etc.)
  const getTitle = (item: any) => item.title || item.user_story || item.name || item.story || "";
  const getId = (item: any) => item.id || item.story_id || null;
  const getEstimate = (item: any) => item.estimate || item.story_points || item.points || null;
  const getDescription = (item: any) => item.description || item.details || null;
  const getCriteria = (item: any): string[] => item.acceptance_criteria || item.criteria || [];

  return (
    <div className="space-y-3">
      {!Array.isArray(data) && data.sprint_name && (
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {data.sprint_name}
        </p>
      )}
      {items.map((item: any, i: number) => {
        const title = getTitle(item);
        const id = getId(item);
        const estimate = getEstimate(item);
        const description = getDescription(item);
        const criteria = getCriteria(item);

        return (
          <div key={i} className="border border-border rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-start">
              {id && <span className="text-xs font-semibold text-primary">{typeof id === "number" ? `US-${String(id).padStart(3, "0")}` : id}</span>}
              {estimate && (
                <span className="text-xs font-medium bg-secondary px-2 py-0.5 rounded-full">
                  {typeof estimate === "number" ? `${estimate} pts` : estimate}
                </span>
              )}
            </div>
            <p className="text-sm font-medium text-foreground">{title}</p>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
            {criteria.length > 0 && (
              <ul className="text-xs text-muted-foreground pl-4 space-y-0.5">
                {criteria.map((ac: string, j: number) => (
                  <li key={j} className="list-disc">{ac}</li>
                ))}
              </ul>
            )}
            {item.status && (
              <span className="text-[10px] font-medium bg-accent px-2 py-0.5 rounded-full">
                {item.status}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Layout: Table (standup → speaker rows) ──────────────────────────────────

function DataTable({ data }: { data: Record<string, any> }) {
  const items = Array.isArray(data) ? data : (data.items || []);
  if (items.length === 0) return <p className="text-sm text-muted-foreground">No data</p>;

  // Derive columns from ALL items' keys (not just first — items may have different shapes)
  const allKeys = new Set<string>();
  items.forEach((item: any) => Object.keys(item).forEach((k) => allKeys.add(k)));
  const columns = [...allKeys].filter((k) => k !== "meeting_type");

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th key={col} className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item: any, i: number) => (
            <tr key={i} className="border-b border-border last:border-b-0">
              {columns.map((col) => (
                <td key={col} className="py-2.5 px-3 text-foreground align-top">
                  {renderValue(item[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Layout: Columns (retro → went well / improve / actions) ─────────────────

function ColumnLayout({ data }: { data: Record<string, any> }) {
  // Filter out non-array fields and meeting_type
  const columnKeys = Object.keys(data).filter(
    (k) => k !== "meeting_type" && Array.isArray(data[k])
  );

  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(columnKeys.length, 3)}, 1fr)` }}>
      {columnKeys.map((key) => (
        <div key={key} className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            {key.replace(/_/g, " ")}
          </h4>
          <div className="space-y-1.5">
            {data[key].map((item: any, i: number) => (
              <div key={i} className="text-sm text-foreground bg-secondary/50 rounded-md px-3 py-2">
                {typeof item === "string" ? item : renderObjectFields(item)}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Layout: List (generic / 1:1 → simple list) ─────────────────────────────

function ItemList({ data }: { data: Record<string, any> }) {
  // Handle bare array (old format)
  if (Array.isArray(data)) {
    return (
      <div className="space-y-3">
        {data.map((item: any, i: number) => (
          <div key={i} className="text-sm text-foreground bg-secondary/50 rounded-md px-3 py-2">
            {typeof item === "string" ? item : renderObjectFields(item)}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Object.entries(data).map(([key, value]) => {
        if (key === "meeting_type") return null;
        return (
          <div key={key} className="space-y-1.5">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              {key.replace(/_/g, " ")}
            </h4>
            <div className="text-sm text-foreground">{renderValue(value)}</div>
          </div>
        );
      })}
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function renderValue(value: any): React.ReactNode {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    if (typeof value[0] === "string") {
      return (
        <ul className="list-disc pl-4 space-y-0.5">
          {value.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      );
    }
    return (
      <div className="space-y-1">
        {value.map((item, i) => (
          <div key={i} className="text-xs">{renderObjectFields(item)}</div>
        ))}
      </div>
    );
  }
  if (typeof value === "object") return renderObjectFields(value);
  return String(value);
}

function renderObjectFields(obj: Record<string, any>): React.ReactNode {
  return (
    <div className="space-y-0.5">
      {Object.entries(obj).map(([k, v]) => {
        if (v === null || v === undefined) return null;
        return (
          <div key={k}>
            <span className="text-muted-foreground font-medium">{k.replace(/_/g, " ")}: </span>
            {typeof v === "string" ? v : Array.isArray(v) ? v.join(", ") : String(v)}
          </div>
        );
      })}
    </div>
  );
}
