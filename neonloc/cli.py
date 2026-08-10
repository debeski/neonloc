import os
import sys
import json
import click
from io import StringIO
from datetime import datetime
from pathlib import Path
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

from neonloc import __version__
from neonloc.core import analyze_directory, detect_duplicates, compute_health
from neonloc.git_info import get_git_summary, get_loc_trend, parse_since
from neonloc.config import load_config
from neonloc.html_report import render_html_report

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

LIST_LOC_MODES = {"auto", "files", "dirs", "both"}

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="neonloc")
@click.argument('directory', default='.', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "-L",
    "--list-loc",
    type=str,
    is_flag=False,
    flag_value="auto",
    default=None,
    help="Also list LOC by files, dirs, or both (default: auto-detects flat, modular, or mixed layout)."
)
@click.option(
    "--depth",
    type=int,
    default=None,
    help="Limit directory nesting depth in dirs mode, e.g. --list-loc dirs --depth 2."
)
@click.option(
    "--top",
    "top_n",
    type=int,
    default=None,
    help="Limit the file listing (files mode) and LARGEST FILES table to the top N entries."
)
@click.option(
    "--top-languages",
    "top_languages",
    type=int,
    default=None,
    help="Limit category tables to the top N languages by total lines."
)
@click.option(
    "--top-dirs",
    "top_dirs",
    type=int,
    default=None,
    help="Limit the dirs-mode listing to the top N directories by total lines."
)
@click.option(
    "--sort",
    "sort_by",
    type=click.Choice(["loc", "name", "code", "comments", "ratio"], case_sensitive=False),
    default=None,
    help="Sort the file listing in files mode (default: loc, descending)."
)
@click.option(
    "-D",
    "--dist",
    is_flag=True,
    help="Show file-size distribution and the largest files."
)
@click.option(
    "-X",
    "--dup",
    is_flag=True,
    help="Detect duplicated code blocks across files (normalized line-hash matching)."
)
@click.option(
    "--git",
    "show_git",
    is_flag=True,
    help="Show Git branch, HEAD commit, author, and uncommitted change stats."
)
@click.option(
    "--since",
    "since",
    default=None,
    help="Show a daily LOC trend from Git history, e.g. --since 30d (also accepts w/m/y)."
)
@click.option(
    "-e",
    "--export",
    is_flag=True,
    help="Write the scan result to the target directory's .neonloc folder."
)
@click.option(
    "--html",
    "html_path",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write a standalone HTML report to the given path, e.g. --html report.html."
)
@click.option(
    "--no-banner",
    is_flag=True,
    help="Skip printing the banner. Useful when running neonloc from scripts."
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output. Color is also auto-disabled when stdout isn't a terminal."
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Print only the total LOC count, nothing else. No banner, spinner, or tables. Combine with -e to also export. Example: LOC=$(neonloc . --quiet)"
)
def main(directory, list_loc, depth, top_n, top_languages, top_dirs, sort_by, dist, dup, show_git, since, export, html_path, no_banner, no_color, quiet):
    """Scan and analyze source code lines with pure edge."""
    global console

    if list_loc and list_loc.lower() not in LIST_LOC_MODES:
        # Click's optional-value option swallowed the directory token (e.g. `-L .`).
        if directory == '.':
            directory = list_loc
        list_loc = "auto"
        if not Path(directory).is_dir():
            raise click.BadParameter(f"Directory '{directory}' does not exist.", param_hint="'DIRECTORY'")

    since_days = None
    if since:
        try:
            since_days = parse_since(since)
        except ValueError as exc:
            raise click.BadParameter(str(exc), param_hint="'--since'")

    target_dir = Path(directory).resolve()
    config = load_config(target_dir)

    effective_no_color = no_color or not config["output"]["color"]
    effective_no_banner = no_banner or not config["output"]["banner"] or quiet
    if effective_no_color:
        console = Console(no_color=True)

    if not effective_no_banner:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(Align.center(BANNER))
        console.print()

    scan_kwargs = dict(
        include_paths=True,
        include_duplicates=dup,
        respect_gitignore=config["scan"]["respect_gitignore"],
        include_hidden=config["scan"]["include_hidden"],
        include_generated=config["scan"]["include_generated"],
    )

    if quiet:
        results, path_metrics = analyze_directory(str(target_dir), **scan_kwargs)
    else:
        with Progress(
            SpinnerColumn(spinner_name="dots2", style="bold cyan"),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"[bold magenta]Scanning the void...[/bold magenta] ({target_dir})", total=None)

            results, path_metrics = analyze_directory(str(target_dir), **scan_kwargs)

    if not results:
        if quiet:
            click.echo(0)
        else:
            console.print(Panel(
                Text("No recognized source files found in the abyss.", justify="center", style="bold red"),
                border_style="red",
                title="[bold yellow]Scan Complete[/bold yellow]"
            ))
        sys.exit(0)

    dup_result = None
    if dup and path_metrics.get("code_lines"):
        dup_result = detect_duplicates(path_metrics["code_lines"])

    git_summary = get_git_summary(target_dir) if show_git else None

    loc_trend = None
    if since_days is not None:
        grand_total = sum(stats["total"] for stats in results.values())
        loc_trend = get_loc_trend(target_dir, since_days, grand_total)

    health = compute_health(
        results, path_metrics,
        huge_file_loc=config["thresholds"]["large_file"],
        very_huge_file_loc=config["thresholds"]["huge_file"]
    )

    report_items = build_report_items(
        results, path_metrics, list_loc, health, dist, dup_result, git_summary, loc_trend,
        depth=depth, top_n=top_n, top_languages=top_languages, top_dirs=top_dirs, sort_by=sort_by
    )

    if quiet:
        total_lines = sum(stats["total"] for stats in results.values())
        click.echo(total_lines)
    else:
        print_report(console, report_items)

    if export:
        export_paths = write_export(target_dir, results, path_metrics, list_loc, report_items, dup_result, git_summary, loc_trend)
        if not quiet:
            console.print(f"[bold cyan]Exported JSON:[/bold cyan] {export_paths['json']}")
            console.print(f"[bold cyan]Exported report:[/bold cyan] {export_paths['txt']}")
            console.print("[dim]Open the .txt report in an IDE or a monospace-font viewer for the tables to render correctly.[/dim]")

    if html_path:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = render_html_report(
            target_dir, generated_at, results, path_metrics, health,
            dup_result=dup_result, git_summary=git_summary, loc_trend=loc_trend
        )
        html_file = Path(html_path)
        html_file.write_text(html_content, encoding="utf-8")
        if not quiet:
            console.print(f"[bold cyan]Exported HTML report:[/bold cyan] {html_file.resolve()}")

