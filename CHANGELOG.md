# Changelog

All notable changes to MindVault are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] — 2026-08-22

### Added

- **Document upload & indexing** — drag & drop, browse, multiple files, progress,
  duplicate detection (SHA-256), retry, re-index, delete.
- **Supported formats** — PDF, DOCX, TXT, Markdown, CSV, JSON.
- **Knowledge bases** — create, rename, delete, add/remove documents.
- **Semantic search** — local embeddings (hash fallback or sentence-transformers)
  with knowledge-base, document, file-type and score filters.
- **RAG chat** — streaming responses, source citations with filename + page/section,
  conversation history, regeneration, stop generation, copy.
- **Anti-hallucination** — hardened system prompt, untrusted-data guard,
  insufficient-evidence detection, source validation.
- **Study mode** — summaries, flashcards, MCQs, short-answer questions, interview
  questions, concepts, revision notes — all generated from local documents.
- **Document comparison** — select 2–5 documents and generate similarities,
  differences, missing concepts, and an overall comparison summary.
- **Resume Compatibility Analysis** — compare a resume against a job description
  (skills found, matching/missing skills, experience alignment, suggestions,
  informational ATS-style analysis — explicitly not an official ATS score).
- **Document viewer** — click any indexed document to browse its chunks with
  page/section metadata and paging.
- **First-run wizard** — guided 6-step onboarding (storage → system check →
  model selection → model test → first upload → first question) shown until setup
  is complete.
- **Settings** — AI, embeddings, retrieval, privacy, appearance, model management,
  data export, danger zone.
- **Model management** — detect Ollama models, test model, recommended models.
- **System info** — OS, CPU, RAM, GPU detection, storage usage, model status.
- **Health checks** — `/health`, `/liveness`, `/readiness`.
- **Data export** — conversations JSON, knowledge bases JSON, all-in-one ZIP.
- **First-run wizard** — guided setup (storage, system check, model, test, upload,
  question).
- **Privacy by default** — no analytics, no telemetry, no external APIs, local-only
  operation.
- **Provider architecture** — swappable LLM, embedding, vector store, and document
  parser interfaces.
- **LLM providers** — Ollama (primary), llama.cpp (secondary), Mock (test/dev).
- **Embedding providers** — sentence-transformers (when `mindvault[ml]` installed),
  hash (deterministic fallback, no dependencies).
- **Vector stores** — NumPy (default, always works), FAISS (when `mindvault[ml]`
  installed).
- **Docker** — multi-stage production image, Docker Compose with Ollama sidecar.
- **CI** — GitHub Actions (backend lint, typecheck, tests; frontend tests, build;
  Docker build; dependency security audit).
- **Dependabot** — weekly dependency updates.
- **E2E tests** — Playwright workflow test (upload → index → chat → citations → delete).
- **RAG evaluation** — labeled dataset with retrieval relevance regression check.
- **Security** — path traversal protection, file validation, prompt injection defense,
  SQLAlchemy parameterized queries, React escaping.

### Architectural

- Clean separation into `parsers/`, `embeddings/`, `vectorstore/`, `llm/`, `rag/`,
  `services/`, `api/`, `domain/`, `security/`, `jobs/` modules.
- All providers are Protocols — new implementations can be added without modifying
  existing code.
- Background indexing via thread pool executor with cancellation support.
- SQLite with Alembic migrations, WAL mode, foreign keys.
- Frontend: React 19, TypeScript strict, Vite 6, Tailwind CSS 4, TanStack Query,
  React Router 7, Lucide icons.