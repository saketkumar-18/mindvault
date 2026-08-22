from __future__ import annotations

import hashlib
from pathlib import Path

from mindvault.errors import PayloadTooLarge


def sha256_digest(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Streaming SHA-256 of a file without loading it into memory."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk_size)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()


def read_stream_limited(
    stream: object, max_bytes: int, chunk_size: int = 1024 * 1024
) -> tuple[bytes, int]:
    """Read a binary stream up to ``max_bytes``.

    Returns ``(data, total_read)``. The caller must decide what to do if
    ``total_read > max_bytes`` (raise PayloadTooLarge).
    """
    read = getattr(stream, "read", None)
    if not callable(read):
        raise PayloadTooLarge("Upload stream is invalid.")

    chunks: list[bytes] = []
    total = 0
    while True:
        block = read(chunk_size)
        if not block:
            break
        total += len(block)
        if total > max_bytes:
            raise PayloadTooLarge(
                f"File is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB."
            )
        chunks.append(block)
    return b"".join(chunks), total
