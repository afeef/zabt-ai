// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
// In-memory mock of AsyncStorage keyed on the mock's lifetime.
const mockStore = new Map<string, string>();

jest.mock("@react-native-async-storage/async-storage", () => ({
  __esModule: true,
  default: {
    getItem: jest.fn(async (k: string) => mockStore.get(k) ?? null),
    setItem: jest.fn(async (k: string, v: string) => {
      mockStore.set(k, v);
    }),
    removeItem: jest.fn(async (k: string) => {
      mockStore.delete(k);
    }),
    clear: jest.fn(async () => {
      mockStore.clear();
    }),
  },
}));

import { RetryQueue } from "../../lib/upload/queue";

describe("RetryQueue", () => {
  beforeEach(() => {
    mockStore.clear();
  });

  test("records a successful part", async () => {
    const q = new RetryQueue("upload-1");
    await q.load();
    await q.recordSuccess(1, "etag-1");
    expect(q.getCompletedParts()).toEqual([{ partNumber: 1, etag: "etag-1" }]);
  });

  test("state persists across instances", async () => {
    const q1 = new RetryQueue("upload-2");
    await q1.load();
    await q1.recordSuccess(1, "etag-a");
    await q1.recordSuccess(3, "etag-c");

    const q2 = new RetryQueue("upload-2");
    await q2.load();
    expect(q2.getCompletedParts()).toEqual([
      { partNumber: 1, etag: "etag-a" },
      { partNumber: 3, etag: "etag-c" },
    ]);
  });

  test("different uploads have separate state", async () => {
    const q1 = new RetryQueue("upload-A");
    const q2 = new RetryQueue("upload-B");
    await q1.load();
    await q2.load();
    await q1.recordSuccess(1, "a1");
    expect(q2.getCompletedParts()).toEqual([]);
  });

  test("clear removes all state", async () => {
    const q = new RetryQueue("upload-C");
    await q.load();
    await q.recordSuccess(1, "etag");
    await q.clear();
    expect(q.getCompletedParts()).toEqual([]);
  });

  test("shouldAttempt returns false for already-completed parts", async () => {
    const q = new RetryQueue("upload-D");
    await q.load();
    await q.recordSuccess(2, "etag");
    expect(q.shouldAttempt(2)).toBe(false);
    expect(q.shouldAttempt(1)).toBe(true);
  });

  test("completed parts stay sorted by part number", async () => {
    const q = new RetryQueue("upload-E");
    await q.load();
    await q.recordSuccess(3, "c");
    await q.recordSuccess(1, "a");
    await q.recordSuccess(2, "b");
    expect(q.getCompletedParts().map((p) => p.partNumber)).toEqual([1, 2, 3]);
  });
});
