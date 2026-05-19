import sys
from pathlib import Path

import yaml


_REQUIRED = [
    ("git", "repo_path"),
    ("git", "target_branch"),
    ("agent", "timeout_seconds"),
    ("verification", "type"),
    ("logging", "log_dir"),
]


def load(path: str = "config.yaml") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        sys.exit(
            f"ERROR: {path} not found. "
            f"Copy config.yaml.example to config.yaml and fill in your values."
        )

    with config_path.open() as f:
        try:
            cfg = yaml.safe_load(f)
        except yaml.YAMLError as e:
            sys.exit(f"ERROR: Failed to parse {path}: {e}")

    if not isinstance(cfg, dict):
        sys.exit(f"ERROR: {path} must be a YAML mapping.")

    missing = []
    for section, key in _REQUIRED:
        if not isinstance(cfg.get(section), dict) or cfg[section].get(key) is None:
            missing.append(f"{section}.{key}")

    if missing:
        sys.exit(f"ERROR: Missing required config fields: {', '.join(missing)}")

    return cfg
