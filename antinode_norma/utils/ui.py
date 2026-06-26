"""CLI UI utilities for color-coded output and progress tracking."""

from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

console = Console()


def success_message(text: str) -> None:
    """Print a green success message."""
    console.print(f"[green]✓[/green] {text}")


def error_message(text: str) -> None:
    """Print a red error message."""
    console.print(f"[red]✗[/red] {text}")


def warning_message(text: str) -> None:
    """Print a yellow warning message."""
    console.print(f"[yellow]⚠[/yellow] {text}")


def info_message(text: str) -> None:
    """Print a cyan info message."""
    console.print(f"[cyan]ℹ[/cyan] {text}")


def section_header(text: str) -> None:
    """Print a section header with styling."""
    console.print(f"\n[bold cyan]{text}[/bold cyan]")
    console.print("[dim]" + "─" * len(text) + "[/dim]")


def code_block(text: str, language: str = "python") -> None:
    """Print a code block with syntax highlighting."""
    from rich.syntax import Syntax

    syntax = Syntax(text, language, theme="monokai", line_numbers=False)
    console.print(syntax)


def table_output(headers: list[str], rows: list[list[str]]) -> None:
    """Print a formatted table."""
    table = Table(title="Results", show_header=True, header_style="bold cyan")
    for header in headers:
        table.add_column(header, style="dim")
    for row in rows:
        table.add_row(*row)
    console.print(table)


def progress_bar(
    description: str = "Processing",
    total: Optional[int] = None,
) -> Progress:
    """Create and return a progress bar context manager."""
    progress = Progress(
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn() if total else SpinnerColumn(),
        console=console,
    )
    return progress


def prompt_user_choice(
    message: str,
    choices: list[str],
    default_index: int = 0,
) -> str:
    """Prompt the user to choose from a list of options."""
    console.print(f"\n[bold]{message}[/bold]")
    for i, choice in enumerate(choices):
        default_marker = " (default)" if i == default_index else ""
        console.print(f"  {i + 1}. {choice}{default_marker}")
    while True:
        try:
            response = click.prompt(
                "[cyan]Enter your choice[/cyan]",
                type=click.IntRange(1, len(choices)),
                default=default_index + 1,
            )
            return choices[response - 1]
        except click.exceptions.Abort:
            raise
        except Exception as e:
            error_message(f"Invalid choice: {e}")


def prompt_user_mapping(
    step_text: str,
    suggested_mappings: Optional[list[str]] = None,
) -> str:
    """Prompt the user to provide or choose a mapping for an unmapped step."""
    section_header(f"Unmapped Step: {step_text}")

    if suggested_mappings:
        console.print("\n[dim]Suggested mappings:[/dim]")
        for i, mapping in enumerate(suggested_mappings, 1):
            console.print(f"  {i}. {mapping}")
        choice = click.prompt(
            "[cyan]Choose a mapping (number) or enter a custom mapping[/cyan]",
            type=str,
        )
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suggested_mappings):
                return suggested_mappings[idx]
        except ValueError:
            pass
        return choice
    else:
        return click.prompt("[cyan]Enter a Playwright mapping[/cyan]", type=str)


def error_context(error: Exception, context: str = "") -> None:
    """Print detailed error information."""
    error_panel = Panel(
        f"[red]{str(error)}[/red]",
        title="[bold red]Error[/bold red]",
        border_style="red",
    )
    console.print(error_panel)
    if context:
        console.print(f"\n[dim]Context:[/dim] {context}")


def example_output(title: str, content: str) -> None:
    """Print example output in a panel."""
    example_panel = Panel(
        content,
        title=f"[bold green]Example: {title}[/bold green]",
        border_style="green",
    )
    console.print(example_panel)
