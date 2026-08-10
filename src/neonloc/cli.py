import os
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

from neonloc.core import analyze_directory

console = Console()

BANNER = """[bold cyan]
 _   _  _____  ____  _   _  _      _____  _____ 
| \\ | ||  ___|/ __ \\| \\ | || |    |  _  |/  __ \\
|  \\| || |__ | |  | |  \\| || |    | | | || /  \\/
| . ` ||  __|| |  | | . ` || |    | | | || |    
| |\\  || |___| |__| | |\\  || |____\\ \\_/ /| \\__/\\
\\_| \\_/\\____/ \\____/\\_| \\_/\\_____/ \\___/  \\____/
[/bold cyan]
[bold magenta]The abyssal line of code counter.[/bold magenta]
"""

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument('directory', default='.', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "-L",
    "--list-loc",
    type=click.Choice(["auto", "files", "dirs", "both"], case_sensitive=False),
    default=None,
    help="Also list LOC by files, dirs, or both. Auto detects flat, modular, or mixed layout."
)
def main(directory, list_loc):
    """Scan and analyze source code lines with pure edge."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    console.print(Align.center(BANNER))
    console.print()
    
    target_dir = Path(directory).resolve()
    
    with Progress(
        SpinnerColumn(spinner_name="dots2", style="bold cyan"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"[bold magenta]Scanning the void...[/bold magenta] ({target_dir})", total=None)
        
        analyzed = analyze_directory(str(target_dir), include_paths=bool(list_loc))
        if list_loc:
            results, path_metrics = analyzed
        else:
            results = analyzed
            path_metrics = None
        
    if not results:
        console.print(Panel(
            Text("No recognized source files found in the abyss.", justify="center", style="bold red"),
            border_style="red",
            title="[bold yellow]Scan Complete[/bold yellow]"
        ))
        sys.exit(0)

    if path_metrics:
        for table in build_path_tables(path_metrics, list_loc.lower()):
            console.print(table)
            console.print()
    else:
        for table in build_category_tables(results):
            console.print(table)
            console.print()

    total_files = sum(stats['files'] for stats in results.values())
    total_code = sum(stats['code'] for stats in results.values())
    
    summary_text = (
        f"Analyzed [bold cyan]{total_files}[/bold cyan] files across "
        f"[bold magenta]{len(results)}[/bold magenta] languages/formats.\n"
        f"Found [bold spring_green2]{total_code:,}[/bold spring_green2] lines of meaningful content."
    )
    
    console.print(Panel(
        summary_text,
        border_style="cyan",
        title="[bold yellow]Scan Summary[/bold yellow]",
        title_align="left"
    ))

def build_category_tables(results):
    categories = {}
    for lang, stats in results.items():
        cat = stats["type"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((lang, stats))

    tables = []
    for cat in sorted(categories.keys()):
        sorted_langs = sorted(categories[cat], key=lambda item: item[1]['total'], reverse=True)

        table = Table(
            title=f"[bold spring_green2]{cat.upper()} METRICS[/bold spring_green2]",
            show_header=True,
            header_style="bold cyan",
            border_style="magenta",
            expand=True
        )
        table.add_column("Language", style="bold bright_white")
        table.add_column("Files", justify="right", style="cyan")
        table.add_column("Lines", justify="right", style="spring_green2")
        table.add_column("Comments", justify="right", style="grey74")
        table.add_column("Blanks", justify="right", style="grey50")
        table.add_column("Total", justify="right", style="bold deep_pink4")

        c_files = c_code = c_comments = c_blanks = c_total = 0
        for lang, stats in sorted_langs:
            table.add_row(
                lang,
                f"{stats['files']:,}",
                f"{stats['code']:,}",
                f"{stats['comments']:,}",
                f"{stats['blanks']:,}",
                f"{stats['total']:,}"
            )
            c_files += stats['files']
            c_code += stats['code']
            c_comments += stats['comments']
            c_blanks += stats['blanks']
            c_total += stats['total']

        table.add_section()
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            f"[bold cyan]{c_files:,}[/bold cyan]",
            f"[bold spring_green2]{c_code:,}[/bold spring_green2]",
            f"[bold grey74]{c_comments:,}[/bold grey74]",
            f"[bold grey50]{c_blanks:,}[/bold grey50]",
            f"[bold deep_pink4]{c_total:,}[/bold deep_pink4]"
        )
        tables.append(table)

    return tables

def build_path_tables(path_metrics, mode):
    tables = []
    selected = resolve_path_mode(path_metrics, mode)
    
    if selected in ("dirs", "both"):
        dir_rows = [row for row in path_metrics["dirs"] if row["path"] != "."]
        if not dir_rows:
            dir_rows = path_metrics["dirs"]
        tables.append(build_path_table("DIRECTORY LOC METRICS", "Directory", dir_rows))
    
    if selected in ("files", "both"):
        tables.append(build_path_table("FILE LOC METRICS", "File", path_metrics["files"], include_language=True))
    
    return tables

def resolve_path_mode(path_metrics, mode):
    if mode != "auto":
        return mode
    
    has_root_files = any(row["path"] == "." for row in path_metrics["dirs"])
    has_nested_files = any(row["path"] != "." for row in path_metrics["dirs"])
    
    if has_root_files and has_nested_files:
        return "both"
    if has_nested_files:
        return "dirs"
    return "files"

def build_path_table(title, path_column, rows, include_language=False):
    table = Table(
        title=f"[bold spring_green2]{title}[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column(path_column, style="bold bright_white")
    if include_language:
        table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right", style="cyan")
    table.add_column("Lines", justify="right", style="spring_green2")
    table.add_column("Comments", justify="right", style="grey74")
    table.add_column("Blanks", justify="right", style="grey50")
    table.add_column("Total", justify="right", style="bold deep_pink4")
    
    totals = {"files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
    for row in rows:
        values = [
            row["path"],
        ]
        if include_language:
            values.append(row["language"])
        values.extend([
            f"{row['files']:,}",
            f"{row['code']:,}",
            f"{row['comments']:,}",
            f"{row['blanks']:,}",
            f"{row['total']:,}"
        ])
        table.add_row(*values)
        for key in totals:
            totals[key] += row[key]
    
    table.add_section()
    total_values = ["[bold white]TOTAL[/bold white]"]
    if include_language:
        total_values.append("[bold cyan]-[/bold cyan]")
    total_values.extend([
        f"[bold cyan]{totals['files']:,}[/bold cyan]",
        f"[bold spring_green2]{totals['code']:,}[/bold spring_green2]",
        f"[bold grey74]{totals['comments']:,}[/bold grey74]",
        f"[bold grey50]{totals['blanks']:,}[/bold grey50]",
        f"[bold deep_pink4]{totals['total']:,}[/bold deep_pink4]"
    ])
    table.add_row(*total_values)
    
    return table

if __name__ == "__main__":
    main()
