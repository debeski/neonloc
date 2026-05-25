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

def count_file(filepath: Path, lang_def: dict) -> Dict[str, int]:
    stats = {"code": 0, "comments": 0, "blanks": 0, "total": 0}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            in_block_comment = False
            current_block_end = None
            
            for line in f:
                stats["total"] += 1
                sline = line.strip()
                
                if not sline:
                    stats["blanks"] += 1
                    continue
                    
                if in_block_comment:
                    stats["comments"] += 1
                    if current_block_end in sline:
                        in_block_comment = False
                        current_block_end = None
                    continue
                
                # Check for block comment start
                block_started = False
                for b_start, b_end in lang_def.get("multi", []):
                    if sline.startswith(b_start):
                        in_block_comment = True
                        current_block_end = b_end
                        stats["comments"] += 1
                        block_started = True
                        # Check if it ends on the same line
                        if b_end in sline[len(b_start):]:
                            in_block_comment = False
                            current_block_end = None
                        break
                
                if block_started:
                    continue
                
                # Check for single line comment
                is_single = False
                for s_cmt in lang_def.get("single", []):
                    if sline.startswith(s_cmt):
                        stats["comments"] += 1
                        is_single = True
                        break
                
                if not is_single:
                    stats["code"] += 1
    except Exception:
        # Ignore unreadable files quietly, keeping total edge
        pass
        
    return stats

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
            
            lang = get_language(file)
            if lang == "Unknown":
                continue
                
            stats = count_file(filepath, LANGUAGE_DEFS[lang])
            if stats["total"] == 0:
                continue
                
            if lang not in results:
                results[lang] = {"type": LANGUAGE_DEFS[lang].get("type", "Code"), "files": 0, "code": 0, "comments": 0, "blanks": 0, "total": 0}
                
            results[lang]["files"] += 1
            results[lang]["code"] += stats["code"]
            results[lang]["comments"] += stats["comments"]
            results[lang]["blanks"] += stats["blanks"]
            results[lang]["total"] += stats["total"]
            
    return results
