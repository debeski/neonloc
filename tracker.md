# Project Tracker (NeonLoc) [Max 100 lines total]

## Part 1: Project Related [Max 55 lines]
### Current Verified Snapshot: 
- `neonloc` implemented as a top-level Python package with Rich and Click.
- CLI code counter groups files by category with an edgy UI.
- `-L`/`--list-loc` shows detailed file/dir LOC tables with auto layout detection, followed by summary; `both` mode renders a single nested tree table (`build_tree_table` in `cli.py`) instead of separate dir/file tables.
- `-e`/`--export` writes JSON scan results to `<target>/.neonloc/result.json` plus a `result.txt` rendered from the same rich report tables (verified layout-identical to console output).
- `VERSION` is the single package version source; GitHub Actions publishes tag builds to PyPI via Trusted Publishing.
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
- `python3 -m compileall neonloc` passed; `python3 -m build --no-isolation` built `neonloc-0.5.1`; `python3 -m twine check dist/*` passed before artifacts moved to `.xpose/`.
### One-line info about last time edited Docs: 
- `docs/RELEASING.md` documents `VERSION` as the single release version source.

## Part 2: Global [Max 20 lines]
### Global Standard Helpers, Shortcuts, Info, etc.:
### Global Rulesets:
### Agent Handoff Rules:
### References and Links:
