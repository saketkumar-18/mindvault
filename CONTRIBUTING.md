# Contributing to MindVault

Thank you for your interest in contributing! MindVault is a local-first,
privacy-focused AI knowledge assistant.

## Code of conduct

This project is governed by the [Contributor Covenant](CODE_OF_CONDUCT.md).
By participating you agree to uphold it.

## How to contribute

### Report bugs

Open an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).
Include your environment, steps to reproduce, and relevant logs (no document
contents, no secrets).

### Suggest features

Open an issue using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml).

### Submit code

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run the check suite (see below).
5. Open a pull request against `main` using the [pull request template](.github/pull_request_template.md).

## Development setup

See [README](README.md#from-source-developers) and [docs/development.md](docs/development.md).

## Before submitting

### Backend

```bash
cd backend
ruff check mindvault tests
mypy mindvault/domain mindvault/parsers mindvault/embeddings mindvault/vectorstore mindvault/llm mindvault/security mindvault/jobs --follow-imports=skip
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests/eval
```

### Frontend

```bash
cd frontend
npx tsc --noEmit
npm run test
npm run build
```

### E2E (optional)

```bash
# Start backend with mock provider, then:
cd frontend
npx playwright install chromium
npx playwright test
```

## Architecture notes

- Providers (LLM, embeddings, vector store, parsers) are swappable
  interfaces — see `backend/mindvault/*/base.py`.
- The RAG pipeline is in `backend/mindvault/rag/rag_service.py`.
- Document parsers are in `backend/mindvault/parsers/`.
- Tests use `MockLLMProvider` and `HashEmbeddingProvider` so they run
  without GPU or external services.

## Privacy promise

- Never add analytics, telemetry or tracking.
- Never require an external API key for core functionality.
- Never send user data outside the local machine without explicit opt-in.
- Review all pull requests for these principles.