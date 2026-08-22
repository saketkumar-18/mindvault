from __future__ import annotations

import csv
import io
from pathlib import Path

from mindvault.errors import ValidationFailed
from mindvault.parsers.base import DocumentParser, Page, ParsedDocument


class CsvParser(DocumentParser):
    """CSV files rendered as readable rows with a header line."""

    extensions = frozenset({"csv"})

    def __init__(self, max_rows: int = 50_000) -> None:
        self.max_rows = max_rows

    def parse(self, source: Path, *, max_pages: int | None = None) -> ParsedDocument:
        self.validate(source)
        try:
            data = source.read_bytes()
            text = data.decode("utf-8-sig", errors="replace")
        except OSError as exc:
            raise ValidationFailed(f"Could not read CSV file: {exc}") from exc

        lines: list[str] = []
        try:
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
        except csv.Error as exc:
            raise ValidationFailed(f"Malformed CSV file: {exc}") from exc

        if not rows:
            raise ValidationFailed("CSV file contains no rows.")

        header = rows[0]
        for index, row in enumerate(rows[1:], start=1):
            if index > self.max_rows:
                lines.append(f"... truncated at {self.max_rows} rows ...")
                break
            values = ", ".join(cell.strip() for cell in row if cell.strip())
            if not values:
                continue
            lines.append(f"Row {index}: {values}")

        body = "Columns: " + ", ".join(header) + "\n" + "\n".join(lines)
        return ParsedDocument(pages=[Page(number=None, text=body)], metadata={"parser": "csv", "rows": len(rows) - 1})
