// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState } from "react";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import { Unplug, ExternalLink, Loader2 } from "lucide-react";
import { IntegrationRead, connectProvider, disconnectProvider } from "@/app/lib/api";

interface ProviderConfig {
  name: string;
  description: string;
  icon: React.ReactNode;
}

const PROVIDERS: Record<string, ProviderConfig> = {
  microsoft: {
    name: "Microsoft",
    description: "Outlook Calendar, Teams meetings, OneDrive recordings",
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 23 23" fill="none">
        <rect x="1" y="1" width="10" height="10" fill="#F25022" />
        <rect x="12" y="1" width="10" height="10" fill="#7FBA00" />
        <rect x="1" y="12" width="10" height="10" fill="#00A4EF" />
        <rect x="12" y="12" width="10" height="10" fill="#FFB900" />
      </svg>
    ),
  },
};

interface IntegrationCardProps {
  provider: string;
  integration: IntegrationRead | null;
  onStatusChange: () => void;
}

export function IntegrationCard({ provider, integration, onStatusChange }: IntegrationCardProps) {
  const [loading, setLoading] = useState(false);
  const config = PROVIDERS[provider];
  if (!config) return null;

  const isConnected = integration?.status === "active";

  const handleConnect = async () => {
    setLoading(true);
    try {
      const { auth_url } = await connectProvider(provider);
      window.location.href = auth_url;
    } catch {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    try {
      await disconnectProvider(provider);
      onStatusChange();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-stone-200 rounded-lg p-5 bg-white">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {config.icon}
          <div>
            <h3 className="font-semibold text-stone-900">{config.name}</h3>
            <p className="text-sm text-stone-500">{config.description}</p>
          </div>
        </div>
        {isConnected && (
          <Badge variant="outline" className="text-green-700 border-green-300 bg-green-50">
            Connected
          </Badge>
        )}
      </div>
      {isConnected && integration?.provider_email && (
        <p className="mt-3 text-sm text-stone-600">
          Signed in as <span className="font-medium">{integration.provider_email}</span>
        </p>
      )}
      <div className="mt-4">
        {isConnected ? (
          <Button variant="outline" size="sm" onClick={handleDisconnect} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Unplug className="w-4 h-4 mr-2" />}
            Disconnect
          </Button>
        ) : (
          <Button size="sm" onClick={handleConnect} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ExternalLink className="w-4 h-4 mr-2" />}
            Connect {config.name}
          </Button>
        )}
      </div>
    </div>
  );
}
