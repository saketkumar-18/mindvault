from __future__ import annotations

import re
from dataclasses import dataclass

from mindvault.parsers.base import ParsedDocument

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


@dataclass(slots=True)
class ChunkSpec:
    size: int = 900
    overlap: int = 120
    separators: tuple[str, ...] = ("\n\n", "\n", ". ", " ")


@dataclass(slots=True)
class Chunk:
    text: str
    ordinal: int
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None
    start_char: int = 0
    end_char: int = 0


class TextChunker:
    """Character-level chunker with overlap.

    - Split decisions prefer the configured separators to keep paragraphs intact.
    - Markdown headings inside page text become chunk ``section`` metadata.
    - Page numbers are tracked per chunk for exact citations.
    """

    def __init__(self, spec: ChunkSpec) -> None:
        if spec.overlap >= spec.size:
            raise ValueError("overlap must be smaller than size")
        self.spec = spec

    def split_text(self, text: str) -> list[tuple[int, str]]:
        """Split text into ``(start_offset, segment)`` pieces."""
        spec = self.spec
        pieces: list[tuple[int, str]] = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + spec.size, length)
            if end < length:
                best: int | None = None
                for sep in spec.separators:
                    idx = text.rfind(sep, start, end)
                    if idx > start:
                        candidate = idx + len(sep)
                        if best is None or candidate > best:
                            best = candidate
                if best is not None:
                    end = best
            piece = text[start:end]
            if piece:
                pieces.append((start, piece))
            start = end
        return pieces

    @staticmethod
    def _heading_of(line: str) -> str | None:
        match = _HEADING_RE.match(line.strip())
        if match:
            return match.group(2).strip()
        return None

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        spec = self.spec
        chunks: list[Chunk] = []
        ordinal = 0

        current_section: str | None = None

        for page in document.pages:
            page_text = page.text or ""
            lines = page_text.splitlines()
            global_line_offset = 0
            for line in lines:
                heading = self._heading_of(line)
                if heading is not None:
                    # Flush any pending chunk when a new section starts.
                    if chunks and chunks[-1].text:
                        chunks[-1].page_end = page.number
                    current_section = heading
                    global_line_offset += len(line) + 1
                    continue

                segment = line.strip()
                if not segment:
                    global_line_offset += len(line) + 1
                    continue

                # Append this line to the last chunk, splitting when over budget.
                if chunks and len(chunks[-1].text) + len(segment) + 1 <= spec.size:
                    chunks[-1].text += "\n" + segment if chunks[-1].text else segment
                    chunks[-1].page_end = page.number
                else:
                    if chunks and chunks[-1].text:
                        chunks[-1].page_end = page.number
                    chunks.append(
                        Chunk(
                            text=segment,
                            ordinal=ordinal,
                            page_start=page.number,
                            page_end=page.number,
                            section=current_section,
                            start_char=global_line_offset,
                            end_char=global_line_offset + len(segment),
                        )
                    )
                    ordinal += 1
                global_line_offset += len(line) + 1

            if chunks:
                chunks[-1].page_end = page.number

        # Apply overlap: prepend the tail of the previous chunk.
        if spec.overlap > 0:
            result: list[Chunk] = []
            prev_tail = ""
            for chunk in chunks:
                if prev_tail:
                    chunk.text = prev_tail + "\n" + chunk.text
                result.append(chunk)
                if len(chunk.text) > spec.overlap:
                    prev_tail = chunk.text[-spec.overlap:]
                else:
                    prev_tail = chunk.text
            chunks = result

        return chunks


def chunk_document(document: ParsedDocument, spec: ChunkSpec) -> list[Chunk]:
    return TextChunker(spec).chunk(document)
