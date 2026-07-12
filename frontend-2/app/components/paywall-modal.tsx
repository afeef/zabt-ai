// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { Lock } from "lucide-react";
import { Button } from "@/app/components/ui/button";

export function PaywallModal() {
    return (
        <div className="absolute inset-x-0 bottom-32 z-20 flex justify-center">
            <div className="bg-background rounded-lg border border-border flex items-center gap-6 max-w-2xl p-6">
                <div className="flex bg-muted items-center justify-center size-10 rounded-lg text-muted-foreground flex-shrink-0">
                    <Lock className="size-5" />
                </div>

                <div className="flex-1">
                    <h3 className="text-sm font-semibold text-foreground mb-0.5">Transcript limit reached</h3>
                    <p className="text-sm text-muted-foreground">
                        You&apos;ve reached your <span className="font-medium text-foreground">30 minute</span> limit. Upgrade for full transcripts.
                    </p>
                </div>

                <Button size="default" className="flex-shrink-0">
                    Upgrade
                </Button>
            </div>
        </div>
    );
}
