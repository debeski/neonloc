import os
import pathspec
from pathlib import Path
from typing import Any, Dict

LANGUAGE_DEFS = {
    "Python": {"type": "Code", "exts": [".py", ".pyw", ".pyx"], "single": ["#"], "multi": [('"""', '"""'), ("'''", "'''")]},
    "JavaScript": {"type": "Code", "exts": [".js", ".jsx", ".mjs", ".cjs"], "single": ["//"], "multi": [("/*", "*/")]},
    "TypeScript": {"type": "Code", "exts": [".ts", ".tsx"], "single": ["//"], "multi": [("/*", "*/")]},
    "Go": {"type": "Code", "exts": [".go"], "single": ["//"], "multi": [("/*", "*/")]},
    "C/C++": {"type": "Code", "exts": [".c", ".cpp", ".h", ".hpp", ".cc", ".cxx"], "single": ["//"], "multi": [("/*", "*/")]},
    "C#": {"type": "Code", "exts": [".cs"], "single": ["//"], "multi": [("/*", "*/")]},
    "Rust": {"type": "Code", "exts": [".rs"], "single": ["//"], "multi": [("/*", "*/")]},
    "Swift": {"type": "Code", "exts": [".swift"], "single": ["//"], "multi": [("/*", "*/")]},
    "Kotlin": {"type": "Code", "exts": [".kt", ".kts"], "single": ["//"], "multi": [("/*", "*/")]},
    "HTML": {"type": "Markup", "exts": [".html", ".htm"], "single": [], "multi": [("<!--", "-->")]},
    "Jinja/Django": {"type": "Markup", "exts": [".jinja", ".jinja2", ".j2", ".twig", ".njk"], "single": [], "multi": [("<!--", "-->"), ("{#", "#}")]},
    "XML/SVG": {"type": "Markup", "exts": [".xml", ".svg"], "single": [], "multi": [("<!--", "-->")]},
    "CSS": {"type": "Style", "exts": [".css", ".scss", ".sass", ".less"], "single": [], "multi": [("/*", "*/")]},
    "YAML": {"type": "Config", "exts": [".yml", ".yaml"], "single": ["#"], "multi": []},
    "JSON": {"type": "Data", "exts": [".json"], "single": [], "multi": []},
    "SQL": {"type": "Data", "exts": [".sql"], "single": ["--"], "multi": [("/*", "*/")]},
    "CSV": {"type": "Data", "exts": [".csv", ".tsv"], "single": [], "multi": []},
    "Markdown": {"type": "Documentation", "exts": [".md", ".markdown"], "single": [], "multi": []},
    "Text": {"type": "Documentation", "exts": [".txt"], "single": [], "multi": []},
    "Bash/Shell": {"type": "Code", "exts": [".sh", ".bash"], "single": ["#"], "multi": []},
    "Ruby": {"type": "Code", "exts": [".rb"], "single": ["#"], "multi": [("=begin", "=end")]},
    "Java": {"type": "Code", "exts": [".java"], "single": ["//"], "multi": [("/*", "*/")]},
    "PHP": {"type": "Code", "exts": [".php"], "single": ["//", "#"], "multi": [("/*", "*/")]},
    "Vue": {"type": "Code", "exts": [".vue"], "single": ["//"], "multi": [("<!--", "-->"), ("/*", "*/")]},
    "Svelte": {"type": "Code", "exts": [".svelte"], "single": ["//"], "multi": [("<!--", "-->"), ("/*", "*/")]},
    "TOML": {"type": "Config", "exts": [".toml"], "single": ["#"], "multi": []},
    "INI/Config": {"type": "Config", "exts": [".ini", ".cfg", ".conf"], "single": [";", "#"], "multi": []},
    "Dockerfile": {"type": "Config", "exts": [".dockerfile"], "exact": ["Dockerfile", "Dockerfile.dev"], "single": ["#"], "multi": []},
    "IgnoreFiles": {"type": "Config", "exts": [".gitignore", ".dockerignore", ".npmignore", ".eslintignore"], "single": ["#"], "multi": []},
}

IGNORE_DIRS = {
    "node_modules", "venv", "env", ".env", ".git", ".idea", ".vscode",
    "__pycache__", "build", "dist", ".pytest_cache", ".next", ".nuxt",
    "target", "vendor"
}

