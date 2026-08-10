# Project Tracker (NeonLoc) [Max 100 lines total]

## Part 1: Project Related [Max 55 lines]
### Current Verified Snapshot: 
- `neonloc` implemented with Python, Rich, and Click.
- CLI code counter groups files by category with an edgy UI.
- `-L`/`--list-loc` shows only detailed file/dir LOC tables with auto layout detection, followed by summary.
- GitHub Actions release workflow publishes tag builds to PyPI via Trusted Publishing.
- Package is officially published to PyPI and GitHub.
### Current Project Adopted Standards: 
- Python 3.8+ compatibility.
- Poetry/Setuptools based `pyproject.toml` structure.
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
- [x] Added tag-driven GitHub Actions release workflow for PyPI and GitHub Releases.
- [x] Added optional `-L`/`--list-loc` file/dir LOC tables.
- [x] Implement inline CSS and JS parsing for HTML, Vue, Svelte, and PHP files.
- [x] Implement SLOC parsing core logic.
- [x] Implement rich CLI interface.
- [x] Build edgy UI components.
### One-line info about last verified Tests: 
- `python3 -m compileall src` passed; CLI smoke blocked because system Python lacks `click` and checked-in venv has stale `/home/debeski/...` shebang.
### One-line info about last time edited Docs: 
- `README.md` documents `-L` detailed-only report behavior.

## Part 2: Global [Max 20 lines]
### Global Standard Helpers, Shortcuts, Info, etc.:
### Global Rulesets:
### Agent Handoff Rules:
### References and Links:
