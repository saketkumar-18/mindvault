"""MindVault desktop launcher entry point.

Bundled by PyInstaller into a native executable. It:
  1. resolves the data directory (default ~/.mindvault),
  2. starts the FastAPI backend (which serves the bundled frontend),
  3. opens the default browser at the local URL.

The frontend build is embedded into the bundle via the ``MV_WEB_DIST``
environment variable set by the PyInstaller build (see desktop/mindvault.spec).
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn


def _resource_path(name: str) -> Path:
    """Resolve a bundled resource in a PyInstaller one-folder/one-file build."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def _resolve_web_dist() -> str | None:
    env = os.environ.get("MV_WEB_DIST")
    if env:
        return env
    # PyInstaller bundles frontend/dist next to the spec resources.
    candidates = [_resource_path("frontend/dist"), _resource_path("dist")]
    for candidate in candidates:
        if candidate.is_dir():
            return str(candidate)
    return None


def _open_browser(url: str) -> None:
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> None:
    host = os.environ.get("MV_HOST", "127.0.0.1")
    port = int(os.environ.get("MV_PORT", "8000"))
    web_dist = _resolve_web_dist()
    if web_dist:
        os.environ["MV_WEB_DIST"] = web_dist

    from mindvault.api.app import create_app

    app = create_app()
    url = f"http://{host}:{port}"
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()
    print(f"MindVault running at {url} — closing this window stops the app.")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
