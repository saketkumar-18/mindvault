from __future__ import annotations

from mindvault.errors import UnsupportedFileType
from mindvault.parsers.base import DocumentParser, ParsedDocument
from mindvault.parsers.csv_parser import CsvParser
from mindvault.parsers.docx_parser import DocxParser
from mindvault.parsers.json_parser import JsonParser
from mindvault.parsers.pdf_parser import PdfParser
from mindvault.parsers.text import MarkdownParser, TextParser

_PARSERS: tuple[DocumentParser, ...] = (
    PdfParser(),
    DocxParser(),
    TextParser(),
    MarkdownParser(),
    CsvParser(),
    JsonParser(),
)


class ParserRegistry:
    """Maps file extensions to the responsible parser."""

    def __init__(self, parsers: tuple[DocumentParser, ...] = _PARSERS) -> None:
        self._by_extension: dict[str, DocumentParser] = {}
        for parser in parsers:
            for ext in parser.extensions:
                self._by_extension[ext] = parser

    @property
    def supported_extensions(self) -> set[str]:
        return set(self._by_extension)

    def get(self, extension: str) -> DocumentParser:
        parser = self._by_extension.get(extension.lower())
        if parser is None:
            raise UnsupportedFileType(f"Unsupported file type: '.{extension}'")
        return parser

    def parse(self, source, extension: str, *, max_pages: int | None = None) -> ParsedDocument:
        return self.get(extension).parse(source, max_pages=max_pages)


registry = ParserRegistry()
