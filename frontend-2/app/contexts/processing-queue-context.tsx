// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
} from "react";
import { usePostHog } from "posthog-js/react";
import { getMeeting } from "@/app/lib/api";
import { getUserStage, type UserStage } from "@/app/lib/stage-utils";

// ── Types ────────────────────────────────────────────────────────────────────

export interface QueueItem {
  id: string;
  meetingId: number;
  displayName: string;
  sourceType: "upload" | "youtube";
  stage: UserStage;
  status: "processing" | "done" | "failed";
  errorMessage: string | null;
  addedAt: number;
}

interface QueueState {
  items: QueueItem[];
  isCollapsed: boolean;
  isVisible: boolean;
}

// ── Actions ──────────────────────────────────────────────────────────────────

type QueueAction =
  | { type: "ADD_ITEM"; payload: { meetingId: number; displayName: string; sourceType: "upload" | "youtube" } }
  | { type: "UPDATE_STAGE"; payload: { meetingId: number; stage: UserStage; status?: "processing" | "done" | "failed"; errorMessage?: string | null } }
  | { type: "SET_COLLAPSED"; payload: { collapsed: boolean } }
  | { type: "SET_VISIBLE"; payload: { visible: boolean } }
  | { type: "CLEAR" };

function queueReducer(state: QueueState, action: QueueAction): QueueState {
  switch (action.type) {
    case "ADD_ITEM": {
      const exists = state.items.some((i) => i.meetingId === action.payload.meetingId);
      if (exists) return state;
      const newItem: QueueItem = {
        id: crypto.randomUUID(),
        meetingId: action.payload.meetingId,
        displayName: action.payload.displayName,
        sourceType: action.payload.sourceType,
        stage: "uploaded",
        status: "processing",
        errorMessage: null,
        addedAt: Date.now(),
      };
      return { ...state, items: [...state.items, newItem], isVisible: true };
    }
    case "UPDATE_STAGE":
      return {
        ...state,
        items: state.items.map((item) =>
          item.meetingId === action.payload.meetingId
            ? {
                ...item,
                stage: action.payload.stage,
                status: action.payload.status ?? item.status,
                errorMessage: action.payload.errorMessage ?? item.errorMessage,
              }
            : item
        ),
      };
    case "SET_COLLAPSED":
      return { ...state, isCollapsed: action.payload.collapsed };
    case "SET_VISIBLE":
      return { ...state, isVisible: action.payload.visible };
    case "CLEAR":
      return { ...state, items: [], isVisible: false };
    default:
      return state;
  }
}

// ── Context ──────────────────────────────────────────────────────────────────

interface ProcessingQueueContextValue {
  items: QueueItem[];
  isCollapsed: boolean;
  isVisible: boolean;
  addItem: (meetingId: number, displayName: string, sourceType: "upload" | "youtube") => void;
  setCollapsed: (collapsed: boolean) => void;
  clearQueue: () => void;
}

const ProcessingQueueContext = createContext<ProcessingQueueContextValue | null>(null);

export function useProcessingQueue() {
  const ctx = useContext(ProcessingQueueContext);
  if (!ctx) throw new Error("useProcessingQueue must be used within ProcessingQueueProvider");
  return ctx;
}

// ── Provider ─────────────────────────────────────────────────────────────────

const POLL_INTERVAL = 3000;
const AUTO_HIDE_DELAY = 10000;

export function ProcessingQueueProvider({ children }: { children: ReactNode }) {
  const posthog = usePostHog();
  const [state, dispatch] = useReducer(queueReducer, {
    items: [],
    isCollapsed: false,
    isVisible: false,
  });

  const pollTimers = useRef<Map<number, ReturnType<typeof setInterval>>>(new Map());
  const autoHideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Poll active items for stage updates
  useEffect(() => {
    const activeItems = state.items.filter((i) => i.status === "processing");

    for (const item of activeItems) {
      if (pollTimers.current.has(item.meetingId)) continue;

      const timer = setInterval(async () => {
        try {
          const meeting = await getMeeting(item.meetingId);
          const stage = getUserStage(meeting);
          const isFailed = stage === "failed";
          const isDone = stage === "done";

          dispatch({
            type: "UPDATE_STAGE",
            payload: {
              meetingId: item.meetingId,
              stage,
              status: isFailed ? "failed" : isDone ? "done" : "processing",
              errorMessage: isFailed ? (meeting.sub_status || "Processing failed") : null,
            },
          });

          if (isDone) {
            const duration = Math.round((Date.now() - item.addedAt) / 1000);
            posthog?.capture("processing_queue_item_completed", {
              source_type: item.sourceType,
              duration_seconds: duration,
            });
            window.dispatchEvent(new Event("meeting-processing-complete"));
          }
          if (isFailed) {
            posthog?.capture("processing_queue_item_failed", {
              source_type: item.sourceType,
              error: meeting.sub_status || "Processing failed",
            });
          }
          if (isDone || isFailed) {
            clearInterval(pollTimers.current.get(item.meetingId));
            pollTimers.current.delete(item.meetingId);
          }
        } catch {
          // Silently ignore poll errors
        }
      }, POLL_INTERVAL);

      pollTimers.current.set(item.meetingId, timer);
    }

    // Clean up timers for items no longer processing
    for (const [meetingId, timer] of pollTimers.current) {
      const item = state.items.find((i) => i.meetingId === meetingId);
      if (!item || item.status !== "processing") {
        clearInterval(timer);
        pollTimers.current.delete(meetingId);
      }
    }

    return () => {
      for (const timer of pollTimers.current.values()) clearInterval(timer);
      pollTimers.current.clear();
    };
  }, [state.items]);

  // Auto-hide 10s after all items reach terminal state
  useEffect(() => {
    if (state.items.length === 0) return;

    const allTerminal = state.items.every((i) => i.status === "done" || i.status === "failed");

    if (allTerminal) {
      autoHideTimer.current = setTimeout(() => {
        dispatch({ type: "SET_VISIBLE", payload: { visible: false } });
      }, AUTO_HIDE_DELAY);
    } else if (autoHideTimer.current) {
      clearTimeout(autoHideTimer.current);
      autoHideTimer.current = null;
    }

    return () => {
      if (autoHideTimer.current) {
        clearTimeout(autoHideTimer.current);
        autoHideTimer.current = null;
      }
    };
  }, [state.items]);

  const addItem = useCallback(
    (meetingId: number, displayName: string, sourceType: "upload" | "youtube") => {
      if (autoHideTimer.current) {
        clearTimeout(autoHideTimer.current);
        autoHideTimer.current = null;
      }
      posthog?.capture("processing_queue_item_added", { source_type: sourceType });
      dispatch({ type: "ADD_ITEM", payload: { meetingId, displayName, sourceType } });
    },
    [posthog]
  );

  const setCollapsed = useCallback((collapsed: boolean) => {
    dispatch({ type: "SET_COLLAPSED", payload: { collapsed } });
  }, []);

  const clearQueue = useCallback(() => {
    dispatch({ type: "CLEAR" });
  }, []);

  return (
    <ProcessingQueueContext.Provider
      value={{
        items: state.items,
        isCollapsed: state.isCollapsed,
        isVisible: state.isVisible,
        addItem,
        setCollapsed,
        clearQueue,
      }}
    >
      {children}
    </ProcessingQueueContext.Provider>
  );
}
