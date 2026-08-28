from pathlib import Path

import yaml

from ..config import settings


def _load(name: str) -> dict:
    p = Path(settings.configs_dir) / name
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_pricing() -> dict:
    return _load("pricing.yaml")


def load_models() -> dict:
    return _load("models.yaml")


def load_membership() -> dict:
    return _load("membership.yaml")