def ratio_str(stats):
    total = stats["total"] or 1
    code_pct = stats["code"] / total * 100
    comm_pct = stats["comments"] / total * 100
    blank_pct = stats["blanks"] / total * 100
    return f"{code_pct:.1f}% / {comm_pct:.1f}% / {blank_pct:.1f}%"

SIZE_BUCKETS = [(0, 50), (51, 100), (101, 250), (251, 500), (501, 1000), (1001, None)]
SIZE_BUCKET_LABELS = ["0-50 LOC", "51-100 LOC", "101-250 LOC", "251-500 LOC", "501-1000 LOC", "1000+ LOC"]

MINIMAL_BUCKETS = [(0, 0), (1, 5), (6, 10)]
MINIMAL_BUCKET_LABELS = ["0 LOC", "1-5 LOC", "6-10 LOC"]

def build_report_items(results, path_metrics, list_loc, health, dist=False, dup_result=None, git_summary=None, loc_trend=None,
                        depth=None, top_n=None, top_languages=None, top_dirs=None, sort_by=None):
    if list_loc and path_metrics:
        tables = build_path_tables(path_metrics, list_loc.lower(), depth=depth, top_n=top_n, top_dirs=top_dirs, sort_by=sort_by)
    else:
        tables = build_category_tables(results, top_languages=top_languages)

    dist_items = []
    if dist and path_metrics and path_metrics["files"]:
        dist_items = [
            build_distribution_table(path_metrics["files"]),
            build_minimal_files_table(path_metrics["files"]),
            build_largest_files_table(path_metrics["files"], top_n=top_n or 10)
        ]

    dup_items = []
    if dup_result is not None:
        dup_items = [build_duplication_table(dup_result)]

    git_items = []
    if git_summary is not None:
        git_items.append(build_git_panel(git_summary))
    if loc_trend is not None:
        git_items.append(build_trend_table(loc_trend))

    error_items = []
    errors = path_metrics.get("errors") if path_metrics else None
    if errors:
        error_items = [build_errors_table(errors)]

    health_panel = build_health_panel(health)
    summary = build_summary_panel(results, path_metrics, dup_result)
    return [*tables, *dist_items, *dup_items, *git_items, *error_items, health_panel, summary]

