// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { resultsDir } from "./config";

interface Record {
  engine: string;
  mentioned: boolean;
  cited: boolean;
  competitorsMentioned: string[];
}

function latestFile(): string {
  const files = readdirSync(resultsDir).filter((f) => f.endsWith(".jsonl")).sort();
  if (files.length === 0) throw new Error("No result files. Run `npm run geo:monitor` first.");
  return join(resultsDir, files[files.length - 1]);
}

const file = process.argv[2] ?? latestFile();
const rows: Record[] = readFileSync(file, "utf8")
  .split("\n")
  .filter(Boolean)
  .map((l) => JSON.parse(l));

const total = rows.length;
const mentions = rows.filter((r) => r.mentioned).length;
const citations = rows.filter((r) => r.cited).length;
const sov: Map<string, number> = new Map();
for (const r of rows) for (const c of r.competitorsMentioned) sov.set(c, (sov.get(c) ?? 0) + 1);

console.log(`File: ${file}`);
console.log(`Responses: ${total}`);
console.log(`Zabt mention rate:  ${((mentions / total) * 100).toFixed(1)}% (${mentions}/${total})`);
console.log(`Zabt citation rate: ${((citations / total) * 100).toFixed(1)}% (${citations}/${total})`);
console.log("Competitor share-of-voice:");
for (const [c, n] of [...sov.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${c}: ${n}`);
}
