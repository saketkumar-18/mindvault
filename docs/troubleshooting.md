# Troubleshooting

Common issues and fixes for MindVault.

## "Your local AI model is not currently available."

- Verify Ollama is running: `curl http://127.0.0.1:11434/api/tags`
  (PowerShell: `Invoke-RestMethod http://127.0.0.1:11434/api/tags`).
- Verify a model is installed: `ollama list` — if empty, `ollama pull llama3.2:3b`.
- In MindVault **Settings → AI**, select the model and click **Test Model**.
- If using llama.cpp, confirm `llama-server` is running and reachable.

## The model returns gibberish like "@@@@@@..."

This typically means your local LLM runtime is trying to use an **unsupported
GPU**. On Windows, Ollama does not support AMD GPUs (ROCm is Linux-only), and
on some machines it will attempt to use the AMD adapter and produce repeated
garbage tokens.

Fix: force CPU inference for Ollama.

```powershell
# Set for your user (persists), then restart Ollama:
setx OLLAMA_LLM_LIBRARY cpu
# Fully quit Ollama (tray icon → Quit), then start it again.
```

Verify: `ollama run llama3.2:1b "say hello"` should return a normal sentence.
Then re-test the model in MindVault **Settings → AI → Test Model**.

## Search returns nothing or poor results

- Documents must show status **indexed** in the Documents page.
- With the default `hash` embedding provider, search is lexical. For better
  semantic results: `pip install -e "backend[ml]"`, set
  `MV_EMBEDDING_PROVIDER=sentence-transformers`, and re-index documents.
- Lower the similarity threshold in **Settings → Retrieval** (default 0.05).

## "Index rebuild required"

You changed the embedding model or dimension. Re-index your documents
(**Documents → Re-index** for each, or upload again).

## Upload fails with 415

The file type is not allowed. Supported: `pdf, docx, txt, md, csv, json`.

## Upload fails with 413

The file exceeds `MV_MAX_UPLOAD_BYTES` (default 100 MB).

## Port already in use

```bash
python -m mindvault --port 9000
# or set MV_PORT=9000
```

## Vector index corrupt / dimension mismatch

- Delete `{MV_HOME}/index/index.npz` (and `.ids.json`) and restart — the index
  rebuilds from SQLite chunk data on re-index.
- Change `MV_EMBEDDING_DIM` only together with the embedding model, then re-index.

## Everything seems to hang

- Check the structured logs (stdout). Enable verbose logging with `MV_DEBUG=1`.
- Embedding/indexing of large PDFs runs in the background — check the Jobs list.

## Browser shows blank screen after upgrade

- Hard-refresh (Ctrl+Shift+R). Old cached JS sometimes lingers.

## Docker: can't pull a model

```bash
docker compose exec ollama ollama pull llama3.2:3b
```

(Service name may be `mindvault-ollama-1` depending on compose project name.)
