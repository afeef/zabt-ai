// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { IntegrationRead, getIntegrations } from "@/app/lib/api";
import { IntegrationCard } from "@/app/components/integration-card";

const SUPPORTED_PROVIDERS = ["microsoft"];

export default function IntegrationsPage() {
  const searchParams = useSearchParams();
  const [integrations, setIntegrations] = useState<IntegrationRead[]>([]);
  const [, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const intData = await getIntegrations();
      setIntegrations(intData);
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

  return (
    <div className="px-8 py-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-stone-900">Integrations</h1>
        <p className="text-sm text-stone-500 mt-1">
          Connect your accounts to automate meeting transcription.
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
    </div>
  );
}