def build_errors_table(errors):
    table = Table(
        title="[bold red]FILE READ ERRORS[/bold red]",
        show_header=True,
        header_style="bold cyan",
        border_style="red",
        expand=True
    )
    table.add_column("File", style="bold bright_white")
    table.add_column("Error", style="red")
    for err in errors:
        table.add_row(err["path"], err["error"])

    return table

def build_health_panel(health):
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left", style="bold bright_white")
    table.add_column(justify="right")

    table.add_row("Code Ratio", f"[bold spring_green2]{health['code_ratio']:.1f}%[/bold spring_green2]")
    table.add_row("Average File Size", f"[cyan]{health['avg_size']:.0f}[/cyan] LOC")
    if health["largest_file"]:
        largest_file = health["largest_file"]
        table.add_row("Largest File", f"[bold cyan]{largest_file['path']}[/bold cyan]  {largest_file['total']:,} LOC")
    table.add_row("Empty Files", f"[yellow]{health['empty_files']:,}[/yellow]")
    table.add_row(f"Huge Files (>{health['huge_file_loc']} LOC)", f"[yellow]{health['huge_files']:,}[/yellow]")

    severity_style = {"warning": "yellow", "error": "bold red"}
    pieces = [table]
    if health["warnings"]:
        pieces.append(Text(""))
        for w in health["warnings"]:
            style = severity_style.get(w["severity"], "yellow")
            pieces.append(Text.from_markup(f"[{style}]⚠ {w['text']}[/{style}]"))

    return Panel(
        Group(*pieces),
        border_style="cyan",
        title="[bold yellow]Project Health[/bold yellow]",
        title_align="left"
    )

def build_git_panel(git_summary):
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left", style="bold bright_white")
    table.add_column(justify="right")

    table.add_row("Branch", f"[bold cyan]{git_summary['branch']}[/bold cyan]")
    table.add_row("Commit", f"[bold magenta]{git_summary['commit']}[/bold magenta]")
    table.add_row("Author", git_summary["author"])
    table.add_row("Changed", f"[cyan]{git_summary['changed_files']:,}[/cyan] files")
    table.add_row("Added", f"[bold spring_green2]+{git_summary['added']:,}[/bold spring_green2] LOC")
    table.add_row("Removed", f"[bold red]-{git_summary['removed']:,}[/bold red] LOC")

    return Panel(
        table,
        border_style="cyan",
        title="[bold yellow]Git[/bold yellow]",
        title_align="left"
    )

