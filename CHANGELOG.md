## v0.6.3
- **Generated/Vendor File Exclusion**: Added `GENERATED_FILE_PATTERN` in `core.py` (matches `*.min.js`/`*.min.css`, `*.bundle.js`/`*.bundle.css`, `*.map`, `*.d.ts`, and lockfiles like `package-lock.json`/`yarn.lock`/`Cargo.lock`) checked in `analyze_directory`'s walk, gated by the existing `include_generated` config/flag — fixes vendored/minified files (e.g. bundled `bootstrap.min.js`) skewing largest-file rankings when they weren't nested under an `IGNORE_DIRS` name.
- **Per-File Table Cleanup**: `build_path_table` in `cli.py` gained `include_files_count`, now `False` for the files-mode listing — the `Files` column always read `1` per row there and carried no information.
- **Language Rollup for File Listings**: Added `build_language_rollup_table` in `cli.py`, printed as a `FILES BY LANGUAGE` table ahead of the per-file listing in `-L files`/`auto` mode, aggregating files/code/comments/blanks/total per language.
- **Full Filenames in Narrow Terminals**: The `File`/`Directory` path column in `build_path_table` now uses `overflow="fold"` with a `ratio=3` width hint instead of Rich's default ellipsis truncation, so long paths wrap across lines instead of being cut to an unidentifiable `…` fragment.

## v0.6.2
- **Wide-Terminal Panel Alignment**: `build_health_panel`/`build_git_panel`/`build_summary_panel` in `cli.py` now build their `Table.grid` with `expand=True`, so the right-aligned value column stretches to the panel's full width instead of staying content-sized while only the panel border grew on wide terminals.

