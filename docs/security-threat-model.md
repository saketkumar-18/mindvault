# MindVault Security Threat Model

This document describes the threats MindVault defends against and the
mitigations in place. MindVault is **local-first**: the threat model assumes
an attacker who can submit untrusted documents and/or queries through the
application's interfaces, plus standard supply-chain and dependency risks.

## Assets

- User documents (private by nature).
- User conversations and generated study materials.
- Local SQLite database and vector index.
- The user's machine (no remote code execution should be possible).

## Trust boundaries

1. **Untrusted input → parser**: uploaded files (PDF/DOCX/TXT/MD/CSV/JSON).
2. **Untrusted input → RAG prompt**: extracted document text.
3. **Local API → local providers**: the frontend to the backend, and the
   backend to the local LLM/embedding runtimes.
4. **User machine**: the process itself, running as the local user.

---

## 1. Malicious documents

**Threat:** a crafted file (malformed PDF/DOCX, oversized, empty, zip-bomb-like
content) crashes the parser, exhausts memory, or leaks host data.

**Mitigations:**

- Extension and MIME validation against an allowlist (`validate_upload`).
- Maximum upload size (default 100 MB) enforced server-side.
- Streaming reads with size caps (`read_stream_limited`).
- Maximum page count (default 2000) to bound parsing work.
- Parser errors are caught and surfaced as failed indexing, not crashes.
- Files are stored with UUID names; display names are sanitized.

## 2. Path traversal / arbitrary file access

**Threat:** `../../etc/passwd` in a filename or crafted parameter reads or
overwrites files outside the data directory.

**Mitigations:**

- `sanitize_display_name` strips path components.
- `resolve_under(base, ...)` verifies the resolved path stays under `base`.
- All stored filenames are `{uuid}.{ext}`.
- Document download resolves through the same `resolve_under` guard.

## 3. Prompt injection from documents

**Threat:** a PDF containing *"Ignore all previous instructions…"* causes the
model to disclose data or behave contrary to the user's intent.

**Mitigations:**

- The RAG system prompt treats `<documents>` content as **untrusted data**.
- The prompt explicitly forbids following instructions found in documents.
- The model is instructed to say *"I couldn't find enough information in your
  documents."* when evidence is insufficient, and never to invent citations.
- MindVault does not give the LLM any tool-calling capability: **the model
  cannot execute shell commands or make network requests.**

## 4. Local file attacks / symlink abuse

**Threat:** a symlink in the data directory redirects writes or reads.

**Mitigations:**

- The data directory is under the user's control; `resolve_under` uses
  `.resolve()` to canonicalize paths and refuses escapes.
- Deletion uses `unlink(missing_ok=True)` on the resolved path.

## 5. Malicious uploads (CPU/memory exhaustion)

**Threat:** a huge CSV/JSON with millions of rows exhausts memory.

**Mitigations:**

- CSV/JSON parsers cap rows/entries (50 000 rows, 20 000 entries).
- Upload size caps and page caps apply.
- Chunk embedding is batched.

## 6. SQL injection / database tampering

**Threat:** crafted input reaches the database.

**Mitigations:**

- All queries go through SQLAlchemy parameterized statements — no string
  interpolation of user data.
- SQLite runs with `PRAGMA foreign_keys=ON` and WAL.

## 7. Cross-site scripting (XSS)

**Threat:** a malicious document name or model response executes script in the
user's browser.

**Mitigations:**

- React escapes all text by default; the UI never uses
  `dangerouslySetInnerHTML`.
- Model output is rendered as text (no markdown/HTML rendering in v1).

## 8. Unauthorized local access

**Threat:** another local process or network host reaches the MindVault API.

**Mitigations:**

- The server binds to `127.0.0.1` by default.
- CORS restricts browser origins to the configured list (dev frontend).
- Documentation warns to use a reverse proxy when binding beyond localhost.

## 9. Model abuse / refusal bypass

**Threat:** prompts engineered to extract raw document content or bypass
system rules.

**Mitigations:**

- RAG prompt hardening (see #3).
- Grounding checks flag insufficient evidence.
- This is an inherently hard problem with LLMs; MindVault reduces the attack
  surface (no tools, local-only, no data exfiltration channel).

## 10. Dependency vulnerabilities

**Threat:** a vulnerable version of FastAPI, httpx, pypdf, etc.

**Mitigations:**

- Dependabot weekly updates (pip, npm, GitHub Actions).
- CI runs `pip-audit` and `npm audit` (npm audit tolerated for dev deps).
- Breaking changes are reviewed before upgrades.

## 11. Supply-chain risks

**Threat:** a compromised dependency or model download.

**Mitigations:**

- Dependencies are pinned with ranges; lockfiles are committed (`uv.lock`
  recommended, `package-lock.json` committed).
- Model weights are never bundled; downloads come from the user's chosen
  provider and are subject to their licenses.

## 12. Secret exposure

**Threat:** credentials committed to the repository.

**Mitigations:**

- `.gitignore` excludes `.env`, keys, DB files, documents, model files.
- CI has no required secrets.
- Structured logging never includes document contents, API keys, or
  credentials.

---

## What MindVault deliberately does *not* do

- Execute shell commands from model output.
- Auto-execute generated code.
- Make outbound network requests by default.
- Require accounts, API keys, or cloud services.

## Reporting

See [SECURITY.md](../SECURITY.md).
