from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all MindVault ORM models."""


def utcnow() -> datetime:
    return datetime.now(UTC)
