# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import typer

from app.cli.transcribe import transcribe

app = typer.Typer(name="zabt")


@app.callback()
def main() -> None:
    """Zabt CLI tools."""


app.command()(transcribe)

if __name__ == "__main__":
    app()
