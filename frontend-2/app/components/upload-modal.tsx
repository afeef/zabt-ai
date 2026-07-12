import { useRef, useState, useEffect } from "react";
import axios from "axios";
import { usePostHog } from "posthog-js/react";
import { Stethoscope, AudioLines } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog";
import apiClient, { MeetingType } from "@/app/lib/api";
import { MeetingTypeSelector } from "@/app/components/meeting-type-selector";
import { LanguagePicker } from "@/app/components/LanguagePicker";
import { useProcessingQueue } from "@/app/contexts/processing-queue-context";

export interface UploadItem {
    id: string;
    file: File;
    progress: number;
    loadedBytes: number;
    totalBytes: number;
    status: "uploading" | "success" | "error" | "cancelled";
    abortController: AbortController;
    meetingId?: number;
}

interface UploadModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
}

function getFileSizeTier(bytes: number): "small" | "medium" | "large" {
    const mb = bytes / (1024 * 1024);
    if (mb < 10) return "small";
    if (mb <= 100) return "medium";
    return "large";
}

function formatBytes(bytes: number, decimals = 1) {
    if (!+bytes) return '0 Bytes'
    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

export function UploadModal({ isOpen, onOpenChange }: UploadModalProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploads, setUploads] = useState<UploadItem[]>([]);
    const [transcriptionType, setTranscriptionType] = useState<"general" | "medical">("general");
    const [meetingType, setMeetingType] = useState<MeetingType>("generic");
    const [language, setLanguage] = useState<string | null>(null);
    const posthog = usePostHog();
    const { addItem } = useProcessingQueue();

    // Track which meetingIds have already been pushed to the queue
    const pushedToQueue = useRef<Set<number>>(new Set());

    // Close on Escape key
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape" && isOpen) {
                handleCloseRequest();
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen]);

    // Push completed uploads to the processing queue and auto-close when all done
    useEffect(() => {
        for (const item of uploads) {
            if (item.status === "success" && item.meetingId && !pushedToQueue.current.has(item.meetingId)) {
                pushedToQueue.current.add(item.meetingId);
                addItem(item.meetingId, item.file.name, "upload");
            }
        }

        // Auto-close once all uploads are finished (no active uploads remaining)
        if (uploads.length > 0 && uploads.every((u) => u.status !== "uploading")) {
            const allSuccess = uploads.every((u) => u.status === "success");
            if (allSuccess) {
                const timer = setTimeout(() => {
                    onOpenChange(false);
                    setUploads([]);
                    pushedToQueue.current.clear();
                }, 800);
                return () => clearTimeout(timer);
            }
        }
    }, [uploads, addItem, onOpenChange]);

    const handleCloseRequest = () => {
        const hasActive = uploads.some((u) => u.status === "uploading");
        if (hasActive) {
            if (!window.confirm("Upload in progress. Cancel anyway?")) {
                return;
            }
            cancelAll();
        }
        onOpenChange(false);
    };

    const handleFileSelect = (files: File[]) => {
        const newUploads: UploadItem[] = [];

        files.forEach((file) => {
            if (file.size > 2147483648) {
                alert(`File ${file.name} is larger than 2GB.`);
                return;
            }

            const item: UploadItem = {
                id: crypto.randomUUID(),
                file,
                progress: 0,
                loadedBytes: 0,
                totalBytes: file.size,
                status: "uploading",
                abortController: new AbortController(),
            };
            newUploads.push(item);
        });

        if (newUploads.length > 0) {
            setUploads((prev) => [...newUploads, ...prev]);
            newUploads.forEach(startUpload);
        }

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const startUpload = async (item: UploadItem) => {
        try {
            const { data: presignedData } = await apiClient.post<{ upload_url: string; file_key: string; storage_provider: string }>(
                "/meetings/presigned-upload",
                { filename: item.file.name, content_type: item.file.type || "audio/mpeg" },
                { signal: item.abortController.signal }
            );

            const { data: meetingData } = await apiClient.post<{ id: number }>("/meetings/", {
                title: item.file.name,
                file_key: presignedData.file_key,
                transcription_type: transcriptionType,
                meeting_type: meetingType,
                ...(language ? { language } : {}),
            }, { signal: item.abortController.signal });

            await axios.put(presignedData.upload_url, item.file, {
                headers: { "Content-Type": item.file.type || "audio/mpeg" },
                signal: item.abortController.signal,
                onUploadProgress: (progressEvent: any) => {
                    const loaded = progressEvent.loaded;
                    const total = progressEvent.total || item.file.size;
                    const progress = Math.round((loaded * 100) / total);

                    setUploads((prev) =>
                        prev.map((u) =>
                            u.id === item.id
                                ? { ...u, progress, loadedBytes: loaded, totalBytes: total }
                                : u
                        )
                    );
                },
            });

            if (presignedData.storage_provider === "s3") {
                await apiClient.post(`/meetings/${meetingData.id}/confirm-upload`, null, {
                    signal: item.abortController.signal,
                });
            }

            setUploads((prev) =>
                prev.map((u) => u.id === item.id ? { ...u, status: "success", progress: 100, meetingId: meetingData.id } : u)
            );
            posthog?.capture('upload_completed', {
                file_size_tier: getFileSizeTier(item.file.size),
                file_type: item.file.type || "audio/mpeg",
                transcription_type: transcriptionType,
            });
        } catch (err: any) {
            if (err.name === "CanceledError" || err.message === "canceled") {
                setUploads((prev) =>
                    prev.map((u) => u.id === item.id ? { ...u, status: "cancelled" } : u)
                );
            } else {
                console.error("Upload error:", err);
                setUploads((prev) =>
                    prev.map((u) => u.id === item.id ? { ...u, status: "error" } : u)
                );
            }
        }
    };

    const cancelUpload = (id: string) => {
        const item = uploads.find((u) => u.id === id);
        if (item && item.status === "uploading") {
            item.abortController.abort();
        }
    };

    const cancelAll = () => {
        uploads.forEach((u) => {
            if (u.status === "uploading") {
                u.abortController.abort();
            }
        });
    };

    return (
        <Dialog
            open={isOpen}
            onOpenChange={(open) => {
                if (!open) handleCloseRequest();
            }}
        >
            <DialogContent className="sm:max-w-lg max-h-[90vh] flex flex-col p-0">

                {/* Header */}
                <DialogHeader className="px-6 py-4 border-b border-border flex-shrink-0">
                    <DialogTitle>Transcribe audio and video</DialogTitle>
                </DialogHeader>

                {/* Scrollable Body area */}
                <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center">

                    {/* Zero State / Upload Trigger */}
                    <div className="flex flex-col items-center text-center w-full mb-6 py-4">
                        <div className="w-12 h-12 bg-stone-100 rounded-lg flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                            </svg>
                        </div>
                        <h3 className="text-sm font-medium text-stone-900 mb-1">Select a file to upload</h3>
                        <p className="text-xs text-stone-500 mb-4">MP4, MOV, MP3, WAV, or M4A up to 2GB</p>

                        {/* Transcription Type Selector */}
                        <div className="flex gap-2 mb-6 w-full max-w-xs">
                            <button
                                type="button"
                                onClick={() => setTranscriptionType("general")}
                                className={`flex-1 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                                    transcriptionType === "general"
                                        ? "border-primary bg-primary/10 text-primary font-medium"
                                        : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50"
                                }`}
                            >
                                <AudioLines className="size-4" />
                                General
                            </button>
                            <button
                                type="button"
                                onClick={() => setTranscriptionType("medical")}
                                className={`flex-1 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                                    transcriptionType === "medical"
                                        ? "border-primary bg-primary/10 text-primary font-medium"
                                        : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50"
                                }`}
                            >
                                <Stethoscope className="size-4" />
                                Medical
                            </button>
                        </div>

                        {/* Meeting Type Selector */}
                        <div className="w-full max-w-sm mb-4">
                            <p className="text-xs text-stone-500 mb-2 text-left">Meeting type</p>
                            <MeetingTypeSelector value={meetingType} onChange={setMeetingType} size="sm" variant="buttons" />
                        </div>

                        {/* Language Picker */}
                        <div className="w-full max-w-sm mb-4">
                            <p className="text-xs text-stone-500 mb-2 text-left">Language</p>
                            <LanguagePicker value={language} onChange={setLanguage} />
                        </div>

                        <input
                            type="file"
                            multiple
                            ref={fileInputRef}
                            className="hidden"
                            accept="audio/*,video/*,.mp4,.mov,.mp3,.wav,.m4a"
                            onChange={(e) => handleFileSelect(Array.from(e.target.files || []))}
                        />

                        <Button onClick={() => fileInputRef.current?.click()} size="default" className="gap-2">
                            Browse files
                        </Button>
                    </div>

                    {/* List of ongoing/completed uploads */}
                    {uploads.length > 0 && (
                        <div className="w-full space-y-3">
                            {uploads.map((item) => (
                                <div key={item.id} className="w-full bg-white border border-stone-200 rounded-lg p-4">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-3 overflow-hidden">
                                            {/* Icon */}
                                            <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                                                item.status === 'success' ? 'bg-emerald-100 text-emerald-600' :
                                                item.status === 'error' ? 'bg-red-100 text-red-600' :
                                                    item.status === 'cancelled' ? 'bg-stone-100 text-stone-500' :
                                                        'bg-primary/10 text-primary'
                                                }`}>
                                                {item.status === 'success' ? (
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                                                ) : item.status === 'error' || item.status === 'cancelled' ? (
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                                                ) : (
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                                                )}
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-medium text-stone-900 truncate">{item.file.name}</p>
                                                <p className="text-xs text-stone-500 truncate">
                                                    {item.status === 'uploading' && `${formatBytes(item.loadedBytes)} of ${formatBytes(item.totalBytes)}`}
                                                    {item.status === 'success' && formatBytes(item.totalBytes)}
                                                    {item.status === 'error' && 'Upload failed'}
                                                    {item.status === 'cancelled' && 'Upload cancelled'}
                                                </p>
                                            </div>
                                        </div>

                                        {item.status === "uploading" && (
                                            <div className="flex items-center gap-3">
                                                <span className="text-xs font-semibold text-stone-700">{item.progress}%</span>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="size-7"
                                                    onClick={() => cancelUpload(item.id)}
                                                >
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                                                </Button>
                                            </div>
                                        )}
                                    </div>

                                    {/* Progress bar */}
                                    <div className="w-full bg-stone-100 rounded-lg h-1.5 overflow-hidden">
                                        <div
                                            className={`h-full transition-all duration-300 ${
                                                item.status === 'error' ? 'bg-red-500' :
                                                item.status === 'cancelled' ? 'bg-stone-300' :
                                                item.status === 'success' ? 'bg-emerald-500' :
                                                    'bg-primary'
                                                }`}
                                            style={{ width: `${item.status === 'uploading' ? item.progress : 100}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-muted/50 border-t border-border flex items-center justify-between flex-shrink-0">
                    <span className="text-xs font-medium text-muted-foreground">3 of 3 imports left</span>
                    {uploads.some(u => u.status === "uploading") ? (
                        <Button variant="ghost" size="sm" onClick={cancelAll}>Cancel all</Button>
                    ) : (
                        <Button variant="secondary" size="sm">Upgrade to Business</Button>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
