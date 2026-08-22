from __future__ import annotations

from pathlib import Path

from mindvault.errors import ValidationFailed
from mindvault.parsers.base import DocumentParser, Page, ParsedDocument


class DocxParser(DocumentParser):
    """DOCX parsing via python-docx. Heading styles become sections."""

    extensions = frozenset({"docx"})

    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        self.validate(source)
        try:
            import docx  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover
            raise ValidationFailed("DOCX support is not installed. Run: pip install mindvault[ml]") from exc

        try:
            document = docx.Document(str(source))
        except Exception as exc:
            raise ValidationFailed(f"Could not read DOCX file: {exc}") from exc

        body_lines: list[str] = []
        headings: list[str] = []
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            style = (paragraph.style.name or "").lower() if paragraph.style is not None else ""
            if style.startswith("heading"):
                headings.append(text)
            else:
                body_lines.append(text)

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    body_lines.append(" | ".join(cells))

        if not body_lines:
            raise ValidationFailed("DOCX contains no extractable text.")

        body = "\n".join(body_lines)
        return ParsedDocument(
            pages=[Page(number=1, text=body, headings=list(headings))],
            metadata={"parser": "docx"},
        )
