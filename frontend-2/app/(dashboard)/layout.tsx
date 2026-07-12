// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { usePostHog } from "posthog-js/react";
import { createClient } from "@/app/lib/supabase/client";
import { AppShell } from "@/app/components/app-shell";
import { TooltipProvider } from "@/app/components/ui/tooltip";
import { Spinner } from "@/app/components/ui/spinner";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const posthog = usePostHog();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const supabase = createClient();

        // Check initial session
        supabase.auth.getSession().then(({ data }) => {
            if (!data.session) {
                router.replace("/login");
            } else {
                const user = data.session.user;
                posthog?.identify(user.id, { email: user.email });
                // Fire user_signed_up once per user (tracked via localStorage flag)
                const signupKey = `ph_signup_tracked_${user.id}`;
                if (!localStorage.getItem(signupKey)) {
                    posthog?.capture('user_signed_up', { signup_date: user.created_at });
                    localStorage.setItem(signupKey, '1');
                }
                setLoading(false);
            }
        });

        // Listen for auth changes
        const { data: listener } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                if (!session) {
                    router.replace("/login");
                } else {
                    const user = session.user;
                    posthog?.identify(user.id, { email: user.email });
                    setLoading(false);
                }
            }
        );

        return () => listener.subscription.unsubscribe();
    }, [router]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-stone-50">
                <div className="flex flex-col items-center gap-3">
                    <Spinner className="size-6 text-muted-foreground" />
                    <p className="text-sm text-stone-400 font-medium">Authenticating...</p>
                </div>
            </div>
        );
    }

    return (
        <TooltipProvider>
            <AppShell>{children}</AppShell>
        </TooltipProvider>
    );
}
