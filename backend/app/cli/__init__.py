import typer

from app.cli.transcribe import transcribe

app = typer.Typer(name="zabt")


@app.callback()
def main() -> None:
    """Zabt CLI tools."""


app.command()(transcribe)

if __name__ == "__main__":
    app()
