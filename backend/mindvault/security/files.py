from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from mindvault.errors import PayloadTooLarge, SecurityViolation, UnsupportedFileType, ValidationFailed

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_RESERVED_WINDOWS = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
MAX_FILENAME_LEN = 180


def sanitize_display_name(name: str) -> str:
    """Normalize an untrusted filename for display and storage naming.

    Strips directory components, control characters and risky patterns.
    """
    if not name:
        raise ValidationFailed("Filename is required.")
    # Strip any path components (handles both separators).
    name = name.replace("\\", "/")
    name = Path(name).name
    name = unicodedata.normalize("NFC", name)
    name = _CONTROL_RE.sub("", name)
    name = name.strip(" .")
    # Collapse repeated dots to avoid traversal-ish names.
    while ".." in name:
        name = name.replace("..", ".")
    if not name:
        raise ValidationFailed("Filename is invalid.")
    stem = name.rsplit(".", 1)[0] if "." in name else name
    if stem.upper() in _RESERVED_WINDOWS:
        name = "_" + name
    if len(name) > MAX_FILENAME_LEN:
        stem, dot, ext = name.rpartition(".")
        keep = MAX_FILENAME_LEN - (1 + len(ext))
        name = stem[:keep] + dot + ext
    return name


def extension_of(name: str) -> str:
    _, _, ext = name.rpartition(".")
    return ext.lower()


def validate_upload(
    original_name: str,
    size_bytes: int,
    *,
    max_size: int,
    allowed_extensions: set[str],
) -> tuple[str, str]:
    """Validate an incoming upload.

    Returns ``(sanitized_display_name, extension)``. Raises AppError subclasses
    with user-safe messages.
    """
    display = sanitize_display_name(original_name)
    ext = extension_of(display)
    if not ext:
        raise UnsupportedFileType("Files must have a valid extension.")
    if ext not in allowed_extensions:
        raise UnsupportedFileType(
            f"File type '.{ext}' is not supported. Allowed: {', '.join(sorted(allowed_extensions))}."
        )
    if size_bytes <= 0:
        raise ValidationFailed("File is empty.")
    if size_bytes > max_size:
        raise PayloadTooLarge(
            f"File is too large. Maximum allowed size is {max_size // (1024 * 1024)} MB."
        )
    return display, ext


def resolve_under(base: Path, *parts: str) -> Path:
    """Resolve a path and guarantee it stays within ``base``.

    Prevents path traversal even if a caller mixes in untrusted segments.
    """
    base_resolved = base.resolve()
    target = base_resolved.joinpath(*parts).resolve()
    if not target.is_relative_to(base_resolved):
        raise SecurityViolation("Refusing to resolve a path outside the allowed directory.")
    return target
