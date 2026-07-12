"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ChevronDown, MoreVertical, Trash2 } from "lucide-react";
import { getMeetings } from "@/app/lib/api";
import type { Meeting } from "@/app/lib/api";
import { StatusBadge } from "@/app/components/status-badge";
import { Button } from "@/app/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/app/components/ui/alert-dialog";
import { isActiveMeeting } from "@/app/lib/stage-utils";

// ── Markdown stripper ─────────────────────────────────────────────────────────

function stripMarkdown(text: string): string {
    return text
        .replace(/^#{1,6}\s+/gm, "")       // headings
        .replace(/\*\*(.+?)\*\*/g, "$1")   // bold
        .replace(/\*(.+?)\*/g, "$1")       // italic
        .replace(/`{1,3}[^`]*`{1,3}/g, "") // code
        .replace(/^[-*+]\s+/gm, "")        // unordered list bullets
        .replace(/^\d+\.\s+/gm, "")        // ordered list numbers
        .replace(/\[(.+?)\]\(.+?\)/g, "$1") // links
        .replace(/^>\s+/gm, "")            // blockquotes
        .replace(/\n{2,}/g, " ")           // collapse blank lines
        .trim();
}

// ── Date grouping helpers ─────────────────────────────────────────────────────

function formatDateLabel(isoString: string): string {
    const date = new Date(isoString);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);

    const sameDay = (a: Date, b: Date) =>
        a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate();

    if (sameDay(date, today)) {
        return `Today, ${date.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
    }
    if (sameDay(date, yesterday)) {
        return "Yesterday";
    }
    return date.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" });
}

function groupByDate(meetings: Meeting[]): { label: string; meetings: Meeting[] }[] {
    const map = new Map<string, Meeting[]>();
    for (const m of meetings) {
        const label = formatDateLabel(m.created_at);
        if (!map.has(label)) map.set(label, []);
        map.get(label)!.push(m);
    }
    return Array.from(map.entries()).map(([label, meetings]) => ({ label, meetings }));
}

// ── Formatting helpers ────────────────────────────────────────────────────────

function formatTimeOfDay(isoString: string): string {
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

function formatDuration(seconds: number | null): string | null {
    if (seconds === null || seconds === undefined) return null;
    if (seconds < 60) return `${Math.round(seconds)} sec`;
    return `${Math.round(seconds / 60)} min`;
}

function formatSpeakerInfo(speakers?: Record<string, { name: string; percentage: number }>): string | null {
    if (!speakers) return null;
    const names = Object.values(speakers).map((s) => s.name);
    if (names.length === 0) return null;
    if (names.length === 1) return names[0];
    if (names.length === 2) return names.join(" & ");
    return `${names[0]} +${names.length - 1} others`;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MeetingFeedCard({ meeting, onDelete }: { meeting: Meeting; onDelete: (id: number) => void }) {
    const [confirmingDelete, setConfirmingDelete] = useState(false);

    const initials = meeting.title
        .split(" ")
        .filter(Boolean)
        .map((w) => w[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    const isProcessing = meeting.status === "queued" || meeting.status === "processing";
    const isCompleted = meeting.status === "completed";
    const hasSummary = isCompleted && meeting.summary_text && meeting.summary_text.length > 0;

    const handleDeleteClick = () => {
        setConfirmingDelete(true);
    };

    // Build metadata parts
    const metaParts: string[] = [];
    metaParts.push(formatTimeOfDay(meeting.created_at));
    const duration = formatDuration(meeting.duration_seconds);
    if (duration) metaParts.push(duration);
    const speakerInfo = formatSpeakerInfo(meeting.speakers);
    if (speakerInfo) metaParts.push(speakerInfo);

    return (
        <>
        <Link href={`/meetings/${meeting.id}`} className="block mb-3 last:mb-0">
            <div className="bg-white rounded-lg border border-stone-200 p-4 hover:bg-stone-50 transition-colors cursor-pointer relative">
                <div className="flex gap-3">
                    {/* Avatar */}
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-stone-100 text-stone-500 text-xs font-semibold flex-shrink-0">
                        {initials}
                    </span>

                    {/* Center content */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-2">
                            <p className="text-sm font-semibold text-stone-900 truncate flex-1">
                                {meeting.title}
                            </p>
                            {/* Right area: StatusBadge + menu */}
                            <div className="flex items-center gap-2 flex-shrink-0">
                                <StatusBadge status={meeting.status} subStatus={meeting.sub_status} />
                                {!isProcessing && (
                                    <DropdownMenu>
                                        <DropdownMenuTrigger
                                            render={<button className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" />}
                                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
                                        >
                                            <MoreVertical className="size-4" />
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end" onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}>
                                            <DropdownMenuItem
                                                className="text-destructive focus:text-destructive"
                                                onClick={handleDeleteClick}
                                            >
                                                <Trash2 />
                                                Delete
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                )}
                            </div>
                        </div>

                        {/* Metadata subtitle */}
                        <p className="text-xs text-stone-500 flex items-center gap-1">
                            {meeting.source_type === "youtube" && (
                                <svg className="w-3 h-3 text-red-500 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0C.488 3.45.029 5.804 0 12c.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0C23.512 20.55 23.971 18.196 24 12c-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 4-8 4z"/>
                                </svg>
                            )}
                            {metaParts.join(" · ")}
                        </p>

                        {/* Summary preview — only for completed meetings with actual summary text */}
                        {hasSummary && (
                            <div>
                                <p className="line-clamp-3 text-sm text-stone-700 leading-relaxed mt-1.5">
                                    {stripMarkdown(meeting.summary_text!)}
                                </p>
                                {meeting.summary_text!.length > 200 && (
                                    <p className="text-xs text-primary font-medium mt-1">Show more</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Link>
        <AlertDialog open={confirmingDelete} onOpenChange={setConfirmingDelete}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Delete meeting?</AlertDialogTitle>
                    <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                        onClick={() => { setConfirmingDelete(false); onDelete(meeting.id); }}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                        Delete
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
        </>
    );
}

function SkeletonCard() {
    return (
        <div className="bg-white rounded-lg border border-stone-200 p-4 flex gap-3 animate-pulse">
            <div className="w-8 h-8 rounded-full bg-stone-100 flex-shrink-0" />
            <div className="flex-1 space-y-2">
                <div className="h-3.5 bg-stone-100 rounded-lg w-2/3" />
                <div className="h-3 bg-stone-100 rounded-lg w-full" />
                <div className="h-3 bg-stone-100 rounded-lg w-4/5" />
            </div>
        </div>
    );
}

// ── Collapsible date group ────────────────────────────────────────────────────

function DateGroup({
    label,
    meetings: groupMeetings,
    onDelete,
}: {
    label: string;
    meetings: Meeting[];
    onDelete: (id: number) => void;
}) {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <div>
            {/* Date group header */}
            <button
                type="button"
                onClick={() => setCollapsed((prev) => !prev)}
                className="flex items-center justify-between cursor-pointer py-1 mb-2 w-full"
            >
                <p className="text-sm font-medium text-stone-500">{label}</p>
                <ChevronDown
                    className={`w-4 h-4 text-stone-400 transition-transform duration-150 ${collapsed ? "rotate-180" : ""}`}
                />
            </button>
            {!collapsed && (
                <div>
                    {groupMeetings.map((m) => (
                        <MeetingFeedCard key={m.id} meeting={m} onDelete={onDelete} />
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Main feed component ───────────────────────────────────────────────────────

const PAGE_SIZE = 5;

export function MeetingFeed() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refreshFeed = () => {
        getMeetings(0, PAGE_SIZE)
            .then((data) => {
                const results = data ?? [];
                setMeetings(results);
                setHasMore(results.length >= PAGE_SIZE);
            })
            .catch(() => setError("Could not load meetings."))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        refreshFeed();

        const handleRefresh = () => refreshFeed();
        window.addEventListener("youtube-url-submitted", handleRefresh);
        window.addEventListener("meeting-processing-complete", handleRefresh);
        return () => {
            window.removeEventListener("youtube-url-submitted", handleRefresh);
            window.removeEventListener("meeting-processing-complete", handleRefresh);
        };
    }, []);

    const loadMore = async () => {
        setLoadingMore(true);
        try {
            const data = await getMeetings(meetings.length, PAGE_SIZE);
            const results = data ?? [];
            setMeetings((prev) => [...prev, ...results]);
            setHasMore(results.length >= PAGE_SIZE);
        } catch {
            // Silently fail — user can retry
        } finally {
            setLoadingMore(false);
        }
    };

    // Poll while any meeting is actively processing
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
    useEffect(() => {
        const hasActive = meetings.some(isActiveMeeting);
        if (hasActive && !pollRef.current) {
            pollRef.current = setInterval(async () => {
                try {
                    const data = await getMeetings(0, meetings.length);
                    setMeetings(data ?? []);
                } catch { /* ignore poll errors */ }
            }, 5000);
        } else if (!hasActive && pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }
        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        };
    }, [meetings]);

    const handleDeleteFromFeed = async (id: number) => {
        try {
            const { deleteMeeting } = await import("@/app/lib/api");
            await deleteMeeting(id);
            setMeetings((prev) => prev.filter((m) => m.id !== id));
        } catch (err) {
            console.error("Failed to delete meeting", err);
            alert("Failed to delete meeting. Please try again.");
        }
    };

    if (loading) {
        return (
            <div className="space-y-2">
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
                {error}
            </div>
        );
    }

    if (meetings.length === 0) {
        return (
            <div className="text-center py-12">
                <div className="w-12 h-12 rounded-lg bg-stone-100 flex items-center justify-center mx-auto mb-4">
                    <svg className="w-6 h-6 text-stone-400" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                        <path d="M14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                    </svg>
                </div>
                <p className="text-stone-700 font-medium mb-1">No meetings yet</p>
                <p className="text-sm text-stone-400 mb-4">
                    Import your first recording to get started.
                </p>
                <Button onClick={() => window.dispatchEvent(new Event('open-upload-modal'))}>Import a meeting</Button>
            </div>
        );
    }

    const sorted = [...meetings].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    const groups = groupByDate(sorted);

    return (
        <div className="space-y-6">
            {groups.map(({ label, meetings: groupMeetings }) => (
                <DateGroup
                    key={label}
                    label={label}
                    meetings={groupMeetings}
                    onDelete={handleDeleteFromFeed}
                />
            ))}

            {hasMore && (
                <div className="flex justify-center pt-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={loadMore}
                        loading={loadingMore}
                    >
                        View more
                    </Button>
                </div>
            )}
        </div>
    );
}
