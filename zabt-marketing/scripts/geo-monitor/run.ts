// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { appendFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { loadQuestions, resultsDir } from "./config";
import { buildEngines } from "./engines";
import { detect } from "./detect";

async function main() {
  const q = loadQuestions();
  const engines = buildEngines(process.env);
  if (engines.length === 0) {
    console.error("No engines configured. Copy .env.example to .env and set at least one key, then run with: node --env-file=.env, or export the vars.");
    process.exit(1);
  }
  mkdirSync(resultsDir, { recursive: true });
  const runAt = new Date().toISOString();
  const outFile = join(resultsDir, `${runAt.slice(0, 10)}.jsonl`);

  for (const engine of engines) {
    for (const question of q.questions) {
      let text = "";
      let error: string | null = null;
      try {
        text = await engine.ask(question);
      } catch (e) {
        error = e instanceof Error ? e.message : String(e);
      }
      const d = detect({
        text,
        brandTerms: q.brandTerms,
        brandDomain: q.brandDomain,
        competitors: q.competitors,
      });
      const record = { runAt, engine: engine.name, question, ...d, error };
      appendFileSync(outFile, JSON.stringify(record) + "\n");
      console.log(`[${engine.name}] mentioned=${d.mentioned} cited=${d.cited} :: ${question}`);
    }
  }
  console.log(`\nWrote results to ${outFile}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
