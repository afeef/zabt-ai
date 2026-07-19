// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));

export interface Questions {
  brandTerms: string[];
  brandDomain: string;
  competitors: string[];
  questions: string[];
}

export function loadQuestions(): Questions {
  return JSON.parse(readFileSync(join(here, "questions.json"), "utf8")) as Questions;
}

export const resultsDir = join(here, "results");
