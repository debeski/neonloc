import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

CONFIG_FILENAME = ".neonloc.toml"

DEFAULT_CONFIG = {
    "scan": {
        "respect_gitignore": True,
        "include_hidden": False,
        "include_generated": False,
    },
    "output": {
        "color": True,
        "banner": True,
    },
    "thresholds": {
        "large_file": 500,
        "huge_file": 1000,
    },
}


def load_config(target_dir: Path) -> dict:
    config = {section: dict(values) for section, values in DEFAULT_CONFIG.items()}
    config_path = target_dir / CONFIG_FILENAME
    if not config_path.exists():
        return config

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return config

    for section, values in data.items():
        if section in config and isinstance(values, dict):
            config[section].update(values)

    return config
