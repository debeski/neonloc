import html as html_lib

CSS = """
:root {
  --bg: #0b0e14;
  --panel: #121620;
  --border: #232a3a;
  --text: #e6e8ee;
  --muted: #8891a7;
  --cyan: #4fd1e8;
  --magenta: #ff6bd6;
  --green: #39d6a5;
  --yellow: #f2c94c;
  --red: #ff5470;
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: "SF Mono", "Cascadia Code", "Fira Code", Consolas, monospace;
  margin: 0;
  padding: 2rem;
  line-height: 1.5;
}
header h1 {
  color: var(--green);
  letter-spacing: 0.1em;
  margin: 0 0 0.25rem 0;
}
.muted { color: var(--muted); font-size: 0.9rem; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}
.stat {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.stat .label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
.stat .value { color: var(--cyan); font-size: 1.5rem; font-weight: bold; }
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  overflow-x: auto;
}
.card h2 {
  color: var(--magenta);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 0;
}
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid var(--border); white-space: nowrap; }
th { color: var(--cyan); font-weight: normal; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
td:not(:first-child), th:not(:first-child) { text-align: right; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.35rem 1rem; margin: 0; }
dt { color: var(--muted); }
dd { margin: 0; color: var(--text); text-align: right; }
ul.warnings { list-style: none; margin: 1rem 0 0 0; padding: 0; }
ul.warnings li { padding: 0.35rem 0; }
ul.warnings li.warning { color: var(--yellow); }
ul.warnings li.error { color: var(--red); }
ul.warnings li.ok { color: var(--green); }
.trend-svg { width: 100%; height: auto; }
.trend-labels { display: flex; justify-content: space-between; color: var(--muted); font-size: 0.8rem; margin-top: 0.25rem; }
footer { color: var(--muted); font-size: 0.8rem; margin-top: 2rem; text-align: center; }
"""


def _esc(value) -> str:
    return html_lib.escape(str(value))


def _render_trend_svg(loc_trend):
    if not loc_trend or len(loc_trend) < 2:
        return ""
    values = [v for _, v in loc_trend]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    width, height, pad = 640, 160, 12
    n = len(loc_trend)
    step = (width - 2 * pad) / max(n - 1, 1)

    points = []
    for i, (_, v) in enumerate(loc_trend):
        x = pad + i * step
        y = pad + (height - 2 * pad) * (1 - (v - lo) / span)
        points.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(points)

    first_date, last_date = loc_trend[0][0], loc_trend[-1][0]
    return f"""
    <svg viewBox="0 0 {width} {height}" class="trend-svg" preserveAspectRatio="none">
      <polyline points="{poly}" fill="none" stroke="#39d6a5" stroke-width="2" />
    </svg>
    <div class="trend-labels"><span>{_esc(first_date)}</span><span>{_esc(last_date)}</span></div>
    """


