# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | ✅ Active |

## Reporting a vulnerability

MindVault takes security seriously. If you find a security vulnerability,
please do NOT file a public issue. Instead, email the maintainers at
**security@mindvault.local** (placeholder — replace with a real address).

We will:

1. Acknowledge receipt within 48 hours.
2. Investigate and fix the issue.
3. Release a security update.
4. Credit the reporter (if desired).

## Scope

The following are in scope:

- Remote code execution or command injection.
- Path traversal or arbitrary file access.
- Prompt injection that bypasses the untrusted-data guard.
- SQL injection (the ORM protects against it, but we check).
- XSS or CSRF in the web UI.

The following are out of scope:

- Local denial of service on one's own machine.
- Attacks requiring physical access.
- Social engineering.

## Security features

- Documents are treated as **untrusted data**, not instructions
  (see `backend/mindvault/rag/rag_service.py` — the RAG system prompt).
- File uploads are validated by extension, size, MIME type, and content hash.
- Stored filenames are UUID-based; no direct path exposure.
- SQLite uses parameterized queries via SQLAlchemy.
- The web UI uses React's escaping (no `dangerouslySetInnerHTML`).
- LLM providers cannot execute shell commands.
- All external AI APIs are disabled by default.