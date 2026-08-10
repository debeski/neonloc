## v0.5.1
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
