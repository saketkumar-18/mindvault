from __future__ import annotations

import argparse

import uvicorn

from mindvault import __version__
from mindvault.config import Settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mindvault", description="MindVault local-first knowledge assistant")
    parser.add_argument("--host", default=None, help="Bind host (default: MV_HOST or 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (default: MV_PORT or 8000)")
    parser.add_argument("--version", action="version", version=f"mindvault {__version__}")
    args = parser.parse_args(argv)

    settings = Settings()
    host = args.host or settings.host
    port = args.port or settings.port

    from mindvault.api.app import create_app

    app = create_app(settings)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
