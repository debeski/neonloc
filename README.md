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

Export the scan result as JSON:

```bash
neonloc . -e
```

Use `-e` or `--export` to write `result.json` and a matching console-style `result.txt` report under the scanned directory's `.neonloc` folder.

## Features

- **Categorized Metrics**: Distinct, color-coded tables for `Code`, `Documentation`, `Config`, `Data`, `Markup`, and `Style`.
- **Cyber Aesthetic**: Pure neon glory in your terminal, rendered with `Rich`.
- **Lightning Fast**: Scans and parses directories in the blink of an eye.
- **Language Support**: Python, JavaScript, TypeScript, Go, C/C++, Rust, HTML, CSS, YAML, JSON, Markdown, Bash, Ruby, Java, PHP, Vue, Svelte, TOML, Dockerfile.
- **Deep Metrics**: Counts true code logic, comments, blanks, and total lines.
- **Path LOC Tables**: Optional file and directory tables replace the generic category report, with `auto` choosing flat, modular, or mixed layout output.
- **Export Files**: Optional `-e`/`--export` writes the scan payload to `.neonloc/result.json` and the rendered report to `.neonloc/result.txt`.

---
[**View on PyPI**](https://pypi.org/project/neonloc/) • [**View on GitHub**](https://github.com/debeski/neonloc)
