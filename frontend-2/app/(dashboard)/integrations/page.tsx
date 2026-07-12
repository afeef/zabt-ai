// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import {
  IntegrationRead,
  CalendarEventRead,
  getIntegrations,
  getCalendarEvents,
} from "@/app/lib/api";
import { IntegrationCard } from "@/app/components/integration-card";
import { CalendarEventList } from "@/app/components/calendar-event-list";

const SUPPORTED_PROVIDERS = ["microsoft"];

export default function IntegrationsPage() {
  const searchParams = useSearchParams();
  const [integrations, setIntegrations] = useState<IntegrationRead[]>([]);
  const [events, setEvents] = useState<CalendarEventRead[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [intData, evData] = await Promise.all([
        getIntegrations(),
        getCalendarEvents(),
      ]);
      setIntegrations(intData);
      setEvents(evData);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (searchParams.get("connected")) {
      load();
    }
  }, [searchParams, load]);

  const getIntegration = (provider: string): IntegrationRead | null => {
    return integrations.find((i) => i.provider === provider) || null;
  };

  const hasAnyConnection = integrations.some((i) => i.status === "active");

  return (
    <div className="px-8 py-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-stone-900">Integrations</h1>
        <p className="text-sm text-stone-500 mt-1">
          Connect your accounts to sync calendars and automate meeting transcription.
        </p>
      </div>

      <section className="mb-10">
        <h2 className="text-lg font-semibold text-stone-900 mb-4">Connected Accounts</h2>
        <div className="space-y-3">
          {SUPPORTED_PROVIDERS.map((provider) => (
            <IntegrationCard
              key={provider}
              provider={provider}
              integration={getIntegration(provider)}
              onStatusChange={load}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-stone-900 mb-4">Upcoming Meetings</h2>
        {loading ? (
          <div className="text-center py-8 text-stone-400">Loading...</div>
        ) : hasAnyConnection ? (
          <CalendarEventList events={events} onEventUpdated={load} />
        ) : (
          <div className="text-center py-12 border border-dashed border-stone-200 rounded-lg text-stone-500">
            <p className="font-medium">No accounts connected</p>
            <p className="text-sm mt-1">Connect Microsoft above to see your upcoming meetings.</p>
          </div>
        )}
      </section>
    </div>
  );
}
