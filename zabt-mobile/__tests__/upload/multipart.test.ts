// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
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

import { runMultipartUpload, type MultipartApi } from "../../lib/upload/multipart";

function makeApi(overrides: Partial<MultipartApi> = {}): jest.Mocked<MultipartApi> {
  return {
    initiate: jest.fn(),
    putPart: jest.fn(),
    complete: jest.fn(),
    refreshPartUrl: jest.fn(),
    ...overrides,
  } as jest.Mocked<MultipartApi>;
}

describe("runMultipartUpload", () => {
  beforeEach(() => {
    mockStore.clear();
  });

  test("initiates, uploads parts, and completes", async () => {
    const api = makeApi();
    api.initiate.mockResolvedValue({
      upload_id: "u1",
      s3_key: "users/1/audio.m4a",
      part_urls: [
        { part_number: 1, url: "https://s3/part1" },
        { part_number: 2, url: "https://s3/part2" },
      ],
    });
    api.putPart.mockImplementation(async (url: string) => `etag-${url.slice(-1)}`);
    api.complete.mockResolvedValue({ s3_key: "users/1/audio.m4a" });

    const result = await runMultipartUpload({
      localUri: "file:///tmp/audio.m4a",
      totalSize: 10 * 1024 * 1024,
      chunkSize: 5 * 1024 * 1024,
      contentType: "audio/mp4",
      api,
      onProgress: () => {},
    });

    expect(api.initiate).toHaveBeenCalledWith({
      filename: "audio.m4a",
      content_type: "audio/mp4",
      total_parts: 2,
    });
    expect(api.putPart).toHaveBeenCalledTimes(2);
    expect(api.complete).toHaveBeenCalledWith({
      s3_key: "users/1/audio.m4a",
      upload_id: "u1",
      parts: [
        { part_number: 1, etag: "etag-1" },
        { part_number: 2, etag: "etag-2" },
      ],
    });
    expect(result.s3Key).toBe("users/1/audio.m4a");
  });

  test("retries failed parts with exponential backoff then throws", async () => {
    const api = makeApi();
    api.initiate.mockResolvedValue({
      upload_id: "u1",
      s3_key: "key",
      part_urls: [{ part_number: 1, url: "https://s3/p1" }],
    });
    api.putPart.mockRejectedValue(new Error("network"));
    api.refreshPartUrl.mockResolvedValue("https://s3/p1-new");

    await expect(
      runMultipartUpload({
        localUri: "file:///a.m4a",
        totalSize: 1000,
        chunkSize: 1000,
        contentType: "audio/mp4",
        api,
        onProgress: () => {},
        maxRetries: 3,
      })
    ).rejects.toThrow(/part 1 failed after 3 attempts/);

    expect(api.putPart).toHaveBeenCalledTimes(3);
    expect(api.complete).not.toHaveBeenCalled();
  });

  test("reports monotonic progress ending at 1.0", async () => {
    const api = makeApi();
    api.initiate.mockResolvedValue({
      upload_id: "u2",
      s3_key: "k",
      part_urls: [
        { part_number: 1, url: "https://s3/1" },
        { part_number: 2, url: "https://s3/2" },
        { part_number: 3, url: "https://s3/3" },
        { part_number: 4, url: "https://s3/4" },
      ],
    });
    api.putPart.mockResolvedValue("etag");
    api.complete.mockResolvedValue({ s3_key: "k" });

    const progress: number[] = [];
    await runMultipartUpload({
      localUri: "file:///a.m4a",
      totalSize: 4 * 1000,
      chunkSize: 1000,
      contentType: "audio/mp4",
      api,
      onProgress: (fraction) => progress.push(fraction),
    });

    expect(progress[progress.length - 1]).toBeCloseTo(1.0, 5);
    // progress is monotonic non-decreasing
    for (let i = 1; i < progress.length; i++) {
      expect(progress[i]).toBeGreaterThanOrEqual(progress[i - 1]);
    }
  });

  test("resumes: skips parts already in the queue from a previous run", async () => {
    // Simulate prior run that completed part 1.
    mockStore.set(
      "@zabt/upload/u3",
      JSON.stringify({
        completed: [{ partNumber: 1, etag: "previously-done" }],
      })
    );

    const api = makeApi();
    api.initiate.mockResolvedValue({
      upload_id: "u3",
      s3_key: "k",
      part_urls: [
        { part_number: 1, url: "https://s3/1" },
        { part_number: 2, url: "https://s3/2" },
      ],
    });
    api.putPart.mockResolvedValue("etag-2");
    api.complete.mockResolvedValue({ s3_key: "k" });

    await runMultipartUpload({
      localUri: "file:///a.m4a",
      totalSize: 2000,
      chunkSize: 1000,
      contentType: "audio/mp4",
      api,
      onProgress: () => {},
    });

    // Only part 2 should be re-uploaded; part 1 resumed from queue
    expect(api.putPart).toHaveBeenCalledTimes(1);
    expect(api.complete).toHaveBeenCalledWith({
      s3_key: "k",
      upload_id: "u3",
      parts: [
        { part_number: 1, etag: "previously-done" },
        { part_number: 2, etag: "etag-2" },
      ],
    });
  });

  test("uses refreshPartUrl if no URL in the initial map", async () => {
    const api = makeApi();
    api.initiate.mockResolvedValue({
      upload_id: "u4",
      s3_key: "k",
      // Note: no URL for part 2 in initial response (simulating server behavior)
      part_urls: [{ part_number: 1, url: "https://s3/1" }],
    });
    api.putPart.mockResolvedValue("etag");
    api.refreshPartUrl.mockResolvedValue("https://s3/2-refreshed");
    api.complete.mockResolvedValue({ s3_key: "k" });

    await runMultipartUpload({
      localUri: "file:///a.m4a",
      totalSize: 2000,
      chunkSize: 1000,
      contentType: "audio/mp4",
      api,
      onProgress: () => {},
    });

    expect(api.refreshPartUrl).toHaveBeenCalledWith({
      s3_key: "k",
      upload_id: "u4",
      part_number: 2,
    });
  });
});
