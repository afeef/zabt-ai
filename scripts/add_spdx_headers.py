#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Add SPDX license headers to tracked source files.

Idempotent: files that already contain an SPDX-License-Identifier are skipped.
Only operates on git-tracked files (so node_modules/.venv/.next are never touched).

Usage:
    uv run python scripts/add_spdx_headers.py           # apply
    uv run python scripts/add_spdx_headers.py --check    # report only, exit 1 if any missing
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SPDX = "SPDX-License-Identifier: AGPL-3.0-only"
COPYRIGHT = "Copyright (C) 2025-2026 Afeef Janjua"

# extension -> line-comment prefix
HASH = "#"
SLASH = "//"
COMMENT = {
    ".py": HASH,
    ".ts": SLASH,
    ".tsx": SLASH,
    ".js": SLASH,
    ".jsx": SLASH,
    ".mjs": SLASH,
    ".cjs": SLASH,
}

# Skip generated / declaration files even if tracked.
SKIP_SUFFIXES = (".d.ts",)
SKIP_NAMES = {"next-env.d.ts"}


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [Path(p) for p in out]


def header_for(prefix: str) -> str:
    return f"{prefix} {SPDX}\n{prefix} {COPYRIGHT}\n"


def needs_header(path: Path) -> bool:
    if path.suffix not in COMMENT:
        return False
    if path.name in SKIP_NAMES or path.name.endswith(SKIP_SUFFIXES):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return False
    return SPDX not in text


def insert_header(path: Path) -> None:
    prefix = COMMENT[path.suffix]
    text = path.read_text(encoding="utf-8")
    header = header_for(prefix)
    lines = text.splitlines(keepends=True)

    # Determine insertion index: after a shebang and/or a leading JS "use client"/
    # "use server" directive (which must precede statements; comments before it are OK).
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx = 1
    # For .py, also skip a coding declaration on line 1/2.
    if path.suffix == ".py" and idx < len(lines) and "coding:" in lines[idx]:
        idx += 1

    new_lines = lines[:idx] + [header] + lines[idx:]
    path.write_text("".join(new_lines), encoding="utf-8")


def main() -> int:
    check = "--check" in sys.argv
    missing: list[Path] = []
    changed = 0
    for path in tracked_files():
        if needs_header(path):
            missing.append(path)
            if not check:
                insert_header(path)
                changed += 1
    if check:
        if missing:
            print(f"Missing SPDX headers in {len(missing)} file(s):")
            for p in missing[:50]:
                print(f"  {p}")
            return 1
        print("All source files have SPDX headers.")
        return 0
    print(f"Added SPDX headers to {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
