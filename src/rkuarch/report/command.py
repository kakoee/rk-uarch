"""B-owned report command; A4 registration is supplied as an unapplied adapter."""

from pathlib import Path
from typing import Annotated

import typer

from .complete import write_report
from .prose import safe_prose


def report_command(
    table: Annotated[
        Path, typer.Argument(help="Saved table; companions default to adjacent artifacts/.")
    ],
    output: Annotated[
        Path | None, typer.Option("--output", "--html", help="New HTML path.")
    ] = None,
    markdown: Annotated[
        Path | None, typer.Option("--markdown", help="New Markdown twin path.")
    ] = None,
    artifacts: Annotated[
        Path | None, typer.Option("--artifacts", help="Explicit companion directory.")
    ] = None,
    show_unvalidated_predictions: Annotated[
        bool, typer.Option("--show-unvalidated-predictions")
    ] = False,
    allow_synthetic_presentation: Annotated[
        bool, typer.Option("--allow-synthetic-presentation")
    ] = False,
) -> None:
    """Render saved captures offline; never invoke the producer or adopt oracle artifacts."""
    try:
        write_report(
            table,
            html_path=output,
            markdown_path=markdown,
            artifact_dir=artifacts,
            show_unvalidated_predictions=show_unvalidated_predictions,
            allow_synthetic_presentation=allow_synthetic_presentation,
        )
    except (ValueError, OSError) as exc:
        typer.echo(type(exc).__name__ + ": " + safe_prose(str(exc)), err=True)
        raise typer.Exit(2) from None
    typer.echo("HTML and Markdown report written.")
