# MindVault PyInstaller spec (Windows / Linux / macOS).
#
# Build:
#   cd desktop
#   pip install pyinstaller
#   pyinstaller mindvault.spec
#
# Output: desktop/dist/MindVault/ (one-folder bundle) with MindVault.exe
# (or MindVault binary on Linux/macOS).
#
# The frontend must be built first: `cd ../frontend && npm run build`.

import os
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # the repository root (desktop/..)

FRONTEND_DIST = ROOT / "frontend" / "dist"
if not FRONTEND_DIST.is_dir():
    raise SystemExit("frontend/dist not found. Build the frontend first: cd frontend && npm run build")


block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=["../backend"],
    binaries=[],
    datas=[
        (str(FRONTEND_DIST), "frontend/dist"),
        # Bundle Alembic migration scripts (non-Python assets).
        (str(ROOT / "backend" / "mindvault" / "migrations"), "mindvault/migrations"),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "alembic.runtime.migration",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "pandas", "scipy", "torch"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MindVault",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MindVault",
)
