# Desktop packaging

MindVault can be distributed as a native desktop application in two ways.

## Option 1 — PyInstaller bundle (recommended for v1, works today)

Packages the backend + built frontend into a single native executable. On
startup it launches the local server, opens your browser, and serves the
app. Requires no Rust toolchain.

### Build

```bash
# 1. Build the frontend
cd frontend && npm run build && cd ..

# 2. Install PyInstaller in the backend venv
backend/.venv/Scripts/python -m pip install pyinstaller   # Windows
backend/.venv/bin/python -m pip install pyinstaller        # Linux/macOS

# 3. Build the bundle
cd desktop
backend/../backend/.venv/Scripts/python -m PyInstaller --noconfirm mindvault.spec
# or use the wrapper scripts:
scripts/build_desktop.ps1        # Windows
scripts/build_desktop.sh         # Linux/macOS
```

### Output

- Windows: `desktop/dist/MindVault/MindVault.exe`
- Linux/macOS: `desktop/dist/MindVault/MindVault` (executable)

The bundle embeds `frontend/dist` and the full backend. On first run it
creates `~/.mindvault` for data.

### Notes

- The launcher (`desktop/launcher.py`) sets `MV_WEB_DIST` automatically and
  opens the default browser.
- Model weights are **not** bundled — users install Ollama/llama.cpp
  separately, exactly as with the web app.
- `MV_HOME` can be overridden with an environment variable.

## Option 2 — Tauri (webview shell, smaller binary)

A Tauri shell wraps the built frontend in a native webview window. Tauri's
frontend is the same React app; it talks to the local backend over
`http://127.0.0.1:8000`.

### Prerequisites

- [Rust toolchain](https://rustup.rs) (stable).
- Tauri CLI: `npm install` in `desktop/`.

### Build

```bash
cd desktop
npm install
npm run tauri build   # requires the backend running separately during dev
```

`desktop/tauri.conf.json` is preconfigured (window size, CSP, bundle targets
deb/msi/appimage). Tauri bundling of the Python backend is a v2/v3 goal —
today Tauri ships the UI shell, and the backend still runs as a local service.

## Which to choose

- **v1 (now):** PyInstaller bundle — one click, no extra toolchains, verified.
- **Future:** Tauri for a lighter, native window and installer UX; the config
  is committed and ready.
