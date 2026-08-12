# Project Tracker (NeonLoc) [Max 100 lines total]

## Part 1: Project Related [Max 55 lines]
### Current Verified Snapshot: 
- `neonloc` (Rich+Click CLI) groups files by category; `-L`/`--list-loc` adds file/dir/both LOC tables (`--depth`/`--top`/`--top-dirs`/`--top-languages`/`--sort`). `-D` size/empty/largest-file tables. `-X` `core.detect_duplicates` (line-hash).
- `core.count_file`/`analyze_directory` never swallow read errors (`path_metrics["errors"]` + FILE READ ERRORS table). `core.compute_health` (shared by CLI panel + HTML) drives always-on `Project Health` panel; thresholds configurable.
- New `neonloc/config.py`: loads `.neonloc.toml` (`[scan]`/`[output]`/`[thresholds]`, `tomllib`/`tomli` fallback) from target dir; CLI flags override. `neonloc/git_info.py`: `--git`, `--since <Nd|w|m|y>` LOC trend.
- `neonloc/html_report.py`: `--html <path>` writes a self-contained dark-themed HTML report (cards, tables, health, trend SVG). `-e`/`--export` writes timestamped `result_<ts>.json`/`.txt` under `.neonloc/`.
- `-V`/`--version`. `--no-banner`/`--no-color`/`-q`/`--quiet` for scripting; config `[output]` also controls banner/color defaults.
- `core.py` `FUNCTION_PATTERNS`/`CONSTANT_PATTERNS` (11 languages) + `collect_features` in `count_file`/`analyze_directory` find longest function (LOC span) / longest constant (value length); shown in Project Summary, HTML report, and export JSON `summary`.
### Current Project Adopted Standards: 
- Python 3.8+ compatibility.
- Setuptools based `pyproject.toml` with dynamic versioning from `VERSION`.
- `rich` for edgy terminal output.
### Adopted Standards' rules and policies: 
- Use absolute imports, modern type hinting.
- Use click for CLI.
### Cross-Cutting Audits if any: 
- None yet.
### Current Project's Unsolved Known Bugs: 
- None.
### Incomplete Tasks: 
### Completed Recently:
- [x] Fixed `Table.grid` (health/git/summary panels in `cli.py`) missing `expand=True`, causing right-aligned values to stay content-width instead of hugging the panel edge on wide terminals.
- [x] Added Longest function/constant to Project Summary (heuristic regex+brace/indent scan, `core.py`/`cli.py`/`html_report.py`).
- [x] Reworked `-L both` into a nested folder/file tree table instead of two flat tables.
- [x] Fixed release/package version mismatch by making `VERSION` the sole source for setuptools metadata and `neonloc.__version__`.
- [x] Added optional `-e`/`--export` JSON export under `.neonloc/result.json`.
- [x] Added tag-driven GitHub Actions release workflow for PyPI and GitHub Releases.
- [x] Added optional `-L`/`--list-loc` file/dir LOC tables.
- [x] Implement inline CSS and JS parsing for HTML, Vue, Svelte, and PHP files.
- [x] Implement SLOC parsing core logic.
- [x] Implement rich CLI interface.
- [x] Build edgy UI components.
### One-line info about last verified Tests: 
- `py_compile` on all `neonloc/*.py` passed; manual CLI smoke tests (config file, `--html`, `-D`/`-X`/`--git`/`--since`/`-q` combos) verified against scratch fixtures and this repo.
### One-line info about last time edited Docs: 
- `README.md` Usage/Features refreshed for all v0.6.0 flags (depth/top/sort, `-D`, `-X`, `--git`/`--since`, `--html`, `.neonloc.toml`).

## Part 2: Global [Max 20 lines]
### Global Standard Helpers, Shortcuts, Info, etc.:
### Global Rulesets:
### Agent Handoff Rules:
### References and Links:
