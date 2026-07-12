// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import AsyncStorage from "@react-native-async-storage/async-storage";

export interface CompletedPart {
  partNumber: number;
  etag: string;
}

interface QueueState {
  completed: CompletedPart[];
}

/**
 * Per-upload persisted retry state. Survives app restarts so a resumed upload
 * can skip parts that already completed. Keyed by the S3 uploadId so each
 * multipart session gets isolated state.
 */
export class RetryQueue {
  private state: QueueState = { completed: [] };
  private readonly storageKey: string;

  constructor(uploadId: string) {
    this.storageKey = `@zabt/upload/${uploadId}`;
  }

  async load(): Promise<void> {
    const raw = await AsyncStorage.getItem(this.storageKey);
    if (raw) {
      try {
        this.state = JSON.parse(raw) as QueueState;
      } catch {
        this.state = { completed: [] };
      }
    }
  }

  async recordSuccess(partNumber: number, etag: string): Promise<void> {
    if (!this.state.completed.find((p) => p.partNumber === partNumber)) {
      this.state.completed.push({ partNumber, etag });
      this.state.completed.sort((a, b) => a.partNumber - b.partNumber);
      await AsyncStorage.setItem(this.storageKey, JSON.stringify(this.state));
    }
  }

  shouldAttempt(partNumber: number): boolean {
    return !this.state.completed.find((p) => p.partNumber === partNumber);
  }

  getCompletedParts(): CompletedPart[] {
    return [...this.state.completed];
  }

  async clear(): Promise<void> {
    this.state = { completed: [] };
    await AsyncStorage.removeItem(this.storageKey);
  }
}
