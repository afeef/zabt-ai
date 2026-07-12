// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
/**
 * Pure file-chunking plan. No I/O — this is the spec for the uploader state machine.
 */

export interface ChunkPlan {
  /** 1-indexed part number (S3 convention). */
  partNumber: number;
  /** Byte offset from the start of the file. */
  offset: number;
  /** Size of this chunk in bytes. The last chunk may be smaller than chunkSize. */
  size: number;
}

/**
 * Split a file of `fileSize` bytes into parts of `chunkSize` bytes each.
 * The last part may be smaller than `chunkSize`. Part numbers are 1-indexed.
 */
export function planChunks(fileSize: number, chunkSize: number): ChunkPlan[] {
  if (fileSize <= 0) throw new Error("file size must be positive");
  if (chunkSize <= 0) throw new Error("chunk size must be positive");

  const plans: ChunkPlan[] = [];
  let offset = 0;
  let partNumber = 1;

  while (offset < fileSize) {
    const size = Math.min(chunkSize, fileSize - offset);
    plans.push({ partNumber, offset, size });
    offset += size;
    partNumber += 1;
  }

  return plans;
}
