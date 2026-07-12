// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { planChunks } from "./chunker";
import { RetryQueue } from "./queue";

/**
 * Upload state machine for S3 multipart uploads. Pure orchestration — I/O is
 * injected via the `MultipartApi` interface so tests can mock it completely.
 */

interface PartUrl {
  part_number: number;
  url: string;
}

interface InitiateResponse {
  upload_id: string;
  s3_key: string;
  part_urls: PartUrl[];
}

interface CompleteResponse {
  s3_key: string;
}

export interface MultipartApi {
  initiate(payload: {
    filename: string;
    content_type: string;
    total_parts: number;
  }): Promise<InitiateResponse>;

  /** Upload a single part. Returns the S3 ETag (without quotes). */
  putPart(
    url: string,
    uri: string,
    offset: number,
    size: number
  ): Promise<string>;

  complete(payload: {
    s3_key: string;
    upload_id: string;
    parts: { part_number: number; etag: string }[];
  }): Promise<CompleteResponse>;

  refreshPartUrl(payload: {
    s3_key: string;
    upload_id: string;
    part_number: number;
  }): Promise<string>;
}

export interface MultipartOptions {
  localUri: string;
  totalSize: number;
  chunkSize: number;
  contentType: string;
  api: MultipartApi;
  onProgress: (fraction: number) => void;
  maxRetries?: number;
}

const filenameFromUri = (uri: string): string => {
  const segment = uri.split("/").pop();
  return segment && segment.length > 0 ? segment : "recording.m4a";
};

export async function runMultipartUpload(
  opts: MultipartOptions
): Promise<{ s3Key: string }> {
  const { localUri, totalSize, chunkSize, contentType, api, onProgress } = opts;
  const maxRetries = opts.maxRetries ?? 5;

  const plan = planChunks(totalSize, chunkSize);

  const {
    upload_id: uploadId,
    s3_key: s3Key,
    part_urls: partUrls,
  } = await api.initiate({
    filename: filenameFromUri(localUri),
    content_type: contentType,
    total_parts: plan.length,
  });

  const queue = new RetryQueue(uploadId);
  await queue.load();

  const urlMap = new Map<number, string>();
  partUrls.forEach((pu) => urlMap.set(pu.part_number, pu.url));

  // Resume: count bytes already uploaded so progress doesn't start at 0.
  let completedBytes = 0;
  const existing = queue.getCompletedParts();
  existing.forEach((p) => {
    const chunk = plan.find((c) => c.partNumber === p.partNumber);
    if (chunk) completedBytes += chunk.size;
  });
  onProgress(completedBytes / totalSize);

  for (const chunk of plan) {
    if (!queue.shouldAttempt(chunk.partNumber)) continue;

    let attempts = 0;
    let etag: string | null = null;
    let lastErr: unknown = null;
    while (attempts < maxRetries && etag === null) {
      attempts++;
      try {
        let url = urlMap.get(chunk.partNumber);
        if (!url) {
          url = await api.refreshPartUrl({
            s3_key: s3Key,
            upload_id: uploadId,
            part_number: chunk.partNumber,
          });
          urlMap.set(chunk.partNumber, url);
        }
        etag = await api.putPart(url, localUri, chunk.offset, chunk.size);
      } catch (err) {
        lastErr = err;
        console.warn(`[upload] part ${chunk.partNumber} attempt ${attempts} failed:`, err);
        if (attempts >= maxRetries) {
          const detail = err instanceof Error ? err.message : String(err);
          throw new Error(
            `part ${chunk.partNumber} failed after ${attempts} attempts: ${detail}`
          );
        }
        const backoffMs = Math.min(30_000, 500 * 2 ** (attempts - 1));
        await new Promise((r) => setTimeout(r, backoffMs));
      }
    }
    void lastErr;

    await queue.recordSuccess(chunk.partNumber, etag!);
    completedBytes += chunk.size;
    onProgress(completedBytes / totalSize);
  }

  const completed = queue.getCompletedParts();
  const response = await api.complete({
    s3_key: s3Key,
    upload_id: uploadId,
    parts: completed.map((p) => ({ part_number: p.partNumber, etag: p.etag })),
  });
  await queue.clear();

  return { s3Key: response.s3_key };
}
