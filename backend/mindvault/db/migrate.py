"""Programmatic Alembic invocation.

Kept in a single module so migrations run both from the CLI and from the
application startup path without shelling out.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def alembic_config(database_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def run_migrations(database_url: str, rev: str = "head") -> None:
    command.upgrade(alembic_config(database_url), rev)
