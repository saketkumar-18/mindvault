from __future__ import annotations

from fastapi import Request

from mindvault.services.container import ServiceContainer
from mindvault.services.container import get_container as _get_container


def get_container(_request: Request) -> ServiceContainer:
    return _get_container()