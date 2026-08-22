# Desktop packaging

MindVault can be distributed as a native desktop application.

## Option 1 — PyInstaller bundle (recommended, self-contained)

Packages the backend + built frontend into a single native executable. On
startup it launches the local server, opens your browser, and serves the app.
**No Rust toolchain required.**

### Build (Windows)

```powershell
scripts/build_desktop.ps1
```

### Build (Linux/macOS)

```bash
./scripts/build_desktop.sh
```

### Output

- Windows: `desktop/dist/MindVault/MindVault.exe`
- Linux/macOS: `desktop/dist/MindVault/MindVault`

This bundle is **fully self-contained** (backend + frontend). Model weights
are not bundled; users install Ollama/llama.cpp separately.

## Option 2 — Tauri native shell (verified build)

A Tauri v2 shell wraps the built frontend in a native WebView window. The
Tauri binary (`src-tauri/target/release/mindvault.exe`) is **built and
verified** on Windows; NSIS and MSI installers are produced:

```
src-tauri/target/release/bundle/nsis/MindVault_0.3.0_x64-setup.exe
src-tauri/target/release/bundle/msi/MindVault_0.3.0_x64_en-US.msi
```

### Important note about the backend

The Tauri shell ships the **frontend** and spawns the **Python backend as a
child process** on startup (`python -m mindvault`). This means:

- In **development**, run `cargo run` / `tauri dev` from a machine with the
  backend venv on PATH.
- For a **fully self-contained installer**, set `MINVAULT_BACKEND_EXE` (or
  bundle the PyInstaller exe and set `MINDVAULT_BACKEND`) so the Tauri app
  launches the packaged backend instead of requiring Python. This is the
  documented production wiring; the PyInstaller bundle (Option 1) is the
  simplest fully self-contained path today.

### Prerequisites to build Tauri yourself

- Rust toolchain (`rustup` + `stable-x86_64-pc-windows-msvc`)
- Visual Studio 2022 Build Tools with the **Desktop development with C++**
  workload (MSVC + Windows SDK)
- Node.js (for `@tauri-apps/cli` and the frontend build)

### Build

```bash
cd src-tauri
npm install
# Windows: run from a "Developer Command Prompt" or after `vcvars64.bat`
npx tauri build
```

## Which to choose

- **Fully self-contained, no toolchains:** PyInstaller bundle.
- **Native window/installer UX:** Tauri shell (frontend + spawned backend).

Both are committed and documented; the PyInstaller bundle is the simplest
path for end users today.
