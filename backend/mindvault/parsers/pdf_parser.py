from __future__ import annotations

from pathlib import Path

from mindvault.errors import ValidationFailed
from mindvault.parsers.base import DocumentParser, Page, ParsedDocument


class PdfParser(DocumentParser):
    """PDF parsing using pypdf. Page numbers are preserved for citations."""

    extensions = frozenset({"pdf"})

    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        self.validate(source)
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise ValidationFailed("PDF support is not installed. Run: pip install mindvault[ml]") from exc

        try:
            reader = PdfReader(str(source))
        except Exception as exc:
            raise ValidationFailed(f"Could not read PDF file: {exc}") from exc

        pages: list[Page] = []
        for index, page in enumerate(reader.pages, start=1):
            if max_pages and len(pages) >= max_pages:
                break
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # malformed page content
                raise ValidationFailed(f"Could not extract text from page {index}: {exc}") from exc
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            if text.strip():
                pages.append(Page(number=index, text=text))

        if not pages:
            raise ValidationFailed("PDF contains no extractable text (scanned image PDFs are not yet supported).")

        metadata: dict[str, object] = {"parser": "pdf", "page_count": len(pages)}
        try:
            if reader.metadata:
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title
                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author
        except Exception:
            pass
        return ParsedDocument(pages=pages, metadata=metadata)
