# Development Guide

Guide for developers contributing to MindVault.

## Prerequisites

- **Python 3.11+** (3.12 recommended for all dependency wheels).
- **Node.js 20+** (22 recommended).
- Git.
- Optional: Docker (for the container workflow), Ollama or llama.cpp (for real
  local models), and `uv` (recommended Python package manager).

## Repository layout

```
mindvault/
├── backend/            # Python FastAPI backend (package: mindvault)
│   ├── mindvault/      # application code
│   ├── migrations/     # Alembic schema migrations
│   └── tests/          # unit + integration + RAG eval tests
├── frontend/           # React + TypeScript + Vite web app
├── docs/               # architecture, API, security, models, deployment
├── .github/            # CI, issue templates, PR template, dependabot
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Backend setup

### Using uv (recommended)

```bash
cd backend
uv sync --extra dev
```

### Using pip

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional ML extra for real semantic embeddings and FAISS:

```bash
pip install -e ".[ml]"
```

### Environment

```bash
cp .env.example .env
```

Set `MV_HOME` if you want data somewhere other than `~/.mindvault`. For daily
development use the deterministic providers so no model download is needed:

```bash
export MV_EMBEDDING_PROVIDER=hash   # PowerShell: $env:MV_EMBEDDING_PROVIDER="hash"
export MV_LLM_PROVIDER=mock
```

### Running the backend

```bash
uvicorn mindvault.api.app:create_app --factory --reload
# or
python -m mindvault
```

OpenAPI docs: http://127.0.0.1:8000/docs

## Frontend setup

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to :8000)
```

Production build:

```bash
npm run build      # outputs to frontend/dist
```

## Running tests

### Backend

```bash
cd backend
ruff check mindvault tests
mypy mindvault/domain mindvault/parsers mindvault/embeddings \
  mindvault/vectorstore mindvault/llm mindvault/security mindvault/jobs \
  --follow-imports=skip
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests/eval
```

Tests use `HashEmbeddingProvider` and `MockLLMProvider`, so they run **without
GPU, without internet, and without model downloads**.

### Frontend

```bash
cd frontend
npx tsc --noEmit
npm run test
npm run build
```

### End-to-end (Playwright)

```bash
# Terminal 1 — backend with mock providers + built web app
cd backend
export MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock
export MV_WEB_DIST=../frontend/dist
python -m mindvault --port 8010

# Terminal 2 — E2E
cd frontend
npx playwright install chromium
MINDVAULT_E2E_URL=http://127.0.0.1:8010 npx playwright test
```

The E2E spec covers: launch → upload → index → search → chat → citations →
delete.

## Working with a real local model (optional)

1. Install [Ollama](https://ollama.com/download) and run `ollama pull llama3.2:3b`.
2. Leave `MV_LLM_PROVIDER` unset (auto-detects Ollama) or set it to `ollama`.
3. For better embeddings, install `mindvault[ml]` and set
   `MV_EMBEDDING_PROVIDER=sentence-transformers` (downloads the model once).

## Database migrations

Migrations run automatically at startup (`mindvault/db/migrate.py`). To create
a new migration after changing `mindvault/db/models.py`:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

`script_location` is `mindvault/migrations`. Commit the generated file.

## Code style

- Python: type hints, small modules, Ruff-clean, docstrings on public APIs.
- TypeScript: strict mode (`noUncheckedIndexedAccess`), no `any`.
- Never add comments for the sake of comments.
- Keep providers swappable (interfaces in `*_service` / `base.py`).

## Privacy rules for contributors

- No analytics, telemetry, or tracking code.
- No external API calls in default paths.
- No secrets in the repository.
- Document content must not be logged.
