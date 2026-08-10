# NeonLoc

A blazingly fast, cyber-styled source code counter. Count your lines with pure edge.

[![PyPI version](https://badge.fury.io/py/neonloc.svg)](https://pypi.org/project/neonloc/)

<p align="center">
  <img src="https://raw.githubusercontent.com/debeski/neonloc/main/logo.png" alt="NeonLoc Logo" width="450"/>
</p>

## Installation

Install directly from PyPI:

```bash
pip install neonloc
```

**From source:**
```bash
git clone https://github.com/debeski/neonloc.git
cd neonloc
pip install .
```

## Usage

Simply run `neonloc` in your terminal and pass a directory. By default, it will use the current directory (`.`).

```bash
neonloc .
```

Or target a specific folder:

```bash
neonloc /path/to/project
```

List line metrics by layout-aware paths:

```bash
neonloc . -L auto
```

Use `-L files`, `--list-loc dirs`, or `--list-loc both` to force file, directory, or combined LOC tables.
When `-L` is passed, NeonLoc shows only the detailed path table view plus the final scan summary.
Tame large listings with `--depth N` (dirs mode), `--top`/`--top-dirs`/`--top-languages N`, and `--sort loc|name|code|comments|ratio` (files mode).

Export the scan result as JSON + text report:

```bash
neonloc . -e
```

Writes timestamped `result_<timestamp>.json`/`.txt` files under the scanned directory's `.neonloc` folder (never overwritten).

Export a standalone HTML report:

```bash
neonloc . --html report.html
```

Other useful flags:

```bash
neonloc . -D              # file-size distribution, empty/minimal files, largest files
neonloc . -X              # duplicate-code detection (normalized line-hash matching)
neonloc . --git           # branch, HEAD commit, author, uncommitted diffstat
neonloc . --since 30d     # daily LOC trend from Git history (also accepts w/m/y)
neonloc . -q              # print only the total LOC count, for scripting
neonloc . --no-banner --no-color  # script-friendly output
```

Configure defaults with a `.neonloc.toml` file in the scanned directory, so `neonloc .` just works:

```toml
[scan]
respect_gitignore = true
include_hidden = false
include_generated = false

[output]
color = true
banner = true

[thresholds]
large_file = 500
huge_file = 1000
```

## Features

- **Categorized Metrics**: Distinct, color-coded tables for `Code`, `Documentation`, `Config`, `Data`, `Markup`, and `Style`, each with a `Code / Comment / Blank` ratio column.
- **Cyber Aesthetic**: Pure neon glory in your terminal, rendered with `Rich`.
- **Lightning Fast**: Scans and parses directories in the blink of an eye.
- **Language Support**: Python, JavaScript, TypeScript, Go, C/C++, C#, Rust, Swift, Kotlin, HTML, Jinja/Django, XML/SVG, CSS, YAML, JSON, SQL, CSV, Markdown, Text, Bash, Ruby, Java, PHP, Vue, Svelte, TOML, INI/Config, Dockerfile, and common ignore files (`.gitignore`, etc.).
- **Deep Metrics**: Counts true code logic, comments, blanks, and total lines.
- **Path LOC Tables**: Optional file and directory tables replace the generic category report, with `auto` choosing flat, modular, or mixed layout output. Supports depth limiting, top-N caps, and sorting.
- **Project Health**: Always-on panel with code ratio, average file size, largest file, empty/huge-file counts, and warnings — plus a `FILE READ ERRORS` table for any file NeonLoc couldn't analyze (never silently skipped).
- **File Size Distribution & Duplication**: `-D` shows size buckets, empty/minimal files, and the largest files; `-X` detects duplicated code blocks across files.
- **Git Integration**: `--git` shows branch/commit/author/diffstat; `--since` shows a daily LOC trend derived from Git history.
- **Config File**: Drop a `.neonloc.toml` in your project to set scan, output, and threshold defaults.
- **Export Files**: `-e`/`--export` writes timestamped JSON + text reports to `.neonloc/`; `--html` writes a standalone, self-contained HTML report.
- **Scripting Friendly**: `-q`/`--quiet`, `--no-banner`, `--no-color`.

---
[**View on PyPI**](https://pypi.org/project/neonloc/) • [**View on GitHub**](https://github.com/debeski/neonloc)
