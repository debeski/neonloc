import os
import pathspec
from pathlib import Path
from typing import Dict, Any, List

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

def count_file(filepath: Path, primary_lang: str) -> Dict[str, Dict[str, int]]:
    stats_by_lang = {primary_lang: {"code": 0, "comments": 0, "blanks": 0, "total": 0}}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            in_block_comment = False
            current_block_end = None
            current_lang = primary_lang
            
            for line in f:
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
    except Exception:
        pass
        
    return stats_by_lang

def analyze_directory(dirpath: str) -> Dict[str, Dict[str, int]]:
    results = {}
    base_path = Path(dirpath).resolve()
    
    spec = None
    gitignore_path = base_path / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
    
    for root, dirs, files in os.walk(base_path):
        if spec:
            valid_dirs = []
            for d in dirs:
                if d in IGNORE_DIRS or d.startswith('.'):
                    continue
                d_rel = (Path(root) / d).relative_to(base_path)
                if not spec.match_file(str(d_rel) + "/"):
                    valid_dirs.append(d)
            dirs[:] = valid_dirs
        else:
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        
        for file in files:
            filepath = Path(root) / file
            
            if spec:
                rel_path = filepath.relative_to(base_path)
                if spec.match_file(str(rel_path)):
                    continue
            
            primary_lang = get_language(file)
            if primary_lang == "Unknown":
                continue
                
            stats_by_lang = count_file(filepath, primary_lang)
            if sum(s["total"] for s in stats_by_lang.values()) == 0:
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
            
    return results
