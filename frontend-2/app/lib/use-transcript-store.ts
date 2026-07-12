import { create } from "zustand";

interface TranscriptState {
    currentTime: number;
    duration: number;
    isPlaying: boolean;
    setCurrentTime: (time: number) => void;
    setDuration: (duration: number) => void;
    setIsPlaying: (playing: boolean) => void;
    seekRequest: number | null;
    setSeekRequest: (time: number | null) => void;
}

export const useTranscriptStore = create<TranscriptState>((set) => ({
    currentTime: 0,
    duration: 0,
    isPlaying: false,
    setCurrentTime: (time) => set({ currentTime: time }),
    setDuration: (duration) => set({ duration }),
    setIsPlaying: (playing) => set({ isPlaying: playing }),
    seekRequest: null,
    setSeekRequest: (time) => set({ seekRequest: time }),
}));
