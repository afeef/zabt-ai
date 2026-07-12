"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/app/lib/supabase/client";
import { AiQueryBar } from "@/app/components/ai-query-bar";
import { MeetingFeed } from "@/app/components/meeting-feed";
import { UploadModal } from "@/app/components/upload-modal";
import { YouTubeUrlDialog } from "@/app/components/youtube-url-dialog";
import { ActionBar } from "@/app/components/action-bar";
import { ProcessingQueueProvider } from "@/app/contexts/processing-queue-context";
import { ProcessingQueue } from "@/app/components/processing-queue";

function getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
}

export default function HomePage() {
    const [firstName, setFirstName] = useState("there");
    const [isUploadModalOpen, setUploadModalOpen] = useState(false);
    const [isYoutubeDialogOpen, setYoutubeDialogOpen] = useState(false);

    useEffect(() => {
        const supabase = createClient();
        supabase.auth.getUser().then(({ data }) => {
            if (data.user) {
                const full = data.user.user_metadata?.full_name as string | undefined;
                const name = full?.split(" ")[0] ?? data.user.email?.split("@")[0] ?? "there";
                setFirstName(name);
            }
        });

        const handleOpenModal = () => setUploadModalOpen(true);
        window.addEventListener('open-upload-modal', handleOpenModal);

        return () => window.removeEventListener('open-upload-modal', handleOpenModal);
    }, []);

    return (
        <ProcessingQueueProvider>
            <div className="px-8 py-8">
                {/* Greeting */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-stone-900">
                        {getGreeting()}, {firstName}.
                    </h1>
                    <p className="text-sm text-stone-500 mt-1">Here&apos;s what&apos;s happening with your meetings.</p>
                </div>

                {/* AI Query Bar */}
                <div className="mb-10">
                    <AiQueryBar />
                </div>

                {/* Section header + Action bar */}
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold text-stone-800">Your meetings</h2>
                    <ActionBar
                        onImportClick={() => setUploadModalOpen(true)}
                        onPasteUrlClick={() => setYoutubeDialogOpen(true)}
                    />
                </div>

                {/* Meeting feed */}
                <MeetingFeed />

                <UploadModal
                    isOpen={isUploadModalOpen}
                    onOpenChange={setUploadModalOpen}
                />

                <YouTubeUrlDialog
                    isOpen={isYoutubeDialogOpen}
                    onOpenChange={setYoutubeDialogOpen}
                    onSuccess={() => {
                        window.dispatchEvent(new Event("youtube-url-submitted"));
                    }}
                />

                <ProcessingQueue />
            </div>
        </ProcessingQueueProvider>
    );
}
