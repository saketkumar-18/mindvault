# MindVault — Backend

Local-first backend for MindVault, the private AI knowledge assistant.

## Quick start (development)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn mindvault.api.app:create_app --factory --reload
```

Optional ML extras (real semantic embeddings + FAISS):

```bash
pip install -e ".[ml]"
```

See the [root README](../README.md) and [`docs/development.md`](../docs/development.md) for full instructions.

## Running the server

```bash
python -m mindvault            # default: http://127.0.0.1:8000
python -m mindvault --port 9000
```

## Tests & checks

```bash
ruff check mindvault tests
mypy mindvault/domain mindvault/parsers mindvault/embeddings mindvault/vectorstore mindvault/llm mindvault/security mindvault/jobs --follow-imports=skip
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests/eval
```

## Layout

```
mindvault/
├── api/          # FastAPI app factory + REST routers
├── db/           # SQLAlchemy models, session, Alembic migrations
├── domain/       # chunker, shared logic
├── embeddings/   # EmbeddingProvider implementations
├── llm/          # LLMProvider implementations (ollama, llama.cpp, mock)
├── parsers/      # DocumentParser implementations (pdf, docx, txt, md, csv, json)
├── rag/          # retrieval-augmented generation pipeline
├── security/     # file validation, path safety, streaming hashing
├── services/     # application services (documents, chat, search, study, …)
├── vectorstore/  # VectorStore implementations (FAISS, NumPy fallback)
└── jobs/         # in-process background job registry
```

Privacy: MindVault makes no external requests by default. Everything runs
against local providers.
