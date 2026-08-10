import re
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SINCE_RE = re.compile(r"^(\d+)([dwmy])$", re.IGNORECASE)
UNIT_DAYS = {"d": 1, "w": 7, "m": 30, "y": 365}


def _run(target_dir: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(target_dir), *args],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_git_repo(target_dir: Path) -> bool:
    return _run(target_dir, "rev-parse", "--is-inside-work-tree") == "true"


def get_git_summary(target_dir: Path) -> Optional[Dict[str, Any]]:
    if not is_git_repo(target_dir):
        return None

    branch = _run(target_dir, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    commit = _run(target_dir, "rev-parse", "--short", "HEAD") or "unknown"
    author = _run(target_dir, "log", "-1", "--pretty=format:%an") or "unknown"
    shortstat = _run(target_dir, "diff", "--shortstat", "HEAD") or ""

    changed_files = added = removed = 0
    m = re.search(r"(\d+) files? changed", shortstat)
    if m:
        changed_files = int(m.group(1))
    m = re.search(r"(\d+) insertions?\(\+\)", shortstat)
    if m:
        added = int(m.group(1))
    m = re.search(r"(\d+) deletions?\(-\)", shortstat)
    if m:
        removed = int(m.group(1))

    return {
        "branch": branch,
        "commit": commit,
        "author": author,
        "changed_files": changed_files,
        "added": added,
        "removed": removed,
    }


def parse_since(value: str) -> int:
    m = SINCE_RE.match(value.strip())
    if not m:
        raise ValueError(f"Invalid --since value '{value}'. Use a number plus d/w/m/y, e.g. 30d, 4w, 6m, 1y.")
    return int(m.group(1)) * UNIT_DAYS[m.group(2).lower()]


def get_loc_trend(target_dir: Path, since_days: int, current_total: int) -> Optional[List[Tuple[str, int]]]:
    if not is_git_repo(target_dir):
        return None

    since_date = date.today() - timedelta(days=since_days)
    out = _run(
        target_dir, "log", f"--since={since_date.isoformat()}",
        "--date=format:%Y-%m-%d", "--pretty=format:C|%ad", "--numstat"
    )
    if out is None:
        return None

    net_by_day: Dict[str, int] = {}
    current_date = None
    for line in out.splitlines():
        if line.startswith("C|"):
            current_date = line[2:]
            continue
        if not line.strip() or current_date is None:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add_s, del_s, _ = parts
        add_n = int(add_s) if add_s.isdigit() else 0
        del_n = int(del_s) if del_s.isdigit() else 0
        net_by_day[current_date] = net_by_day.get(current_date, 0) + (add_n - del_n)

    days = []
    d = date.today()
    while d >= since_date:
        days.append(d)
        d -= timedelta(days=1)
    days.reverse()

    totals: Dict[str, int] = {}
    running = current_total
    totals[days[-1].isoformat()] = running
    for d in reversed(days[:-1]):
        next_day_key = (d + timedelta(days=1)).isoformat()
        running -= net_by_day.get(next_day_key, 0)
        totals[d.isoformat()] = running

    return [(d.isoformat(), totals[d.isoformat()]) for d in days]
