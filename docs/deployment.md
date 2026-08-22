# Deployment Guide

MindVault can be deployed in several ways. All are fully local.

## Docker (recommended for self-hosting)

### Prerequisites

- Docker Engine with Compose v2.
- 4 GB+ RAM for a small model.

### Start

```bash
docker compose up --build -d
```

- MindVault web UI: http://localhost:8000
- Ollama: http://localhost:11434

The compose file defines a `mindvault` service (built from the multi-stage
Dockerfile) and an `ollama` sidecar. Data lives in named volumes
(`mv-data`, `ollama-models`).

### Install a model into the sidecar

```bash
docker exec -it mindvault-ollama-1 ollama pull llama3.2:3b
```

Then in MindVault *Settings → AI* choose the model and **Test Model**.

### GPU (NVIDIA)

Uncomment the `deploy.resources.reservations.devices` block in
`docker-compose.yml` for the `ollama` service, then `docker compose up -d`.

### Updating

```bash
git pull
docker compose up --build -d
```

Your data persists in the volumes.

## Native installation (Windows / Linux / macOS)

1. Install a model runtime (Ollama recommended) and pull a model.
2. Install MindVault and run it.
3. Data is stored under `~/.mindvault` by default.

## Running from source

See [development.md](development.md) — but in short:

```bash
pip install -e "backend[ml]"   # optional ml extra for better embeddings
python -m mindvault            # binds 127.0.0.1:8000 by default
```

### Exposing beyond localhost

MindVault binds to `127.0.0.1` by default and has no built-in authentication.
To expose it on a LAN or the internet:

- Set `MV_HOST=0.0.0.0` **only** behind a reverse proxy (Caddy / nginx / Traefik).
- Enable TLS.
- Add basic auth or a VPN at the proxy layer.
- Restrict CORS origins via `MV_CORS_ORIGINS`.

This is a local-first tool; exposing it is the operator's responsibility.

## Configuration reference

| Variable | Default | Purpose |
|---|---|---|
| `MV_HOME` | `~/.mindvault` | Root data directory |
| `MV_DATABASE_URL` | `sqlite:///{MV_HOME}/mindvault.db` | SQLite location |
| `MV_DOCUMENTS_DIR` | `{MV_HOME}/documents` | Uploaded file storage |
| `MV_INDEX_DIR` | `{MV_HOME}/index` | Vector index files |
| `MV_HOST` | `127.0.0.1` | Bind address |
| `MV_PORT` | `8000` | Bind port |
| `MV_CORS_ORIGINS` | localhost:5173 origins | Allowed browser origins |
| `MV_MAX_UPLOAD_BYTES` | `104857600` | Upload cap |
| `MV_ALLOWED_EXTENSIONS` | `pdf,docx,txt,md,csv,json` | Allowed file types |
| `MV_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama endpoint |
| `MV_EMBEDDING_PROVIDER` | `hash` | `sentence-transformers` or `hash` |
| `MV_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model (ST) |
| `MV_EMBEDDING_DIM` | `384` | Embedding dimension |
| `MV_LLM_PROVIDER` | `auto` | `auto`, `ollama`, `llama_cpp`, `mock` |
| `MV_WEB_DIST` | unset | Path to built frontend to serve (production) |
| `MV_DEBUG` | `0` | Verbose logging |

## Backups

See [backup.md](backup.md).

## Troubleshooting

- **Model unavailable** — confirm Ollama is running (`curl http://127.0.0.1:11434/api/tags`),
  a model is pulled, and the correct model is selected in Settings.
- **Poor search quality** — install `mindvault[ml]` and set
  `MV_EMBEDDING_PROVIDER=sentence-transformers`, then rebuild the index.
- **Port already in use** — use `MV_PORT` or `--port`.
- **"Index rebuild required"** — you changed the embedding model; re-index
  documents from Settings.
