import { planChunks } from "../../lib/upload/chunker";

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB

describe("planChunks", () => {
  test("file smaller than chunk size → single chunk", () => {
    const plan = planChunks(1_000, CHUNK_SIZE);
    expect(plan).toEqual([{ partNumber: 1, offset: 0, size: 1_000 }]);
  });

  test("file exactly chunk size → single chunk", () => {
    const plan = planChunks(CHUNK_SIZE, CHUNK_SIZE);
    expect(plan).toHaveLength(1);
    expect(plan[0]).toEqual({ partNumber: 1, offset: 0, size: CHUNK_SIZE });
  });

  test("file 2x chunk size → two full chunks", () => {
    const plan = planChunks(CHUNK_SIZE * 2, CHUNK_SIZE);
    expect(plan).toHaveLength(2);
    expect(plan[0]).toEqual({ partNumber: 1, offset: 0, size: CHUNK_SIZE });
    expect(plan[1]).toEqual({
      partNumber: 2,
      offset: CHUNK_SIZE,
      size: CHUNK_SIZE,
    });
  });

  test("file 2.5x chunk size → 3 chunks, last one smaller", () => {
    const plan = planChunks(CHUNK_SIZE * 2 + 1000, CHUNK_SIZE);
    expect(plan).toHaveLength(3);
    expect(plan[2]).toEqual({
      partNumber: 3,
      offset: CHUNK_SIZE * 2,
      size: 1000,
    });
  });

  test("zero-size file throws", () => {
    expect(() => planChunks(0, CHUNK_SIZE)).toThrow("file size must be positive");
  });

  test("zero chunk size throws", () => {
    expect(() => planChunks(100, 0)).toThrow("chunk size must be positive");
  });

  test("part numbers are 1-indexed sequential", () => {
    const plan = planChunks(CHUNK_SIZE * 5, CHUNK_SIZE);
    plan.forEach((p, idx) => {
      expect(p.partNumber).toBe(idx + 1);
    });
  });

  test("offsets are contiguous and sum matches file size", () => {
    const FILE_SIZE = CHUNK_SIZE * 3 + 12345;
    const plan = planChunks(FILE_SIZE, CHUNK_SIZE);
    let expectedOffset = 0;
    for (const chunk of plan) {
      expect(chunk.offset).toBe(expectedOffset);
      expectedOffset += chunk.size;
    }
    expect(expectedOffset).toBe(FILE_SIZE);
  });
});
