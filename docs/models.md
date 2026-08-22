# Local Model Guide

MindVault works with fully local models. It never calls cloud AI APIs.

## LLM providers

### Ollama (recommended)

1. Install [Ollama](https://ollama.com/download) for your OS.
2. Pull a model: `ollama pull llama3.2:3b`
3. Keep Ollama running (it auto-starts as a service).
4. In MindVault **Settings → AI**, select the model and click **Test Model**.

MindVault connects to Ollama's local HTTP API at `http://127.0.0.1:11434`
(configurable via `MV_OLLAMA_URL`).

### llama.cpp

1. Build or download `llama-server` for your platform.
2. Run it with a GGUF model:
   ```
   llama-server -m path/to/model.gguf --host 127.0.0.1
   ```
3. MindVault auto-detects the OpenAI-compatible endpoint.

### Mock provider (development/testing only)

Set `MV_LLM_PROVIDER=mock` for deterministic test responses without any model.
Never used in production.

## Recommended models by hardware

Model size → quality trade-off. Start small, upgrade if hardware allows.

| Hardware | Recommended model | Notes |
|---|---|---|
| 8 GB RAM (low) | `llama3.2:3b` | Runs on CPU |
| 16 GB RAM (medium) | `llama3.1:8b` | Good balance on CPU; better with GPU |
| 32 GB+ / discrete GPU | `llama3.1:70b` (q4) | Requires ~40 GB+ RAM or GPU VRAM |

MindVault never assumes CUDA exists — everything runs on CPU by default, and
GPU acceleration (CUDA / ROCm / Metal) is provided by your chosen runtime
(Ollama handles this for you).

## Embedding models

Embeddings are used for semantic search and RAG retrieval.

| Provider | Quality | Download | Offline after setup |
|---|---|---|---|
| `hash` (default) | lexical similarity | **None** | ✅ always |
| `sentence-transformers` (`all-MiniLM-L6-v2`) | good semantic similarity | ~90 MB once | ✅ |

To enable sentence-transformers:

```bash
pip install -e "backend[ml]"
# or
pip install sentence-transformers
```

then set `MV_EMBEDDING_PROVIDER=sentence-transformers`. The model downloads
once and is cached locally. **After changing the embedding model, re-index
your documents** (the app shows a "rebuild required" notice).

For Ollama-based embeddings (e.g. `nomic-embed-text`), the provider architecture
supports adding an `OllamaEmbeddingProvider` — see `backend/mindvault/embeddings/`.

## Model licensing

MindVault does not redistribute model weights. Each model has its own license;
you are responsible for respecting it. Check the license that ships with the
model you choose (see `THIRD_PARTY_LICENSES.md`).
