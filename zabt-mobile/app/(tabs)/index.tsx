// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { useMemo } from "react";
import { ActivityIndicator, FlatList, RefreshControl, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import type { Meeting } from "@zabt/shared";
import { MeetingCard } from "@/components/meeting-card";
import { EmptyState } from "@/components/empty-state";
import { useMeetings } from "@/lib/queries";

export default function Home() {
  const {
    data,
    isLoading,
    refetch,
    isRefetching,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useMeetings();

  // Dedupe by id — offset pagination + polling can surface the same row on
  // two pages when a new meeting lands between fetches (skip=0 shifts).
  const meetings = useMemo(() => {
    const seen = new Set<number>();
    const out: Meeting[] = [];
    for (const page of data?.pages ?? []) {
      for (const m of page) {
        if (!seen.has(m.id)) {
          seen.add(m.id);
          out.push(m);
        }
      }
    }
    return out;
  }, [data]);

  return (
    <SafeAreaView className="flex-1 bg-background" edges={["top"]}>
      <View className="px-6 pt-4 pb-2 border-b border-border">
        <Text className="text-2xl font-bold text-foreground">Zabt</Text>
      </View>

      <FlatList
        data={meetings}
        keyExtractor={(m) => m.id.toString()}
        renderItem={({ item }) => <MeetingCard meeting={item} />}
        contentContainerStyle={
          meetings.length === 0 ? { flex: 1 } : { padding: 16 }
        }
        ItemSeparatorComponent={() => <View className="h-3" />}
        ListEmptyComponent={
          isLoading ? (
            <View className="flex-1 items-center justify-center">
              <ActivityIndicator color="#e11d74" />
            </View>
          ) : (
            <EmptyState
              title="No meetings yet"
              description="Tap the pink record button to capture your first meeting."
            />
          )
        }
        ListFooterComponent={
          isFetchingNextPage ? (
            <View className="py-6 items-center">
              <ActivityIndicator color="#e11d74" />
            </View>
          ) : null
        }
        onEndReached={() => {
          if (hasNextPage && !isFetchingNextPage) fetchNextPage();
        }}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching && !isFetchingNextPage}
            onRefresh={refetch}
            tintColor="#e11d74"
          />
        }
      />
    </SafeAreaView>
  );
}
