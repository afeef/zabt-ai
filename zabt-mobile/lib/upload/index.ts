// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { File } from "expo-file-system";
import * as FileSystemLegacy from "expo-file-system/legacy";
import { api } from "../api";
import { runMultipartUpload, type MultipartApi } from "./multipart";

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB — S3 multipart minimum per-part size

/**
 * Concrete MultipartApi bound to the Zabt backend and expo-file-system v19.
 * All network + disk I/O lives here. The state machine in ./multipart.ts stays
 * pure and testable.
 *
 * Per-part upload writes the slice to a temp file, then PUTs it via the legacy
 * FileSystem.uploadAsync — RN's fetch can't reliably consume Blobs from
 * File.slice() ("Creating blobs from ArrayBuffer ... not supported"). The
 * legacy uploader streams binary natively from a file path and dodges the
 * JS-side Blob path entirely.
 */
const mobileApi: MultipartApi = {
  async initiate(payload) {
    const { data } = await api.post("/uploads/initiate", payload);
    return data;
  },
  async putPart(url, uri, offset, size) {
    // Read the slice as base64 with native range read — bypasses RN Blob limits.
    const base64 = await FileSystemLegacy.readAsStringAsync(uri, {
      encoding: FileSystemLegacy.EncodingType.Base64,
      position: offset,
      length: size,
    });

    const tempPath = `${FileSystemLegacy.cacheDirectory}upload-chunk-${Date.now()}-${offset}.bin`;
    await FileSystemLegacy.writeAsStringAsync(tempPath, base64, {
      encoding: FileSystemLegacy.EncodingType.Base64,
    });

    try {
      const result = await FileSystemLegacy.uploadAsync(url, tempPath, {
        httpMethod: "PUT",
        uploadType: FileSystemLegacy.FileSystemUploadType.BINARY_CONTENT,
      });
      if (result.status < 200 || result.status >= 300) {
        throw new Error(`PUT ${result.status}: ${result.body?.slice(0, 200) ?? ""}`);
      }
      const etag = result.headers.etag ?? result.headers.ETag;
      if (!etag) throw new Error("missing ETag in response");
      return etag.replace(/"/g, "");
    } finally {
      try { await FileSystemLegacy.deleteAsync(tempPath, { idempotent: true }); } catch { /* best-effort */ }
    }
  },
  async complete(payload) {
    const { data } = await api.post("/uploads/complete", payload);
    return data;
  },
  async refreshPartUrl(payload) {
    const { data } = await api.post("/uploads/part-url", payload);
    return data.url;
  },
};

export interface UploadResult {
  meetingId: number;
}

/**
 * Upload a locally-recorded file and create its meeting record.
 *
 * Flow:
 *   1. Chunked resumable upload to S3 (via backend-issued presigned URLs).
 *   2. POST /meetings/ with the final S3 key.
 *   3. Backend Celery pipeline kicks off transcription + summary.
 *
 * Pass `onProgress` to drive a UI banner (fraction 0..1).
 */
export async function uploadMeetingRecording(
  localUri: string,
  onProgress?: (fraction: number) => void
): Promise<UploadResult> {
  const file = new File(localUri);
  if (!file.exists) throw new Error("Recording file not found");
  const size = file.size;
  if (!size) throw new Error("Empty recording");

  const { s3Key } = await runMultipartUpload({
    localUri,
    totalSize: size,
    chunkSize: CHUNK_SIZE,
    contentType: "audio/mp4",
    api: mobileApi,
    onProgress: onProgress ?? (() => {}),
  });

  const { data } = await api.post("/meetings/", {
    title: "Untitled Meeting",
    file_key: s3Key,
  });

  // Triggers the Celery transcription pipeline. Web client does the same
  // (frontend-2/app/components/upload-modal.tsx:169) — without it the meeting
  // sits in "pending upload" forever even though the file is in S3.
  await api.post(`/meetings/${data.id}/confirm-upload`);

  return { meetingId: data.id };
}
