# MindVault API

MindVault exposes a REST API over HTTP (JSON), plus Server-Sent Events for
streaming chat. Interactive OpenAPI documentation is available at
`/docs` (Swagger UI) and `/openapi.json` while the backend is running.

All endpoints are under `/api`. There is **no authentication** in the default
local mode: the server binds to `127.0.0.1` by default and assumes the client
is the local user. When exposing MindVault beyond localhost, place it behind a
trusted network / reverse proxy.

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/health`, `/api/health` | Overall health (DB, vector store, model) |
| GET | `/liveness`, `/api/liveness` | Process is alive |
| GET | `/readiness`, `/api/readiness` | Ready to serve requests |

Responses are JSON like `{"status":"ok","database":true,"vector_store":3,"model":{...}}`.

## System

| Method | Path | Description |
|---|---|---|
| GET | `/api/system/info` | OS, CPU, RAM, GPU, storage, model status |
| GET | `/api/system/stats` | Document/KB/conversation counts, bytes, model |
| GET | `/api/system/first-run` | First-run wizard state |
| POST | `/api/system/first-run/complete` | Mark first-run complete |
| DELETE | `/api/system/data?confirm=DELETE` | **Clear all data** (dangerous) |

## Documents

| Method | Path | Description |
|---|---|---|
| POST | `/api/documents` | Upload (multipart `file`; optional `knowledge_base_id`, `replace`, `duplicate`) |
| GET | `/api/documents` | List (filters: `knowledge_base_id`, `status`, `file_type`, `q`, `limit`, `offset`) |
| GET | `/api/documents/{id}` | Details |
| GET | `/api/documents/{id}/download` | Download original file (attachment) |
| GET | `/api/documents/{id}/view` | View original file inline (e.g. browser-rendered PDF) |
| PATCH | `/api/documents/{id}` | Rename and/or set knowledge base (`{"filename": "...", "knowledge_base_id": "..."}`; `knowledge_base_id: null` unassigns) |
| DELETE | `/api/documents/{id}` | Delete + cleanup vectors/chunks/file |
| POST | `/api/documents/{id}/reindex` | Re-run indexing |
| GET | `/api/documents/{id}/chunks` | List chunks (paged) |

Upload responses include the new document id and, on duplicate content, a 409
with `error.details.existing_id`.

## Knowledge bases

| Method | Path | Description |
|---|---|---|
| GET | `/api/knowledge-bases` | List |
| POST | `/api/knowledge-bases` | Create `{name, description?}` |
| GET | `/api/knowledge-bases/{id}` | Detail + statistics |
| PATCH | `/api/knowledge-bases/{id}` | Rename `{name}` |
| DELETE | `/api/knowledge-bases/{id}` | Delete (documents unassigned, kept) |
| POST | `/api/knowledge-bases/{id}/documents` | Assign documents `{"document_ids":[...]}` |
| DELETE | `/api/knowledge-bases/{id}/documents/{doc_id}` | Remove document from KB |

## Chat & conversations

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | Ask. Body: `{message, conversation_id?, knowledge_base_id?, stream?}`. If `stream:false` returns JSON; if `stream:true` (default) returns SSE |
| POST | `/api/chat/{id}/stop` | Stop generation |
| POST | `/api/chat/{id}/regenerate?stream=...` | Regenerate last answer |
| POST | `/api/conversations` | Create conversation |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Detail with messages |
| PATCH | `/api/conversations/{id}` | Rename `{title}` |
| DELETE | `/api/conversations/{id}` | Delete conversation |

### SSE stream format

The streaming response is `text/event-stream` with JSON `data:` lines:

```
data: {"type":"sources","sources":[{"chunk_id":"…","document_id":"…","filename":"…","score":0.9,"page_start":12,"page_end":12,"section":null,"excerpt":"…"}]}

data: {"type":"token","text":"Zero trust "}

data: {"type":"token","text":"assumes…"}

data: {"type":"done","text":"…","model":"llama3.2:3b","provider":"ollama","grounded":true}

event: done
data: {}
```

Error events look like `{"type":"error","message":"…","suggestion":"…"}`.

## Search

| Method | Path | Description |
|---|---|---|
| POST | `/api/search` | Body: `{query, knowledge_base_id?, document_ids?, file_types?, top_k?, global_scope?}`. `global_scope:true` also searches conversations and KBs |

## Settings

| Method | Path | Description |
|---|---|---|
| GET | `/api/settings` | Effective settings + `rebuild_required` flag |
| PUT | `/api/settings` | Partial nested update `{ai:{...}, retrieval:{...}, ...}` |
| POST | `/api/settings/reset` | Reset to defaults |

## Models

| Method | Path | Description |
|---|---|---|
| GET | `/api/models` | Current model, installed candidates, Ollama/llama.cpp status |
| POST | `/api/models/test` | Run a quick generation test (returns latency) |

## Jobs

| Method | Path | Description |
|---|---|---|
| GET | `/api/jobs` | List background jobs (index/reindex, status, progress) |
| POST | `/api/jobs/{id}/cancel` | Cancel a queued/processing job |

## Study

| Method | Path | Description |
|---|---|---|
| POST | `/api/study/generate` | Body: `{kind, document_id? or knowledge_base_id?}`. Kinds: `summary, flashcards, mcq, short_answer, interview, concepts, revision` |
| POST | `/api/study/compare` | Body: `{document_ids: [...]}` (2–5 documents). Generates similarities, differences, missing concepts, summary |
| POST | `/api/study/resume-analysis` | Body: `{resume_document_id, job_description_document_id}`. Resume compatibility analysis (informational, not an ATS score) |
| GET | `/api/study/materials` | List generated materials |
| GET | `/api/study/materials/{id}` | Detail |
| DELETE | `/api/study/materials/{id}` | Delete |

## Export

| Method | Path | Description |
|---|---|---|
| GET | `/api/export/conversations` | JSON download |
| GET | `/api/export/knowledge-bases` | JSON download |
| GET | `/api/export/all` | ZIP of the above |

## Errors

All errors return:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable message.",
    "status": 422,
    "details": { ... optional ... },
    "suggestion": "Suggested action."
  }
}
```

Common status codes:

- `400` security / bad request
- `404` not found
- `409` conflict (duplicate document, duplicate KB name, not ready)
- `413` payload too large
- `415` unsupported file type
- `422` validation failure
- `503` provider/index unavailable

Stack traces are never returned to the client; they go to the structured
server logs.
