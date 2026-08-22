from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mindvault.errors import ValidationFailed


@dataclass(slots=True)
class Page:
    number: int | None
    text: str
    headings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedDocument:
    pages: list[Page]
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentParser(ABC):
    """Base class for all document parsers.

    New formats (PPTX, XLSX, images, code) plug in here without touching the
    rest of the application.
    """

    extensions: frozenset[str]

    @abstractmethod
    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        """Extract text from ``source``.

        Implementations must be defensive against malformed input and raise
        ``ValidationFailed`` for unreadable content.
        """

    def validate(self, source: Path) -> None:
        if not source.is_file():
            raise ValidationFailed("Source file does not exist.")
        if source.stat().st_size == 0:
            raise ValidationFailed("File is empty.")
