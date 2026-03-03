"""
Shared contract utilities.

Single source of truth for modes, feature schema, and per-mode crop metadata.
Backed by Aiml/model_registry.json.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    # Backend/app/apps/contract.py -> CRS root
    return Path(__file__).resolve().parents[3]


def _resolve_registry_path() -> Path:
    env_path = os.environ.get("MODEL_REGISTRY_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = (_project_root() / p).resolve()
        if p.exists():
            return p

    ai_ml_dir = os.environ.get("AI_ML_DIR")
    if ai_ml_dir:
        p = Path(ai_ml_dir).resolve() / "model_registry.json"
        if p.exists():
            return p

    return _project_root() / "Aiml" / "model_registry.json"


@lru_cache(maxsize=1)
def load_model_registry() -> dict[str, Any]:
    path = _resolve_registry_path()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def clear_registry_cache() -> None:
    load_model_registry.cache_clear()


def get_contract_config() -> dict[str, Any]:
    registry = load_model_registry()
    contract = registry.get("contract", {})
    if not contract:
        return {
            "modes": ["soil", "extended", "both"],
            "mode_aliases": {"original": "soil", "synthetic": "extended", "real": "soil"},
            "default_mode": "soil",
            "feature_schema": {},
        }
    return contract


def get_available_modes() -> list[str]:
    return list(get_contract_config().get("modes", ["soil", "extended", "both"]))


def get_mode_aliases() -> dict[str, str]:
    aliases = dict(get_contract_config().get("mode_aliases", {}))
    # Keep compatibility even if alias is omitted from registry
    aliases.setdefault("original", "soil")
    aliases.setdefault("synthetic", "extended")
    aliases.setdefault("real", "soil")
    return aliases


def get_default_mode() -> str:
    return str(get_contract_config().get("default_mode", "soil"))


def canonicalize_mode(mode: str | None) -> str:
    normalized = (mode or get_default_mode()).strip().lower()
    normalized = get_mode_aliases().get(normalized, normalized)
    if normalized not in set(get_available_modes()):
        valid = ", ".join(get_available_modes())
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid}")
    return normalized


def get_feature_schema() -> dict[str, dict[str, Any]]:
    return dict(get_contract_config().get("feature_schema", {}))


def get_feature_rule(feature_name: str) -> dict[str, Any]:
    schema = get_feature_schema()
    if feature_name not in schema:
        raise KeyError(f"Feature '{feature_name}' not found in contract schema")
    return schema[feature_name]


def get_model_metadata(mode: str | None = None) -> dict[str, Any]:
    models = load_model_registry().get("models", {})
    if mode is None:
        return models
    return models.get(canonicalize_mode(mode), {})


def get_crop_labels(mode: str) -> list[str]:
    mode_meta = get_model_metadata(mode)
    labels = mode_meta.get("crop_labels", [])
    return [str(v) for v in labels]


def get_crop_count(mode: str) -> int:
    labels = get_crop_labels(mode)
    if labels:
        return len(labels)
    mode_meta = get_model_metadata(mode)
    return int(mode_meta.get("crop_count", 0))


def build_public_contract() -> dict[str, Any]:
    models = get_model_metadata()
    model_summary = {}
    for mode in get_available_modes():
        meta = models.get(mode, {})
        model_summary[mode] = {
            "crop_count": int(meta.get("crop_count", 0)),
            "feature_count": int(meta.get("feature_count", 0)),
            "type": meta.get("type", ""),
            "crop_labels": [str(v) for v in meta.get("crop_labels", [])],
        }

    return {
        "version": load_model_registry().get("version"),
        "modes": get_available_modes(),
        "mode_aliases": get_mode_aliases(),
        "default_mode": get_default_mode(),
        "feature_schema": get_feature_schema(),
        "models": model_summary,
    }
