// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua

export interface Engine {
  name: string;
  ask(prompt: string): Promise<string>;
}

async function postJson(url: string, headers: Record<string, string>, body: unknown): Promise<any> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${url} -> ${res.status} ${await res.text()}`);
  return res.json();
}

function openAiCompatible(name: string, baseUrl: string, key: string, model: string): Engine {
  return {
    name,
    async ask(prompt) {
      const data = await postJson(
        `${baseUrl.replace(/\/$/, "")}/chat/completions`,
        { authorization: `Bearer ${key}` },
        { model, messages: [{ role: "user", content: prompt }] },
      );
      return data.choices?.[0]?.message?.content ?? "";
    },
  };
}

function anthropic(key: string, model: string): Engine {
  return {
    name: "anthropic",
    async ask(prompt) {
      const data = await postJson(
        "https://api.anthropic.com/v1/messages",
        { "x-api-key": key, "anthropic-version": "2023-06-01" },
        { model, max_tokens: 1024, messages: [{ role: "user", content: prompt }] },
      );
      return (data.content ?? []).map((b: any) => b.text ?? "").join("");
    },
  };
}

export function buildEngines(env: NodeJS.ProcessEnv): Engine[] {
  const engines: Engine[] = [];
  if (env.OPENAI_API_KEY) {
    engines.push(
      openAiCompatible(
        "openai",
        env.OPENAI_BASE_URL ?? "https://api.openai.com/v1",
        env.OPENAI_API_KEY,
        env.OPENAI_MODEL ?? "gpt-4o-mini",
      ),
    );
  }
  if (env.ANTHROPIC_API_KEY) {
    engines.push(anthropic(env.ANTHROPIC_API_KEY, env.ANTHROPIC_MODEL ?? "claude-sonnet-5"));
  }
  if (env.PERPLEXITY_API_KEY) {
    engines.push(
      openAiCompatible(
        "perplexity",
        "https://api.perplexity.ai",
        env.PERPLEXITY_API_KEY,
        env.PERPLEXITY_MODEL ?? "sonar",
      ),
    );
  }
  return engines;
}