def get_language(filename: str) -> str:
    # Check exact match first (e.g. Dockerfile)
    for lang, df in LANGUAGE_DEFS.items():
        if "exact" in df and filename in df["exact"]:
            return lang
            
    # Check extension
    ext = Path(filename).suffix.lower()
    for lang, df in LANGUAGE_DEFS.items():
        if "exts" in df and ext in df["exts"]:
            return lang
    
    return "Unknown"

def count_file(filepath: Path, primary_lang: str, collect_lines: bool = False):
    stats_by_lang = {primary_lang: {"code": 0, "comments": 0, "blanks": 0, "total": 0}}
    code_lines = [] if collect_lines else None
    error = None
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            in_block_comment = False
            current_block_end = None
            current_lang = primary_lang

            for line_no, line in enumerate(f, start=1):
                sline = line.strip()
                lower_line = sline.lower()

                if not sline:
                    stats_by_lang[current_lang]["total"] += 1
                    stats_by_lang[current_lang]["blanks"] += 1
                    continue

                line_lang = current_lang
                
                # Context switching logic
                if not in_block_comment:
                    if current_lang == primary_lang and (LANGUAGE_DEFS.get(primary_lang, {}).get("type") == "Markup" or primary_lang in ["Vue", "Svelte", "PHP"]):
                        if "<script" in lower_line and "</script>" not in lower_line and "<!--" not in lower_line:
                            current_lang = "JavaScript"
                            line_lang = primary_lang
                        elif "<style" in lower_line and "</style>" not in lower_line and "<!--" not in lower_line:
                            current_lang = "CSS"
                            line_lang = primary_lang
                    elif current_lang != primary_lang:
                        if current_lang == "JavaScript" and "</script>" in lower_line:
                            current_lang = primary_lang
                            line_lang = primary_lang
                        elif current_lang == "CSS" and "</style>" in lower_line:
                            current_lang = primary_lang
                            line_lang = primary_lang
                
                if line_lang not in stats_by_lang:
                    stats_by_lang[line_lang] = {"code": 0, "comments": 0, "blanks": 0, "total": 0}
                
                stats_by_lang[line_lang]["total"] += 1
                line_lang_def = LANGUAGE_DEFS.get(line_lang, {})
                
                if in_block_comment:
                    stats_by_lang[line_lang]["comments"] += 1
                    if current_block_end in sline:
                        in_block_comment = False
                        current_block_end = None
                    continue
                
                block_started = False
                for b_start, b_end in line_lang_def.get("multi", []):
                    if sline.startswith(b_start):
                        in_block_comment = True
                        current_block_end = b_end
                        stats_by_lang[line_lang]["comments"] += 1
                        block_started = True
                        if b_end in sline[len(b_start):]:
                            in_block_comment = False
                            current_block_end = None
                        break
                
                if block_started:
                    continue
                
                is_single = False
                for s_cmt in line_lang_def.get("single", []):
                    if sline.startswith(s_cmt):
                        stats_by_lang[line_lang]["comments"] += 1
                        is_single = True
                        break
                
                if not is_single:
                    stats_by_lang[line_lang]["code"] += 1
                    if collect_lines:
                        code_lines.append((line_no, sline))
    except Exception as exc:
        error = str(exc) or exc.__class__.__name__

    return stats_by_lang, code_lines, error

