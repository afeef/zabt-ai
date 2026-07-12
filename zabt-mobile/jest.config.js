// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
/**
 * Minimal jest config for pure-TS unit tests (chunker, queue, multipart state machine).
 * Avoids jest-expo because its winter runtime pulls in React Native's module system,
 * which breaks in a Node environment even though our pure tests never touch it.
 *
 * If we need React Native tests later (components, hooks touching native modules),
 * set up a separate config + `jest --config` flag.
 */
module.exports = {
  testEnvironment: "node",
  transform: {
    "^.+\\.(ts|tsx|js|jsx)$": [
      "babel-jest",
      {
        presets: [["babel-preset-expo", { jsxImportSource: "nativewind" }]],
      },
    ],
  },
  testMatch: ["**/__tests__/**/*.test.ts"],
  moduleFileExtensions: ["ts", "tsx", "js", "json"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  transformIgnorePatterns: ["/node_modules/"],
};
