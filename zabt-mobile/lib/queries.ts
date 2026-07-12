// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type { Meeting, MeetingList, User } from "@zabt/shared";
import { api } from "./api";

const POLL_MS = 5000;
export const MEETINGS_PAGE_SIZE = 10;

function isActive(m: Meeting): boolean {
  return m.status === "queued" || m.status === "processing";
}

function pageItems(data: MeetingList | Meeting[]): Meeting[] {
  return Array.isArray(data) ? data : data.items;
}

export function useMeetings() {
  return useInfiniteQuery({
    queryKey: ["meetings"],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const response = await api.get<MeetingList | Meeting[]>(
        `/meetings/?skip=${pageParam}&limit=${MEETINGS_PAGE_SIZE}`
      );
      return pageItems(response.data);
    },
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length < MEETINGS_PAGE_SIZE
        ? undefined
        : allPages.reduce((sum, p) => sum + p.length, 0),
    // Only poll the FIRST page while any visible meeting is active. Refetching
    // every page on each poll would be wasteful and disrupt scroll position.
    refetchInterval: (query) => {
      const all = query.state.data?.pages.flat() ?? [];
      return all.some(isActive) ? POLL_MS : false;
    },
  });
}

export function useMeeting(id: number | string | undefined) {
  return useQuery<Meeting>({
    queryKey: ["meeting", id],
    queryFn: async () => {
      const response = await api.get<Meeting>(`/meetings/${id}`);
      return response.data;
    },
    enabled: id !== undefined && id !== null && id !== "",
    refetchInterval: (query) =>
      query.state.data && isActive(query.state.data) ? POLL_MS : false,
  });
}

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ["me"],
    queryFn: async () => {
      const response = await api.get<User>("/users/me");
      return response.data;
    },
  });
}
