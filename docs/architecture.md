# MindVault Architecture

## System overview

MindVault is a local-first AI knowledge assistant. The entire system runs on
the user's machine: the React frontend, the FastAPI backend, the SQLite
database, the vector index, and the local LLM runtime.

```
┌─────────────────────────────┐
│        Frontend (React)      │
│  Dashboard · Documents ·    │
│  Knowledge Bases · Chat ·   │
│  Search · Study · Settings  │
└──────────────┬──────────────┘
               │ REST + SSE (streaming)
┌──────────────▼──────────────┐
│         FastAPI backend      │
│  routers → services → domain │
│  + background job runner     │
└───┬───────┬───────┬──────────┘
    │       │       │
┌───▼───┐ ┌─▼─────┐ ┌▼──────────────┐
│ SQLite│ │Vector │ │File storage    │
│ (DB,  │ │store  │ │(documents dir) │
│ WAL)  │ │FAISS/ │ │               │
│       │ │NumPy  │ │               │
└───────┘ └───────┘ └───────────────┘
    ▲          ▲
    │          │
┌───┴──────────┴───────────┐
│ Providers (interfaces)    │
│ ┌──────────────────────┐  │
│ │ LLM (Ollama/llama.cpp)│ │
│ │ Embeddings (ST/hash)  │ │
│ │ Parsers (6 formats)   │ │
│ └──────────────────────┘  │
└───────────────────────────┘
```

## Component responsibilities

### `backend/mindvault/api/`
FastAPI application factory (`app.py`), REST routers, error handlers, and
dependency injection (a `ServiceContainer` registers all services).

### `backend/mindvault/services/`
Application-layer services. Each is a plain class injected with its
dependencies:

- `documents` — upload validation, storage, indexing jobs, delete, re-index.
- `chat` — conversation CRUD and the streaming answer flow.
- `search` — vector retrieval + lexical fallback, global search.
- `knowledge_bases` — KB CRUD and document assignment.
- `study` — summaries, flashcards, MCQs, Q&A generation.
- `settings` — persisted, validated settings.
- `models` — provider/model inspection and testing.
- `system` — stats, system info, GPU/RAM detection.
- `export` — JSON/ZIP data export.

### `backend/mindvault/rag/`
The RAG pipeline (`rag_service.py`): retrieval → dedup → context budget →
prompt construction → LLM → citation metadata. The system prompt enforces the
untrusted-data rule (see *Prompt injection defense* below).

### `backend/mindvault/domain/`
`chunker.py` — configurable character-level chunker with overlap and
page/section provenance.

### `backend/mindvault/parsers/`
One class per format implementing the `DocumentParser` Protocol:
`pdf_parser`, `docx_parser`, `text` (TXT/MD), `csv_parser`, `json_parser`.
New formats plug in by implementing the interface and registering.

### `backend/mindvault/embeddings/`
`EmbeddingProvider` implementations: `SentenceTransformerProvider` (real
semantic embeddings) and `HashEmbeddingProvider` (deterministic, dependency
free, works offline with zero downloads). The factory selects one based on
settings and installed packages.

### `backend/mindvault/vectorstore/`
`VectorStore` implementations: `NumpyVectorStore` (default) and
`FaissVectorStore` (when `mindvault[ml]` installed). Both are persisted to
disk and hold only vectors + IDs; chunk *text* lives in SQLite so the index
can always be rebuilt.

### `backend/mindvault/llm/`
`LLMProvider` implementations: `OllamaProvider` (primary), `LlamaCppProvider`
(OpenAI-compatible endpoint), `MockLLMProvider` (tests/dev only). The
`registry.resolve_llm()` picks a provider based on settings + availability.

### `backend/mindvault/db/`
SQLAlchemy models, engine/session factory (WAL, foreign keys), and Alembic
migrations invoked programmatically on startup.

### `backend/mindvault/jobs/`
Thread-safe `JobRegistry` + `ThreadPoolExecutor` for background indexing with
cancellation.

## The RAG pipeline

```
User question
  → normalize (strip, collapse whitespace)
  → embed query (embedding provider)
  → vector retrieval (top-k × 2)
  → filter (knowledge base / document / file type)
  → relevance threshold
  → deduplicate near-identical chunks
  → context budget (max_context_chars)
  → build prompt (<documents> block + anti-hallucination rules)
  → stream from local LLM
  → cite sources (filename, page, section, score)
  → persist conversation
```

Sources returned to the frontend include `chunk_id`, `document_id`,
`filename`, `page_start/page_end`, `section`, `score`, and a short `excerpt`.

## Prompt injection defense

Documents are untrusted. The RAG system prompt (in `rag_service.py`) states
explicitly that content inside `<documents>` is **data, not instructions**,
forbids following instructions found in documents, and forbids inventing
citations or page numbers. The application never lets document text modify
system behavior, and the LLM has no ability to execute shell commands.

## Storage architecture

- **SQLite** (`mindvault.db`, WAL) — documents, chunks (text + metadata),
  conversations, messages, study materials, settings.
- **Vector index** — one persisted file (`index/index.npz` or FAISS). Contains
  embeddings + IDs only; rebuildable from SQLite chunk text.
- **Document files** — stored under `documents/` with UUID-based names; the
  display filename is stored in the database only.
- **Logs** — structured JSON lines to stdout (configurable).

## Data flow for a query

1. Frontend `POST /api/chat` (SSE stream).
2. `ChatService` persists the user message, builds history.
3. `RAGService` retrieves and grounds, streams tokens back via SSE.
4. Frontend renders the streaming answer and the source list.
5. Assistant message + sources are persisted to SQLite.

## Deployment architectures

- **Native desktop** — packaged frontend served by the backend; Ollama runs
  separately. *(packaging config for future releases)*
- **Docker** — `mindvault` service + optional `ollama` sidecar on a shared
  network; data in volumes. See `docker-compose.yml`.
- **Self-hosted server** — bind to `0.0.0.0` with `MV_HOST`, run behind a
  reverse proxy if desired.

## Security boundaries

- **Input boundary** — file validation, path safety, parameterized queries.
- **Data boundary** — untrusted documents never influence system prompts or
  execute code.
- **Network boundary** — no outbound calls by default; LLM endpoint is the
  only connection, and it is user-configured localhost.