## v0.6.1
- **Longest Function/Constant in Summary**: `core.py` gained heuristic `FUNCTION_PATTERNS`/`CONSTANT_PATTERNS` (Python, JS/TS, Go, Java, C#, C/C++, Rust, Swift, Kotlin, PHP) and an opt-in `collect_features` pass in `count_file`/`analyze_directory` (indent-based tracking for Python, brace-depth tracking for the rest) that finds the longest function by LOC span and the longest constant declaration by value length. Surfaced as `Longest function`/`Longest constant` rows in the `Project Summary` panel (`cli.py`), the HTML report's `Project Health` section (`html_report.py`), and `summary.longest_function`/`summary.longest_constant` in `-e`/`--export` JSON.

## v0.6.0
- **`.neonloc.toml` Config File**: Added `neonloc/config.py` — drop a `.neonloc.toml` (`[scan]` respect_gitignore/include_hidden/include_generated, `[output]` color/banner, `[thresholds]` large_file/huge_file) in the scanned directory and `neonloc .` picks it up automatically; CLI flags still override. Uses stdlib `tomllib` on Python 3.11+, falls back to the new `tomli` dependency below that. `analyze_directory` in `core.py` gained `respect_gitignore`/`include_hidden`/`include_generated` params to back the scan settings.
- **HTML Export**: Added `--html <path>`, rendering a standalone, self-contained dark-themed HTML report (`neonloc/html_report.py`) with summary cards, language breakdown, directories, largest files, Project Health (with warnings), duplication, Git info, and an inline SVG LOC-trend chart when `--since` is used — no server or external assets required.
- **Project Health Panel & Error Reporting**: `count_file`/`analyze_directory` in `core.py` no longer discard file read exceptions via bare `except: pass` — errors are collected into `path_metrics["errors"]` and the file is skipped from counts instead of silently corrupting them. `cli.py` renders a `FILE READ ERRORS` table when any occur, plus an always-on `Project Health` panel (code ratio, average file size, largest file, empty/huge-file counts, and warning lines for files >500/>1,000 LOC, low-code files, and unreadable files). `-e`/`--export` JSON adds an `errors` key when applicable.
- **Depth/Top/Sort Controls**: Added `--depth N` (collapses dirs-mode directory paths to N path components via `collapse_dirs_by_depth`), `--top N` (limits files-mode listing and the `-D` LARGEST FILES table), `--top-dirs N` / `--top-languages N` (caps dirs-mode and category-table rows), and `--sort loc|name|code|comments|ratio` (files-mode sorting via `sort_file_rows`) to `cli.py`, for taming output on large codebases.
- **`--quiet` Mode**: Added `-q`/`--quiet` to `cli.py` — prints only the total LOC count (no banner, spinner, or tables), for scripting like `LOC=$(neonloc . --quiet)`. Combines with `-e`/`--export` to still write the full export silently.
- **Git Integration**: Added `neonloc/git_info.py` with `--git` (shows branch, HEAD commit, author, and uncommitted `git diff --shortstat` changed/added/removed) and `--since <Nd|w|m|y>` (shows a daily `LOC TREND` table derived from `git log --numstat`, walked backward from the current scan total). Both are no-ops outside a Git repo. `-e`/`--export` JSON gains `git`/`loc_trend` keys when used.
- **Empty/Minimal File Detection**: `-D`/`--dist` now also shows an `EMPTY / MINIMAL FILES` table bucketing files at 0, 1-5, and 6-10 LOC with example paths (`bucket_minimal_files`/`build_minimal_files_table` in `cli.py`), for spotting dead files, placeholders, and generated junk. Fixed `analyze_directory` in `core.py` to keep 0-line files in `path_metrics` instead of skipping them outright (language/category totals are unaffected). `-e`/`--export` JSON adds `minimal_files`.
- **Duplicate-Code Detection**: Added `-X`/`--dup` and `core.detect_duplicates` — a normalized line-hash matcher (min 6-line blocks, extended to full match length) that finds duplicated code across files. Shows a `DUPLICATION` table (`Block A`/`Block B`/`Lines`) plus a `Duplication ratio`, also folded into the Project Summary panel. `count_file`/`analyze_directory` gained an opt-in `collect_lines`/`include_duplicates` path to capture normalized code lines without extra cost when unused. `-e`/`--export` JSON adds a `duplication` key when `-X` is set.
- **Script-Friendly Flags**: Added `--no-banner` (skips the screen clear + ASCII banner) and `--no-color` (forces `Console(no_color=True)`) to `cli.py` for use in scripts/CI; color already auto-disables when stdout isn't a TTY via Rich's own detection.
- **File Size Distribution**: Added `-D`/`--dist` to `cli.py`, showing a `FILE SIZE DISTRIBUTION` table (6 fixed LOC buckets via `bucket_file_sizes`) and a top-10 `LARGEST FILES` table. `-e`/`--export` JSON now always includes `size_distribution` and `largest_files`, independent of `-D`.
- **Blank Ratio in Summary**: `build_summary_panel` in `cli.py` now shows a `Blank ratio` row under `Comment ratio`.
- **Auto Mode as `-L` Default**: `-L`/`--list-loc` now defaults to `auto` when given without a mode, including `neonloc -L <directory>` — previously Click's optional-value parsing swallowed the directory token as an invalid mode value and errored. `main()` in `cli.py` now reinterprets an unrecognized `-L` value as the `DIRECTORY` argument.

## v0.5.2
- **Version Flag**: Added `-V`/`--version` to the `neonloc` CLI via `click.version_option`, reporting `neonloc.__version__`.
- **Timestamped Exports**: `write_export` in `cli.py` now names files `result_<YYYYMMDD_HHMMSS>.json`/`.txt` so repeated `-e` runs no longer overwrite prior exports, and prints a console hint to open the `.txt` in a monospace-font viewer.
- **Per-row Ratios**: Category, path, and tree tables in `cli.py` gained a `Code / Comm / Blank` percentage column (`ratio_str`); JSON export summary adds `code_ratio`/`comment_ratio`/`blank_ratio`.
- **Richer Project Summary**: `build_summary_panel` replaces the old one-line scan summary with a full breakdown (Files/Code/Comments/Blank/Total, Languages, Largest language %, Largest directory %, Comment ratio); path metrics are now always computed so the summary works without `-L`.

## v0.5.1
- **Matching TXT Export Layout**: `write_export` in `cli.py` now renders `result.txt` by piping the same `report_items` (category/path tables plus summary) through a `rich.Console` into a `StringIO` buffer, so the exported text report is byte-identical in layout to the console output.
- **Nested Tree View for `-L both`**: Replaced the separate directory/file tables in `cli.py`'s `build_path_tables` with a single indented tree table (`build_tree_table`) showing each directory followed by its nested files, recursing through subdirectories in hierarchical order.

## v0.5.0
- **JSON Export Option**: Added `-e`/`--export` in `cli.py` to write `result.json` under the scanned directory's `.neonloc` folder with summary, language metrics, and optional path metrics.
- **Single Version Source**: Switched `pyproject.toml` to setuptools dynamic versioning from `VERSION`, updated `neonloc.__version__` to read package metadata, and fixed release workflow checks for the top-level `neonloc` package layout.

## v0.4.2
- **Detailed LOC Report Mode**: Changed `-L`/`--list-loc` in `cli.py` to show only path-level LOC tables plus the final scan summary, and added `-h` as a help alias.

## v0.4.1
- **Trusted Publisher Release Workflow**: Added `.github/workflows/release.yml` to build, check, publish `neonloc` to PyPI, and create GitHub Releases from version tags.
- **Path LOC Tables**: Added `-L` and `--list-loc` support in `cli.py` with `auto`, `files`, `dirs`, and `both` modes backed by optional file and directory metrics from `core.py`.

## v0.4.0
- **Inline CSS and JS Parsing**: Upgraded `core.py` to intelligently parse embedded CSS and JavaScript inside HTML, Vue, Svelte, and PHP files. Inline scripts and styles are now uniquely identified, and their code, comments, and blanks are properly attributed to CSS and JavaScript metrics tables instead of being lumped into Markup.

## v0.3.0
- **GitIgnore Parsing**: Integrated `pathspec` to deeply respect `.gitignore` rules while traversing the directory tree, ensuring perfectly accurate code metrics without bloating.
- **Massive Language Expansion**: Expanded recognition to cover Jinja, Django Templates, SQL, CSV, XML, SVG, INI, Text files, C#, Swift, Kotlin, and config ignore files to capture everything recursive-ly and definitively.

## v0.2.1
- **Logo**: Added logo to the app.
- **Documentation Refined**: Updated `README.md` for official PyPI launch, shifting primary installation instructions to `pip install neonloc`, clarifying the features list with categorization details, and adding footer repository links.

## v0.2.0
- **Categorized Tracking**: Reintroduced Markdown, YAML, TOML, and JSON. Files are now rigorously categorized into `Code`, `Documentation`, `Config`, `Data`, `Markup`, and `Style`, displaying distinct metrics tables for each category in the CLI.

## v0.1.1
- **Removed Markdown Tracking**: Excluded Markdown from line counting as it is purely documentation and skews source code metrics.

## v0.1.0
- **Initial Release**: Bootstrapped the NeonLoc codebase with an edgy aesthetic terminal UI, rich tables, and basic code counting logic for major programming languages.
