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
