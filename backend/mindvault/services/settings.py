from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import sessionmaker

from mindvault.db.models import AppSetting
from mindvault.errors import ValidationFailed

DEFAULTS: dict[str, Any] = {
    "ai": {
        "provider": "auto",
        "model": "",
        "temperature": 0.2,
        "max_tokens": 1024,
        "context_size": 4096,
    },
    "embeddings": {
        "provider": "auto",
        "model": "all-MiniLM-L6-v2",
        "dim": 384,
        "rebuild_required": False,
    },
    "retrieval": {
        "top_k": 8,
        "similarity_threshold": 0.05,
        "chunk_size": 900,
        "chunk_overlap": 120,
        "max_context_chars": 9000,
        "rerank_enabled": False,
    },
    "privacy": {
        "telemetry_enabled": False,
        "external_apis_enabled": False,
    },
    "appearance": {
        "theme": "system",
    },
    "storage": {},
}

_KNOWN_KEYS: dict[str, type] = {
    "ai.provider": str,
    "ai.model": str,
    "ai.temperature": float,
    "ai.max_tokens": int,
    "ai.context_size": int,
    "embeddings.provider": str,
    "embeddings.model": str,
    "embeddings.dim": int,
    "embeddings.rebuild_required": bool,
    "retrieval.top_k": int,
    "retrieval.similarity_threshold": float,
    "retrieval.chunk_size": int,
    "retrieval.chunk_overlap": int,
    "retrieval.max_context_chars": int,
    "retrieval.rerank_enabled": bool,
    "privacy.telemetry_enabled": bool,
    "privacy.external_apis_enabled": bool,
    "appearance.theme": str,
    "app.first_run_completed": bool,
}

_LIMITS: dict[str, tuple[int, int]] = {
    "retrieval.top_k": (1, 50),
    "retrieval.similarity_threshold": (0, 10000),
    "retrieval.chunk_size": (200, 8000),
    "retrieval.chunk_overlap": (0, 4000),
    "retrieval.max_context_chars": (500, 60000),
    "ai.temperature": (0, 200),
    "ai.max_tokens": (64, 8192),
    "ai.context_size": (256, 131072),
}


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, dotted))
        else:
            out[dotted] = value
    return out


def _nest(flat: dict[str, Any]) -> dict[str, Any]:
    nested: dict[str, Any] = {}
    for dotted, value in flat.items():
        parts = dotted.split(".")
        cursor = nested
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    return nested


class SettingsService:
    """Read/write persisted application settings.

    ``get_effective`` merges persisted values over compiled defaults; the LLM
    registry and other services consult it for runtime behavior.
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

    def get_effective(self) -> dict[str, Any]:
        flat: dict[str, Any] = {}
        with self.session_factory() as session:
            rows = session.query(AppSetting).all()
            for row in rows:
                try:
                    flat[row.key] = json.loads(row.value_json)
                except json.JSONDecodeError:
                    flat[row.key] = row.value_json
        merged = dict(_flatten(DEFAULTS))
        merged.update(flat)
        return _nest(merged)

    def get_section(self, section: str) -> dict[str, Any]:
        return self.get_effective().get(section, {})

    def put(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Validate and persist a partial settings update.

        ``updates`` may be nested (e.g. ``{"ai": {"temperature": 0.5}}``).
        Raises ``ValidationFailed`` on unknown keys or out-of-range values.
        """
        if not isinstance(updates, dict):
            raise ValidationFailed("Settings must be a JSON object.")
        flat = _flatten(updates)
        if not flat:
            raise ValidationFailed("No settings provided.")
        for key in flat:
            if key not in _KNOWN_KEYS:
                raise ValidationFailed(f"Unknown setting: {key}")
            expected = _KNOWN_KEYS[key]
            value = flat[key]
            if isinstance(value, str) and expected is not float:
                try:
                    value = expected(value)
                except (TypeError, ValueError):
                    pass
            if not isinstance(value, expected):
                raise ValidationFailed(f"Setting '{key}' must be {expected.__name__}.")
            if key in _LIMITS:
                lo, hi = _LIMITS[key]
                if not lo <= int(value) <= hi:
                    raise ValidationFailed(f"Setting '{key}' is out of range ({lo}–{hi}).")
            if key == "retrieval.chunk_overlap" and int(value) >= int(
                flat.get("retrieval.chunk_size", DEFAULTS["retrieval"]["chunk_size"])
            ):
                raise ValidationFailed("chunk_overlap must be smaller than chunk_size.")

        with self.session_factory.begin() as session:
            for key, value in flat.items():
                row = session.get(AppSetting, key)
                if row is None:
                    row = AppSetting(key=key, value_json="")
                    session.add(row)
                row.value_json = json.dumps(value)

        # Changing the embedding model/dim requires a full re-index.
        changed = set(flat) & {"embeddings.provider", "embeddings.model", "embeddings.dim"}
        if changed:
            with self.session_factory.begin() as session:
                row = session.get(AppSetting, "embeddings.rebuild_required")
                if row is None:
                    row = AppSetting(key="embeddings.rebuild_required", value_json="")
                    session.add(row)
                row.value_json = json.dumps(True)

        return self.get_effective()