def render_html_report(target_dir, generated_at, results, path_metrics, health,
                        dup_result=None, git_summary=None, loc_trend=None):
    total_files = sum(stats["files"] for stats in results.values())
    total_code = sum(stats["code"] for stats in results.values())
    total_comments = sum(stats["comments"] for stats in results.values())
    total_blanks = sum(stats["blanks"] for stats in results.values())
    total_lines = sum(stats["total"] for stats in results.values()) or 1
    comment_ratio = total_comments / total_lines * 100

    lang_rows = "".join(
        f"<tr><td>{_esc(lang)}</td><td>{stats['files']:,}</td><td>{stats['code']:,}</td>"
        f"<td>{stats['comments']:,}</td><td>{stats['blanks']:,}</td><td>{stats['total']:,}</td></tr>"
        for lang, stats in sorted(results.items(), key=lambda item: item[1]["total"], reverse=True)
    )

    dir_section = ""
    if path_metrics and path_metrics.get("dirs"):
        dir_rows = "".join(
            f"<tr><td>{_esc(row['path'])}</td><td>{row['files']:,}</td><td>{row['total']:,}</td></tr>"
            for row in sorted(path_metrics["dirs"], key=lambda r: r["total"], reverse=True)[:25]
        )
        dir_section = f"""
        <section class="card">
          <h2>Directories</h2>
          <table><thead><tr><th>Directory</th><th>Files</th><th>Total</th></tr></thead>
          <tbody>{dir_rows}</tbody></table>
        </section>
        """

    largest_section = ""
    if path_metrics and path_metrics.get("files"):
        largest_rows = "".join(
            f"<tr><td>{i}</td><td>{_esc(row['path'])}</td><td>{row['total']:,}</td></tr>"
            for i, row in enumerate(sorted(path_metrics["files"], key=lambda r: r["total"], reverse=True)[:15], start=1)
        )
        largest_section = f"""
        <section class="card">
          <h2>Largest Files</h2>
          <table><thead><tr><th>#</th><th>File</th><th>Total</th></tr></thead>
          <tbody>{largest_rows}</tbody></table>
        </section>
        """

    warnings_html = "".join(
        f'<li class="{_esc(w["severity"])}">⚠ {_esc(w["text"])}</li>' for w in health["warnings"]
    ) or '<li class="ok">No warnings — codebase looks healthy.</li>'

    largest_file = health["largest_file"]
    largest_file_text = (
        f"{_esc(largest_file['path'])} ({largest_file['total']:,} LOC)" if largest_file else "-"
    )

    git_section = ""
    if git_summary:
        git_section = f"""
        <section class="card">
          <h2>Git</h2>
          <dl>
            <dt>Branch</dt><dd>{_esc(git_summary['branch'])}</dd>
            <dt>Commit</dt><dd>{_esc(git_summary['commit'])}</dd>
            <dt>Author</dt><dd>{_esc(git_summary['author'])}</dd>
            <dt>Changed</dt><dd>{git_summary['changed_files']:,} files</dd>
            <dt>Added</dt><dd>+{git_summary['added']:,} LOC</dd>
            <dt>Removed</dt><dd>-{git_summary['removed']:,} LOC</dd>
          </dl>
        </section>
        """

    dup_section = ""
    if dup_result is not None:
        dup_rows = "".join(
            f"<tr><td>{_esc(m['a']['path'])}:{m['a']['start_line']}-{m['a']['end_line']}</td>"
            f"<td>{_esc(m['b']['path'])}:{m['b']['start_line']}-{m['b']['end_line']}</td>"
            f"<td>{m['lines']:,}</td></tr>"
            for m in dup_result["matches"][:20]
        )
        dup_section = f"""
        <section class="card">
          <h2>Duplication — {dup_result['ratio']:.1f}%</h2>
          <table><thead><tr><th>Block A</th><th>Block B</th><th>Lines</th></tr></thead>
          <tbody>{dup_rows or '<tr><td colspan="3">No duplicated blocks found.</td></tr>'}</tbody></table>
        </section>
        """

    trend_section = ""
    trend_svg = _render_trend_svg(loc_trend)
    if trend_svg:
        trend_section = f"""
        <section class="card">
          <h2>LOC Trend</h2>
          {trend_svg}
        </section>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>neonloc report — {_esc(target_dir.name)}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>NEONLOC</h1>
  <p class="muted">{_esc(str(target_dir))} — generated {_esc(generated_at)}</p>
</header>

<section class="cards">
  <div class="stat"><span class="label">Files</span><span class="value">{total_files:,}</span></div>
  <div class="stat"><span class="label">Code</span><span class="value">{total_code:,}</span></div>
  <div class="stat"><span class="label">Comments</span><span class="value">{total_comments:,}</span></div>
  <div class="stat"><span class="label">Blank</span><span class="value">{total_blanks:,}</span></div>
  <div class="stat"><span class="label">Total</span><span class="value">{total_lines:,}</span></div>
  <div class="stat"><span class="label">Comment Ratio</span><span class="value">{comment_ratio:.1f}%</span></div>
</section>

<section class="card">
  <h2>Language Breakdown</h2>
  <table><thead><tr><th>Language</th><th>Files</th><th>Code</th><th>Comments</th><th>Blanks</th><th>Total</th></tr></thead>
  <tbody>{lang_rows}</tbody></table>
</section>

{dir_section}
{largest_section}

<section class="card">
  <h2>Project Health</h2>
  <dl>
    <dt>Code Ratio</dt><dd>{health['code_ratio']:.1f}%</dd>
    <dt>Average File Size</dt><dd>{health['avg_size']:.0f} LOC</dd>
    <dt>Largest File</dt><dd>{largest_file_text}</dd>
    <dt>Empty Files</dt><dd>{health['empty_files']:,}</dd>
    <dt>Huge Files (&gt;{health['huge_file_loc']} LOC)</dt><dd>{health['huge_files']:,}</dd>
  </dl>
  <ul class="warnings">{warnings_html}</ul>
</section>

{dup_section}
{git_section}
{trend_section}

<footer>Generated by neonloc</footer>
</body>
</html>
"""
