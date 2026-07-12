"use client";

import Link from "next/link";
import { Button } from "@/app/components/ui/button";

export function RightPanel() {
    return (
        <div className="flex flex-col h-full px-4 py-5 gap-6">
            {/* Quick actions */}
            <section>
                <h3 className="text-xs font-medium uppercase tracking-wide text-stone-400 mb-3">
                    Quick Actions
                </h3>
                <div className="space-y-2">
                    <Button variant="secondary" className="w-full justify-start gap-2" size="default" disabled>
                        <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                        </svg>
                        Connect a calendar
                    </Button>
                </div>
            </section>

            {/* Upcoming meetings */}
            <section>
                <h3 className="text-xs font-medium uppercase tracking-wide text-stone-400 mb-3">
                    Upcoming Meetings
                </h3>
                <div className="bg-stone-50 rounded-lg border border-stone-200 px-4 py-5 text-center">
                    <p className="text-sm text-stone-500 mb-1">No upcoming meetings</p>
                    <p className="text-xs text-stone-400">
                        Connect a calendar to see your schedule here.
                    </p>
                    <div className="mt-4 flex gap-2">
                        <Button variant="outline" size="sm" className="flex-1 gap-1.5 text-xs" disabled>
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                            </svg>
                            Google
                        </Button>
                        <Button variant="outline" size="sm" className="flex-1 gap-1.5 text-xs" disabled>
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                            </svg>
                            Outlook
                        </Button>
                    </div>
                </div>
            </section>

            {/* Get started checklist */}
            <section>
                <h3 className="text-xs font-medium uppercase tracking-wide text-stone-400 mb-3">
                    Get Started
                </h3>
                <div className="space-y-2">
                    {[
                        { label: "Import your first meeting", done: false, href: "/" },
                        { label: "Connect a calendar", done: false, href: "#" },
                        { label: "Invite a teammate", done: false, href: "#" },
                    ].map(({ label, done, href }) => (
                        <Link
                            key={label}
                            href={href}
                            className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 transition-colors"
                        >
                            <span
                                className={`w-4 h-4 rounded-full border flex-shrink-0 ${done ? "border-primary bg-primary" : "border-stone-300"
                                    }`}
                            />
                            <span className={`text-xs ${done ? "line-through text-stone-400" : "text-stone-500"}`}>
                                {label}
                            </span>
                        </Link>
                    ))}
                </div>
                <p className="mt-2 text-xs text-stone-400 text-right">0/3 complete</p>
            </section>
        </div>
    );
}
