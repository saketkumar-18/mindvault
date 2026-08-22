# Privacy

MindVault is designed so that **your data never has to leave your machine**.

## By default

- **Documents are stored locally** — under `~/.mindvault/documents`.
- **Conversations are stored locally** — in the SQLite database on your disk.
- **AI inference is local** — the model runs on your machine via Ollama or
  llama.cpp. MindVault never sends your question or documents to a cloud API.
- **Embeddings are local** — computed on your machine (hash embeddings need
  nothing; sentence-transformers downloads a model once, then runs offline).
- **No analytics** — no telemetry, no tracking pixels, no crash reporters.
- **No account** — nothing to sign up for, nothing stored remotely.
- **No external AI APIs** — disabled by default and never required.

## Offline mode

After the required local models are installed, MindVault works fully offline:

- Upload documents, index, search, chat, and study — all offline.
- The UI shows **Local Mode** and **Local-only operation** status.
- If the model runtime is unreachable, MindVault tells you the model is
  unavailable and never silently substitutes a cloud service.

## What the application does on the network

- **Nothing by default.** The only connection MindVault makes is to your local
  model runtime (Ollama at `http://127.0.0.1:11434` by default).
- The backend binds to `127.0.0.1` by default, so other devices can't reach it.

## If you want to use cloud services

Any future cloud integration (sync, remote inference, collaboration) will be:

- **opt-in** (disabled by default),
- **clearly disclosed** in the UI,
- **never required** for core functionality.

Nothing in MindVault v1 makes outbound calls unless you configure a
non-localhost model endpoint yourself.

## Verifying privacy

- Inspect the code — the backend makes HTTP requests only to the configured
  `MV_OLLAMA_URL` / llama.cpp endpoint (see `backend/mindvault/llm/`).
- Watch your network — with default settings you'll see localhost traffic
  only.
- Read the [security threat model](security-threat-model.md).
