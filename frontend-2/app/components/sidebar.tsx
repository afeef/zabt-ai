// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/app/lib/supabase/client";
import { ProfileMenu } from "@/app/components/profile-menu";
import clsx from "clsx";

// ── Icons ──────────────────────────────────────────────────────────────────────

const HomeIcon = () => (
    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7A1 1 0 003 11h1v6a1 1 0 001 1h4v-4h2v4h4a1 1 0 001-1v-6h1a1 1 0 00.707-1.707l-7-7z" />
    </svg>
);
const ChatIcon = () => (
    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
        <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
    </svg>
);
const IntegrationsIcon = () => (
    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
    </svg>
);
const TemplatesIcon = () => (
    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
    </svg>
);
const SettingsIcon = () => (
    <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
    </svg>
);
const ChevronIcon = ({ open }: { open: boolean }) => (
    <svg className={clsx("w-3 h-3 transition-transform duration-150", open && "rotate-180")} viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
    </svg>
);
const HashIcon = () => (
    <svg className="w-3.5 h-3.5 text-stone-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M9.243 3.03a1 1 0 01.727 1.213L9.53 6h2.94l.56-2.243a1 1 0 111.94.486L14.53 6H17a1 1 0 110 2h-2.97l-1 4H15a1 1 0 110 2h-2.47l-.56 2.243a1 1 0 11-1.94-.486L10.47 14H7.53l-.56 2.243a1 1 0 11-1.94-.486L5.47 14H3a1 1 0 110-2h2.97l1-4H5a1 1 0 110-2h2.47l.56-2.243a1 1 0 011.213-.727zM9.03 8l-1 4h2.938l1-4H9.031z" clipRule="evenodd" />
    </svg>
);

const NAV_LINKS = [
    { href: "/", label: "Home", icon: <HomeIcon /> },
    { href: "/ai-chat", label: "AI Chat", icon: <ChatIcon /> },
    { href: "/templates", label: "Templates", icon: <TemplatesIcon /> },
    { href: "/integrations", label: "Integrations", icon: <IntegrationsIcon /> },
    { href: "/settings", label: "Settings", icon: <SettingsIcon /> },
];

interface SidebarProps {
    onNavClick?: () => void;
}

export function Sidebar({ onNavClick }: SidebarProps) {
    const pathname = usePathname();
    const [userName, setUserName] = useState("User");
    const [userEmail, setUserEmail] = useState("");
    const [channelsOpen, setChannelsOpen] = useState(true);
    const [dmOpen, setDmOpen] = useState(true);
    const [foldersOpen, setFoldersOpen] = useState(false);

    useEffect(() => {
        const supabase = createClient();
        supabase.auth.getUser().then(({ data }) => {
            if (data.user) {
                const full = data.user.user_metadata?.full_name as string | undefined;
                setUserName(full ?? data.user.email?.split("@")[0] ?? "User");
                setUserEmail(data.user.email ?? "");
            }
        });
    }, []);

    const initials = userName
        .split(" ")
        .filter(Boolean)
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    return (
        <aside
            className="flex flex-col h-full bg-white border-r border-stone-200 overflow-y-auto"
            style={{ width: "220px", minWidth: "220px" }}
        >
            {/* Logo */}
            <div className="px-4 pt-5 pb-3 border-b border-stone-100">
                <span className="flex items-center gap-2">
                    <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary text-primary-foreground text-xs font-bold select-none">
                        Z
                    </span>
                    <span className="text-base font-bold text-stone-900 tracking-tight">Zabt AI</span>
                </span>
            </div>

            {/* Profile */}
            <div className="px-3 py-3 border-b border-stone-100">
                <ProfileMenu>
                    <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-stone-50 cursor-pointer transition-colors">
                        <span className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/15 text-primary text-xs font-semibold flex-shrink-0">
                            {initials}
                        </span>
                        <div className="min-w-0 flex-1 text-left">
                            <p className="text-sm font-medium text-stone-800 truncate leading-tight">{userName}</p>
                            <p className="text-xs text-stone-400 truncate leading-tight">{userEmail}</p>
                        </div>
                    </div>
                </ProfileMenu>
            </div>

            {/* Primary Nav */}
            <nav className="px-2 py-3 space-y-0.5">
                {NAV_LINKS.map(({ href, label, icon }) => {
                    const active = pathname === href || (href !== "/" && pathname.startsWith(href));
                    return (
                        <Link
                            key={href}
                            href={href}
                            onClick={onNavClick}
                            className={clsx(
                                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                                active
                                    ? "bg-primary/10 text-primary"
                                    : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
                            )}
                        >
                            <span className={active ? "text-primary" : "text-stone-400"}>{icon}</span>
                            {label}
                        </Link>
                    );
                })}
            </nav>

            {/* Channels */}
            <div className="mt-1">
                <button
                    onClick={() => setChannelsOpen((v) => !v)}
                    className="w-full flex items-center justify-between px-4 py-1.5 text-xs font-medium uppercase tracking-wide text-stone-400 hover:text-stone-500 transition-colors"
                >
                    <span>Channels</span>
                    <ChevronIcon open={channelsOpen} />
                </button>
                {channelsOpen && (
                    <div className="px-2 pb-1 space-y-0.5">
                        <Link
                            href="/channels/general"
                            onClick={onNavClick}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-stone-600 hover:bg-stone-100 transition-colors"
                        >
                            <HashIcon /> General
                        </Link>
                    </div>
                )}
            </div>

            {/* Direct Messages */}
            <div className="mt-1">
                <button
                    onClick={() => setDmOpen((v) => !v)}
                    className="w-full flex items-center justify-between px-4 py-1.5 text-xs font-medium uppercase tracking-wide text-stone-400 hover:text-stone-500 transition-colors"
                >
                    <span>Direct Messages</span>
                    <ChevronIcon open={dmOpen} />
                </button>
                {dmOpen && (
                    <p className="px-5 pb-2 text-xs text-stone-400 italic">No conversations yet</p>
                )}
            </div>

            {/* Folders */}
            <div className="mt-1">
                <button
                    onClick={() => setFoldersOpen((v) => !v)}
                    className="w-full flex items-center justify-between px-4 py-1.5 text-xs font-medium uppercase tracking-wide text-stone-400 hover:text-stone-500 transition-colors"
                >
                    <span>Folders</span>
                    <ChevronIcon open={foldersOpen} />
                </button>
                {foldersOpen && (
                    <p className="px-5 pb-2 text-xs text-stone-400 italic">No folders yet</p>
                )}
            </div>

            <div className="flex-1" />

            {/* Plan usage */}
            <div className="px-3 py-4 border-t border-stone-100">
                <div className="bg-stone-50 rounded-lg px-3 py-2 border border-stone-200">
                    <p className="text-xs font-medium text-stone-700">Basic Plan</p>
                    <div className="mt-1 h-1.5 w-full rounded-lg bg-stone-200 overflow-hidden">
                        <div className="h-full bg-primary/60 rounded-lg" style={{ width: "0%" }} />
                    </div>
                    <p className="mt-1 text-xs text-stone-400">0 of 300 monthly mins used</p>
                </div>
            </div>
        </aside>
    );
}
