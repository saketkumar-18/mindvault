from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mindvault.errors import ValidationFailed
from mindvault.parsers.base import DocumentParser, Page, ParsedDocument


def _flatten(
    value: Any,
    prefix: str = "",
    out: list[str] | None = None,
    depth: int = 0,
    max_depth: int = 6,
) -> list[str]:
    out = out if out is not None else []
    if depth > max_depth:
        out.append(f"{prefix}: <nested>")
        return out
    if isinstance(value, dict):
        for key, item in value.items():
            _flatten(item, f"{prefix}.{key}" if prefix else str(key), out, depth + 1, max_depth)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _flatten(item, f"{prefix}[{i}]" if prefix else f"[{i}]", out, depth + 1, max_depth)
    else:
        out.append(f"{prefix}: {value}")
    return out


class JsonParser(DocumentParser):
    """JSON files flattened into readable ``key: value`` lines."""

    extensions = frozenset({"json"})

    def __init__(self, max_entries: int = 20_000) -> None:
        self.max_entries = max_entries

    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        self.validate(source)
        try:
            data = json.loads(source.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            raise ValidationFailed(f"Malformed JSON file: {exc}") from exc

        lines = _flatten(data)
        if len(lines) > self.max_entries:
            lines = lines[: self.max_entries] + [f"... truncated at {self.max_entries} entries ..."]
        body = "\n".join(lines)
        return ParsedDocument(pages=[Page(number=None, text=body)], metadata={"parser": "json"})
