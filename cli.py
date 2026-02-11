"""
CLI interface for text-to-chart.

Usage:
    python -m cli chart --input path/to/file.csv [--output chart.png] [--type bar]
    python -m cli chart --text "Week\\tPoints\\n2025-20\\t40\\n2025-21\\t45" [--output chart.png]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root on path and load .env
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
import config  # noqa: F401  # loads .env

import click


@click.group()
def main():
    """Text-to-Chart: Convert text, CSV, or Excel into charts."""
    pass


@main.command()
@click.option("--input", "-i", "input_path", type=click.Path(exists=True), help="Path to input file (CSV, Excel, TXT)")
@click.option("--text", "-t", "text_input", type=str, help="Raw text input (tab/comma/space separated)")
@click.option("--output", "-o", "output_path", type=click.Path(), default=None, help="Output PNG path (default: show in browser)")
@click.option("--type", "-T", "chart_type", type=str, default="auto", help="Chart type: auto, line, bar, scatter, pie")
@click.option("--title", type=str, default=None, help="Chart title")
def chart(input_path, text_input, output_path, chart_type, title):
    """Generate a chart from text or file input."""
    from chart_service import create_chart

    if not input_path and not text_input:
        click.echo("Error: Provide either --input (file path) or --text (raw text).", err=True)
        sys.exit(1)

    try:
        if input_path:
            path = Path(input_path)
            raw_input = path.read_bytes()
            filename = path.name
        else:
            # Handle escaped newlines and tabs from command line
            raw_input = text_input.replace("\\n", "\n").replace("\\t", "\t")
            filename = None

        parsed, config, fig = create_chart(
            raw_input=raw_input,
            filename=filename,
            chart_type=chart_type,
            title=title,
        )

        click.echo(f"Parser: {parsed.source_type}")
        click.echo(f"Data shape: {parsed.shape}")
        click.echo(f"Chart type: {config.chart_type}")
        click.echo(f"X column: {config.x_column}")
        click.echo(f"Y columns: {config.y_columns}")

        if output_path:
            fig.write_image(output_path)
            click.echo(f"Chart saved to: {output_path}")
        else:
            fig.show()
            click.echo("Chart opened in browser.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