def build_trend_table(loc_trend):
    table = Table(
        title="[bold spring_green2]LOC TREND[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column("Date", style="bold bright_white")
    table.add_column("Total LOC", justify="right", style="bold deep_pink4")
    for day, total in loc_trend:
        table.add_row(day, f"{total:,}")

    return table

def build_duplication_table(dup_result):
    table = Table(
        title="[bold spring_green2]DUPLICATION[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column("Block A", style="bold bright_white")
    table.add_column("Block B", style="bold bright_white")
    table.add_column("Lines", justify="right", style="bold deep_pink4")

    if not dup_result["matches"]:
        table.add_row("[dim]No duplicated blocks found.[/dim]", "", "")
    else:
        for match in dup_result["matches"][:20]:
            a, b = match["a"], match["b"]
            table.add_row(
                f"{a['path']}:{a['start_line']}-{a['end_line']}",
                f"{b['path']}:{b['start_line']}-{b['end_line']}",
                f"{match['lines']:,}"
            )

    table.add_section()
    table.add_row(
        "[bold white]Duplication ratio[/bold white]",
        "",
        f"[bold yellow]{dup_result['ratio']:.1f}%[/bold yellow]"
    )

    return table

def bucket_file_sizes(file_rows):
    counts = [0] * len(SIZE_BUCKETS)
    for row in file_rows:
        total = row["total"]
        for i, (lo, hi) in enumerate(SIZE_BUCKETS):
            if hi is None or total <= hi:
                if total >= lo:
                    counts[i] += 1
                    break
    return counts

def bucket_minimal_files(file_rows):
    buckets = [[] for _ in MINIMAL_BUCKETS]
    for row in file_rows:
        total = row["total"]
        for i, (lo, hi) in enumerate(MINIMAL_BUCKETS):
            if lo <= total <= hi:
                buckets[i].append(row["path"])
                break
    return buckets

def build_minimal_files_table(file_rows):
    buckets = bucket_minimal_files(file_rows)

    table = Table(
        title="[bold spring_green2]EMPTY / MINIMAL FILES[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column("Range", style="bold bright_white")
    table.add_column("Files", justify="right", style="cyan")
    table.add_column("Examples", style="dim")
    for label, paths in zip(MINIMAL_BUCKET_LABELS, buckets):
        examples = ", ".join(paths[:3]) + (f", +{len(paths) - 3} more" if len(paths) > 3 else "")
        table.add_row(label, f"{len(paths):,}", examples)

    return table

def build_distribution_table(file_rows):
    counts = bucket_file_sizes(file_rows)

    table = Table(
        title="[bold spring_green2]FILE SIZE DISTRIBUTION[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column("Range", style="bold bright_white")
    table.add_column("Files", justify="right", style="cyan")
    for label, count in zip(SIZE_BUCKET_LABELS, counts):
        table.add_row(label, f"{count:,}")

    return table

def build_largest_files_table(file_rows, top_n=10):
    top = sorted(file_rows, key=lambda row: row["total"], reverse=True)[:top_n]

    table = Table(
        title="[bold spring_green2]LARGEST FILES[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="bold bright_white")
    table.add_column("Total", justify="right", style="bold deep_pink4")
    for i, row in enumerate(top, start=1):
        table.add_row(str(i), row["path"], f"{row['total']:,}")

    return table

def build_summary_panel(results, path_metrics, dup_result=None):
    totals = {"files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
    for stats in results.values():
        for key in totals:
            totals[key] += stats[key]
    grand_total = totals["total"] or 1

    largest_lang = max(results.items(), key=lambda item: item[1]["total"], default=None)
    largest_dir = None
    if path_metrics:
        dir_rows = [row for row in path_metrics["dirs"] if row["path"] != "."]
        if not dir_rows:
            dir_rows = path_metrics["dirs"]
        if dir_rows:
            largest_dir = max(dir_rows, key=lambda row: row["total"])

    comment_ratio = totals["comments"] / grand_total * 100
    blank_ratio = totals["blanks"] / grand_total * 100

    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left", style="bold bright_white")
    table.add_column(justify="right")

    table.add_row("Files", f"[bold cyan]{totals['files']:,}[/bold cyan]")
    table.add_row("Code", f"[bold spring_green2]{totals['code']:,}[/bold spring_green2] LOC")
    table.add_row("Comments", f"[grey74]{totals['comments']:,}[/grey74]")
    table.add_row("Blank", f"[grey50]{totals['blanks']:,}[/grey50]")
    table.add_row("Total", f"[bold deep_pink4]{totals['total']:,}[/bold deep_pink4]")
    table.add_row("", "")
    table.add_row("Languages", f"[bold magenta]{len(results)}[/bold magenta]")
    if largest_lang:
        lang_name, lang_stats = largest_lang
        lang_pct = lang_stats["total"] / grand_total * 100
        table.add_row("Largest language", f"[bold cyan]{lang_name}[/bold cyan] ({lang_pct:.1f}%)")
    if largest_dir:
        dir_pct = largest_dir["total"] / grand_total * 100
        dir_label = largest_dir["path"] if largest_dir["path"] != "." else "./"
        table.add_row("Largest directory", f"[bold cyan]{dir_label}[/bold cyan] ({dir_pct:.1f}%)")
    table.add_row("Comment ratio", f"[bold yellow]{comment_ratio:.1f}%[/bold yellow]")
    table.add_row("Blank ratio", f"[bold yellow]{blank_ratio:.1f}%[/bold yellow]")
    if dup_result is not None:
        table.add_row("Duplication ratio", f"[bold yellow]{dup_result['ratio']:.1f}%[/bold yellow]")

    return Panel(
        table,
        border_style="cyan",
        title="[bold yellow]Project Summary[/bold yellow]",
        title_align="left"
    )

def print_report(target_console, report_items):
    for item in report_items:
        target_console.print(item)
        target_console.print()

def build_category_tables(results, top_languages=None):
    allowed = None
    if top_languages:
        allowed = {
            lang for lang, _ in sorted(results.items(), key=lambda item: item[1]["total"], reverse=True)[:top_languages]
        }

    categories = {}
    for lang, stats in results.items():
        if allowed is not None and lang not in allowed:
            continue
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
        table.add_column("Code / Comm / Blank", justify="right", style="dim")

        c_files = c_code = c_comments = c_blanks = c_total = 0
        for lang, stats in sorted_langs:
            table.add_row(
                lang,
                f"{stats['files']:,}",
                f"{stats['code']:,}",
                f"{stats['comments']:,}",
                f"{stats['blanks']:,}",
                f"{stats['total']:,}",
                ratio_str(stats)
            )
            c_files += stats['files']
            c_code += stats['code']
            c_comments += stats['comments']
            c_blanks += stats['blanks']
            c_total += stats['total']

        c_totals = {"code": c_code, "comments": c_comments, "blanks": c_blanks, "total": c_total}
        table.add_section()
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            f"[bold cyan]{c_files:,}[/bold cyan]",
            f"[bold spring_green2]{c_code:,}[/bold spring_green2]",
            f"[bold grey74]{c_comments:,}[/bold grey74]",
            f"[bold grey50]{c_blanks:,}[/bold grey50]",
            f"[bold deep_pink4]{c_total:,}[/bold deep_pink4]",
            f"[dim]{ratio_str(c_totals)}[/dim]"
        )
        tables.append(table)

    return tables

def collapse_dirs_by_depth(dir_rows, depth):
    collapsed = {}
    for row in dir_rows:
        parts = row["path"].split("/")
        truncated = "/".join(parts[:depth]) if len(parts) > depth else row["path"]
        if truncated not in collapsed:
            collapsed[truncated] = {"path": truncated, "files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
        for key in ("files", "code", "comments", "blanks", "total"):
            collapsed[truncated][key] += row[key]
    return list(collapsed.values())

def sort_file_rows(file_rows, sort_by):
    sort_by = (sort_by or "loc").lower()
    if sort_by == "name":
        return sorted(file_rows, key=lambda row: row["path"])
    if sort_by == "code":
        return sorted(file_rows, key=lambda row: row["code"], reverse=True)
    if sort_by == "comments":
        return sorted(file_rows, key=lambda row: row["comments"], reverse=True)
    if sort_by == "ratio":
        return sorted(file_rows, key=lambda row: (row["comments"] / row["total"]) if row["total"] else 0, reverse=True)
    return sorted(file_rows, key=lambda row: row["total"], reverse=True)

def build_path_tables(path_metrics, mode, depth=None, top_n=None, top_dirs=None, sort_by=None):
    selected = resolve_path_mode(path_metrics, mode)

    if selected == "both":
        return [build_tree_table(path_metrics)]

    tables = []
    if selected == "dirs":
        dir_rows = [row for row in path_metrics["dirs"] if row["path"] != "."]
        if not dir_rows:
            dir_rows = path_metrics["dirs"]
        if depth:
            dir_rows = collapse_dirs_by_depth(dir_rows, depth)
        dir_rows = sorted(dir_rows, key=lambda row: row["total"], reverse=True)
        title = "DIRECTORY LOC METRICS"
        if top_dirs:
            dir_rows = dir_rows[:top_dirs]
            title = f"TOP {top_dirs} DIRECTORIES"
        tables.append(build_path_table(title, "Directory", dir_rows))

    if selected == "files":
        file_rows = sort_file_rows(path_metrics["files"], sort_by)
        title = "FILE LOC METRICS"
        if top_n:
            file_rows = file_rows[:top_n]
            title = f"TOP {top_n} LARGEST FILES"
        tables.append(build_path_table(title, "File", file_rows, include_language=True))

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
    table.add_column("Code / Comm / Blank", justify="right", style="dim")

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
            f"{row['total']:,}",
            ratio_str(row)
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
        f"[bold deep_pink4]{totals['total']:,}[/bold deep_pink4]",
        f"[dim]{ratio_str(totals)}[/dim]"
    ])
    table.add_row(*total_values)

    return table

def build_tree_table(path_metrics):
    dirs = path_metrics["dirs"]

    files_by_dir = {}
    for f in path_metrics["files"]:
        parent = str(Path(f["path"]).parent)
        parent = "." if parent == "." else parent
        files_by_dir.setdefault(parent, []).append(f)
    for rows in files_by_dir.values():
        rows.sort(key=lambda row: row["total"], reverse=True)

    def dir_sort_key(row):
        return () if row["path"] == "." else tuple(row["path"].split("/"))

    sorted_dirs = sorted(dirs, key=dir_sort_key)

    table = Table(
        title="[bold spring_green2]LOC METRICS[/bold spring_green2]",
        show_header=True,
        header_style="bold cyan",
        border_style="magenta",
        expand=True
    )
    table.add_column("Path", style="bold bright_white")
    table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right", style="cyan")
    table.add_column("Lines", justify="right", style="spring_green2")
    table.add_column("Comments", justify="right", style="grey74")
    table.add_column("Blanks", justify="right", style="grey50")
    table.add_column("Total", justify="right", style="bold deep_pink4")
    table.add_column("Code / Comm / Blank", justify="right", style="dim")

    totals = {"files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
    for d in sorted_dirs:
        depth = 0 if d["path"] == "." else d["path"].count("/") + 1
        indent = "  " * depth
        label = "." if d["path"] == "." else d["path"].split("/")[-1] + "/"
        table.add_row(
            f"{indent}[bold]{label}[/bold]",
            "[cyan]-[/cyan]",
            f"[bold cyan]{d['files']:,}[/bold cyan]",
            f"[bold spring_green2]{d['code']:,}[/bold spring_green2]",
            f"[bold grey74]{d['comments']:,}[/bold grey74]",
            f"[bold grey50]{d['blanks']:,}[/bold grey50]",
            f"[bold deep_pink4]{d['total']:,}[/bold deep_pink4]",
            f"[dim]{ratio_str(d)}[/dim]"
        )
        for key in totals:
            totals[key] += d[key]

        file_indent = "  " * (depth + 1)
        for f in files_by_dir.get(d["path"], []):
            fname = Path(f["path"]).name
            table.add_row(
                f"{file_indent}- {fname}",
                f["language"],
                f"{f['files']:,}",
                f"{f['code']:,}",
                f"{f['comments']:,}",
                f"{f['blanks']:,}",
                f"{f['total']:,}",
                ratio_str(f)
            )

    table.add_section()
    table.add_row(
        "[bold white]TOTAL[/bold white]",
        "[bold cyan]-[/bold cyan]",
        f"[bold cyan]{totals['files']:,}[/bold cyan]",
        f"[bold spring_green2]{totals['code']:,}[/bold spring_green2]",
        f"[bold grey74]{totals['comments']:,}[/bold grey74]",
        f"[bold grey50]{totals['blanks']:,}[/bold grey50]",
        f"[bold deep_pink4]{totals['total']:,}[/bold deep_pink4]",
        f"[dim]{ratio_str(totals)}[/dim]"
    )

    return table

def write_export(target_dir, results, path_metrics, list_loc, report_items, dup_result=None, git_summary=None, loc_trend=None):
    export_dir = target_dir / ".neonloc"
    export_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = export_dir / f"result_{timestamp}.json"
    txt_path = export_dir / f"result_{timestamp}.txt"
    total_code = sum(stats["code"] for stats in results.values())
    total_comments = sum(stats["comments"] for stats in results.values())
    total_blanks = sum(stats["blanks"] for stats in results.values())
    total_lines = sum(stats["total"] for stats in results.values()) or 1
    payload = {
        "generated_at": f"{datetime.utcnow().isoformat(timespec='seconds')}Z",
        "directory": str(target_dir),
        "summary": {
            "files": sum(stats["files"] for stats in results.values()),
            "languages": len(results),
            "code": total_code,
            "comments": total_comments,
            "blanks": total_blanks,
            "total": total_lines,
            "code_ratio": round(total_code / total_lines * 100, 1),
            "comment_ratio": round(total_comments / total_lines * 100, 1),
            "blank_ratio": round(total_blanks / total_lines * 100, 1),
        },
        "languages": results,
    }
    if path_metrics and path_metrics["files"]:
        payload["size_distribution"] = dict(zip(SIZE_BUCKET_LABELS, bucket_file_sizes(path_metrics["files"])))
        payload["largest_files"] = [
            {"path": row["path"], "total": row["total"]}
            for row in sorted(path_metrics["files"], key=lambda row: row["total"], reverse=True)[:10]
        ]
        payload["minimal_files"] = {
            label: paths for label, paths in zip(MINIMAL_BUCKET_LABELS, bucket_minimal_files(path_metrics["files"]))
        }
    if path_metrics and path_metrics.get("errors"):
        payload["errors"] = path_metrics["errors"]
    if dup_result is not None:
        payload["duplication"] = dup_result
    if git_summary is not None:
        payload["git"] = git_summary
    if loc_trend is not None:
        payload["loc_trend"] = [{"date": day, "total": total} for day, total in loc_trend]
    if list_loc and path_metrics:
        payload["paths"] = {
            "mode": list_loc.lower() if list_loc else None,
            "files": path_metrics["files"],
            "dirs": path_metrics["dirs"],
        }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    report_buffer = StringIO()
    report_console = Console(file=report_buffer, force_terminal=False, width=120)
    print_report(report_console, report_items)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(report_buffer.getvalue())

    return {"json": json_path, "txt": txt_path}

if __name__ == "__main__":
    main()
