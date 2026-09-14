from __future__ import annotations

from pathlib import Path

import typer

from .pipeline import build_wiki

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Build and explore graph-native repository wikis."""


@app.command()
def build(
    repository: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    output: Path = typer.Option(Path("wiki-output"), "--output", "-o"),
) -> None:
    """Generate a Markdown code wiki and a Semantica graph."""
    artifacts = build_wiki(repository, output)
    typer.echo(f"Wiki:  {artifacts['wiki'].resolve()}")
    typer.echo(f"Graph: {artifacts['graph'].resolve()}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Interface to bind."),
    port: int = typer.Option(8080, min=1, max=65535),
) -> None:
    """Start the FastAPI backend for the static frontend."""
    import uvicorn

    uvicorn.run("semantica_wiki.web:app", host=host, port=port)


if __name__ == "__main__":
    app()
