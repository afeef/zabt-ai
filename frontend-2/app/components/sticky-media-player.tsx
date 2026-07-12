// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useEffect, useRef, useState } from "react";
import { useTranscriptStore } from "@/app/lib/use-transcript-store";
import { Meeting } from "@/app/lib/api";
import { Play, Pause, RotateCcw } from "lucide-react";

export function StickyMediaPlayer({ meeting }: { meeting: Meeting }) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const rafRef = useRef<number | null>(null);
    const { setCurrentTime, seekRequest, setSeekRequest, setIsPlaying, currentTime } = useTranscriptStore();

    const [playbackRate, setPlaybackRate] = useState(1);
    const [duration, setDuration] = useState(meeting.duration_seconds || 0);

    // Sync seek requests from the UI (Transcript words clicking) to the native player
    useEffect(() => {
        if (seekRequest !== null && audioRef.current) {
            audioRef.current.currentTime = seekRequest;
            setSeekRequest(null);
        }
    }, [seekRequest, setSeekRequest]);

    // High performance time tracking loop using RequestAnimationFrame
    const loop = () => {
        if (audioRef.current && !audioRef.current.paused) {
            setCurrentTime(audioRef.current.currentTime);
            rafRef.current = requestAnimationFrame(loop);
        }
    };

    const togglePlay = () => {
        if (audioRef.current) {
            if (audioRef.current.paused) {
                audioRef.current.play();
            } else {
                audioRef.current.pause();
            }
        }
    };

    const handleRewind = () => {
        if (audioRef.current) {
            audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
            setCurrentTime(audioRef.current.currentTime);
        }
    };

    const toggleSpeed = () => {
        const nextSpeed = playbackRate === 1 ? 1.5 : playbackRate === 1.5 ? 2 : 1;
        setPlaybackRate(nextSpeed);
        if (audioRef.current) {
            audioRef.current.playbackRate = nextSpeed;
        }
    };

    const getSpeakerColor = (speaker: string) => {
        if (speaker === "SPEAKER_00") return "bg-stone-500";
        if (speaker === "SPEAKER_01") return "bg-amber-600";
        if (speaker === "SPEAKER_02") return "bg-teal-600";
        return "bg-stone-300";
    };

    const formatTime = (secs: number) => {
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60);
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const audioSrc = meeting.audio_url || meeting.file_path;

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-stone-200 z-50 px-6 py-4 pb-safe">
            <div className="max-w-5xl mx-auto flex flex-col gap-3">

                {/* Progress Bar with Speaker Segments */}
                <div className="w-full h-1 bg-stone-100 rounded-lg relative group cursor-pointer overflow-hidden"
                    onClick={(e) => {
                        // Simple seek to click position
                        if (!audioRef.current) return;
                        const bounds = e.currentTarget.getBoundingClientRect();
                        const percent = (e.clientX - bounds.left) / bounds.width;
                        const newTime = percent * duration;
                        setSeekRequest(newTime);
                    }}
                >
                    {/* Base mapped segments */}
                    {meeting.segments?.map((seg, i) => {
                        const left = (seg.start / duration) * 100;
                        const width = ((seg.end - seg.start) / duration) * 100;
                        return (
                            <div
                                key={i}
                                className={`absolute top-0 bottom-0 ${getSpeakerColor(seg.speaker)} opacity-30`}
                                style={{ left: `${left}%`, width: `${width}%` }}
                            />
                        );
                    })}

                    {/* Active progress fill */}
                    <div
                        className="absolute top-0 bottom-0 left-0 bg-primary transition-all duration-75"
                        style={{ width: `${(currentTime / duration) * 100}%` }}
                    />
                </div>

                {/* Controls */}
                <div className="flex items-center justify-between">

                    {/* Left: Time + Main Controls */}
                    <div className="flex items-center gap-6">
                        <span className="text-xs font-medium text-stone-500 w-10 text-right font-mono">
                            {formatTime(currentTime)}
                        </span>

                        <div className="flex items-center gap-4">
                            <button onClick={handleRewind} className="hover:text-stone-900 text-stone-500 transition">
                                <RotateCcw className="w-5 h-5" />
                            </button>

                            <button onClick={togglePlay} className="w-8 h-8 flex items-center justify-center rounded-full bg-stone-900 text-white hover:bg-stone-800 transition-colors">
                                {audioRef.current?.paused === false ? (
                                    <Pause className="w-4 h-4 fill-current" />
                                ) : (
                                    <Play className="w-4 h-4 fill-current ml-0.5" />
                                )}
                            </button>

                            <button
                                onClick={toggleSpeed}
                                className="hover:text-stone-900 text-stone-500 font-medium text-sm w-6 text-center transition"
                            >
                                {playbackRate}x
                            </button>
                        </div>

                        <span className="text-xs font-medium text-stone-400 w-10 font-mono">
                            {formatTime(duration)}
                        </span>
                    </div>

                    {/* Spacer for balanced layout */}
                    <div />
                </div>

            </div>

            {/* Hidden Native Audio Element */}
            <audio
                ref={audioRef}
                src={audioSrc}
                onPlay={() => {
                    setIsPlaying(true);
                    rafRef.current = requestAnimationFrame(loop);
                }}
                onPause={() => {
                    setIsPlaying(false);
                    if (rafRef.current) cancelAnimationFrame(rafRef.current);
                }}
                onEnded={() => {
                    setIsPlaying(false);
                    if (rafRef.current) cancelAnimationFrame(rafRef.current);
                }}
                onLoadedMetadata={(e) => {
                    if (!meeting.duration_seconds) {
                        setDuration(e.currentTarget.duration);
                    }
                }}
            />
        </div>
    );
}
