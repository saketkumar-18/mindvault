from __future__ import annotations

from pathlib import Path

from mindvault.parsers.base import DocumentParser, Page, ParsedDocument


class TextParser(DocumentParser):
    """Plain text files. Page breaks are honored via form feeds."""

    extensions = frozenset({"txt"})

    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        self.validate(source)
        raw = source.read_text(encoding="utf-8", errors="replace")
        pages: list[Page] = []
        for index, block in enumerate(raw.split("\f"), start=1):
            block = block.strip()
            if not block:
                continue
            pages.append(Page(number=index, text=block))
            if max_pages and len(pages) >= max_pages:
                break
        if not pages:
            pages = [Page(number=None, text=raw.strip())]
        return ParsedDocument(pages=pages, metadata={"parser": "txt"})


class MarkdownParser(DocumentParser):
    """Markdown files, preserving heading structure as chunk sections."""

    extensions = frozenset({"md", "markdown"})

    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        self.validate(source)
        raw = source.read_text(encoding="utf-8", errors="replace")
        pages: list[Page] = []
        headings: list[str] = []
        for index, block in enumerate(raw.split("\f"), start=1):
            lines = block.splitlines()
            body_lines: list[str] = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#") and stripped.lstrip("#").strip():
                    headings.append(stripped)
                else:
                    body_lines.append(line)
            block = "\n".join(body_lines).strip()
            if not block:
                continue
            pages.append(Page(number=index, text=block, headings=list(headings)))
            headings.clear()
            if max_pages and len(pages) >= max_pages:
                break
        if not pages:
            pages = [Page(number=None, text=raw.strip())]
        return ParsedDocument(pages=pages, metadata={"parser": "markdown"})