def _empty_stats() -> Dict[str, int]:
    return {"files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}

def _add_stats(target: Dict[str, int], source: Dict[str, int]) -> None:
    for key in ("code", "comments", "blanks", "total"):
        target[key] += source[key]

def _file_totals(stats_by_lang: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    totals = _empty_stats()
    totals["files"] = 1
    for stats in stats_by_lang.values():
        _add_stats(totals, stats)
    return totals

def analyze_directory(
    dirpath: str,
    include_paths: bool = False,
    include_duplicates: bool = False,
    respect_gitignore: bool = True,
    include_hidden: bool = False,
    include_generated: bool = False,
) -> Any:
    results = {}
    file_stats = []
    dir_stats = {}
    errors = []
    code_lines_by_file = {} if include_duplicates else None
    base_path = Path(dirpath).resolve()

    spec = None
    gitignore_path = base_path / ".gitignore"
    if respect_gitignore and gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)

    def dir_allowed(d):
        if not include_generated and d in IGNORE_DIRS:
            return False
        if not include_hidden and d.startswith('.'):
            return False
        return True

    for root, dirs, files in os.walk(base_path):
        if spec:
            valid_dirs = []
            for d in dirs:
                if not dir_allowed(d):
                    continue
                d_rel = (Path(root) / d).relative_to(base_path)
                if not spec.match_file(str(d_rel) + "/"):
                    valid_dirs.append(d)
            dirs[:] = valid_dirs
        else:
            dirs[:] = [d for d in dirs if dir_allowed(d)]
        
        for file in files:
            filepath = Path(root) / file
            
            if spec:
                rel_path = filepath.relative_to(base_path)
                if spec.match_file(str(rel_path)):
                    continue
            
            primary_lang = get_language(file)
            if primary_lang == "Unknown":
                continue

            rel_path = filepath.relative_to(base_path)
            stats_by_lang, code_lines, error = count_file(filepath, primary_lang, collect_lines=include_duplicates)
            if error:
                errors.append({"path": str(rel_path), "error": error})
                continue
            is_empty = sum(s["total"] for s in stats_by_lang.values()) == 0

            if include_duplicates and not is_empty and code_lines:
                code_lines_by_file[str(rel_path)] = code_lines

            if include_paths:
                file_total = _file_totals(stats_by_lang)
                file_total["language"] = primary_lang
                file_total["path"] = str(rel_path)
                file_stats.append(file_total)

                parent = rel_path.parent
                dir_key = "." if str(parent) == "." else str(parent)
                if dir_key not in dir_stats:
                    dir_stats[dir_key] = _empty_stats()
                dir_stats[dir_key]["files"] += 1
                _add_stats(dir_stats[dir_key], file_total)

            if is_empty:
                continue

            if primary_lang not in results:
                results[primary_lang] = {"type": LANGUAGE_DEFS[primary_lang].get("type", "Code"), "files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
            results[primary_lang]["files"] += 1

            for lang, stats in stats_by_lang.items():
                if stats["total"] == 0:
                    continue
                    
                if lang not in results:
                    results[lang] = {"type": LANGUAGE_DEFS.get(lang, {}).get("type", "Code"), "files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
                    
                results[lang]["code"] += stats["code"]
                results[lang]["comments"] += stats["comments"]
                results[lang]["blanks"] += stats["blanks"]
                results[lang]["total"] += stats["total"]
            
    if include_paths:
        path_metrics = {
            "files": sorted(file_stats, key=lambda item: item["total"], reverse=True),
            "dirs": sorted(
                [{"path": path, **stats} for path, stats in dir_stats.items()],
                key=lambda item: item["total"],
                reverse=True
            ),
            "errors": errors,
        }
        if include_duplicates:
            path_metrics["code_lines"] = code_lines_by_file
        return results, path_metrics

    return results

DEFAULT_HUGE_FILE_LOC = 500
DEFAULT_VERY_HUGE_FILE_LOC = 1000

def compute_health(results: Dict[str, Dict[str, int]], path_metrics: Dict[str, Any],
                    huge_file_loc: int = DEFAULT_HUGE_FILE_LOC,
                    very_huge_file_loc: int = DEFAULT_VERY_HUGE_FILE_LOC) -> Dict[str, Any]:
    files = path_metrics["files"] if path_metrics else []
    total_files = len(files)
    total_lines = sum(stats["total"] for stats in results.values())
    total_code = sum(stats["code"] for stats in results.values())
    code_ratio = (total_code / total_lines * 100) if total_lines else 0.0
    avg_size = (sum(f["total"] for f in files) / total_files) if total_files else 0.0
    largest_file = max(files, key=lambda f: f["total"], default=None)
    empty_files = sum(1 for f in files if f["total"] == 0)
    huge_files = sum(1 for f in files if f["total"] > huge_file_loc)
    very_huge_files = sum(1 for f in files if f["total"] > very_huge_file_loc)
    minimal_files = sum(1 for f in files if 1 <= f["total"] <= 10)
    error_count = len(path_metrics.get("errors", [])) if path_metrics else 0

    warnings = []
    if huge_files:
        noun, verb = ("file", "exceeds") if huge_files == 1 else ("files", "exceed")
        warnings.append({"text": f"{huge_files} {noun} {verb} {huge_file_loc} LOC", "severity": "warning"})
    if very_huge_files:
        noun, verb = ("file", "exceeds") if very_huge_files == 1 else ("files", "exceed")
        warnings.append({"text": f"{very_huge_files} {noun} {verb} {very_huge_file_loc:,} LOC", "severity": "warning"})
    if minimal_files:
        noun, verb = ("file", "contains") if minimal_files == 1 else ("files", "contain")
        warnings.append({"text": f"{minimal_files} {noun} {verb} very little executable code", "severity": "warning"})
    if error_count:
        noun = "file" if error_count == 1 else "files"
        warnings.append({"text": f"{error_count} {noun} could not be analyzed", "severity": "error"})

    return {
        "code_ratio": code_ratio,
        "avg_size": avg_size,
        "largest_file": largest_file,
        "empty_files": empty_files,
        "huge_files": huge_files,
        "very_huge_files": very_huge_files,
        "minimal_files": minimal_files,
        "error_count": error_count,
        "huge_file_loc": huge_file_loc,
        "very_huge_file_loc": very_huge_file_loc,
        "warnings": warnings,
    }

MIN_DUPLICATE_BLOCK = 6

def detect_duplicates(code_lines_by_file: Dict[str, list], min_block: int = MIN_DUPLICATE_BLOCK) -> Dict[str, Any]:
    sequences = {path: [text for _, text in lines] for path, lines in code_lines_by_file.items()}
    line_numbers = {path: [no for no, _ in lines] for path, lines in code_lines_by_file.items()}

    window_index: Dict[int, list] = {}
    for path, seq in sequences.items():
        for i in range(len(seq) - min_block + 1):
            window = tuple(seq[i:i + min_block])
            window_index.setdefault(hash(window), []).append((path, i))

    covered: Dict[str, set] = {}
    matches = []
    seen_pairs = set()
    seen_regions = set()

    for occurrences in window_index.values():
        if len(occurrences) < 2:
            continue
        for a in range(len(occurrences)):
            for b in range(a + 1, len(occurrences)):
                pa, ia = occurrences[a]
                pb, ib = occurrences[b]
                if pa == pb and abs(ia - ib) < min_block:
                    continue
                key = ((pa, ia), (pb, ib)) if (pa, ia) <= (pb, ib) else ((pb, ib), (pa, ia))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)

                seq_a, seq_b = sequences[pa], sequences[pb]
                if seq_a[ia:ia + min_block] != seq_b[ib:ib + min_block]:
                    continue

                start_a, start_b = ia, ib
                while start_a > 0 and start_b > 0 and seq_a[start_a - 1] == seq_b[start_b - 1] and (pa != pb or start_a - 1 != start_b):
                    start_a -= 1
                    start_b -= 1

                end_a, end_b = ia + min_block, ib + min_block
                while end_a < len(seq_a) and end_b < len(seq_b) and seq_a[end_a] == seq_b[end_b] and (pa != pb or end_a != end_b):
                    end_a += 1
                    end_b += 1

                region_key = (pa, start_a, end_a, pb, start_b, end_b)
                if region_key in seen_regions:
                    continue
                seen_regions.add(region_key)

                matches.append({
                    "a": {"path": pa, "start_line": line_numbers[pa][start_a], "end_line": line_numbers[pa][end_a - 1]},
                    "b": {"path": pb, "start_line": line_numbers[pb][start_b], "end_line": line_numbers[pb][end_b - 1]},
                    "lines": end_a - start_a,
                })
                covered.setdefault(pa, set()).update(range(start_a, end_a))
                covered.setdefault(pb, set()).update(range(start_b, end_b))

    matches.sort(key=lambda m: m["lines"], reverse=True)
    duplicate_lines = sum(len(idxs) for idxs in covered.values())
    total_code_lines = sum(len(seq) for seq in sequences.values()) or 1

    return {
        "matches": matches,
        "duplicate_lines": duplicate_lines,
        "total_code_lines": total_code_lines,
        "ratio": round(duplicate_lines / total_code_lines * 100, 1),
    }
