# RAG Evaluation

MindVault ships a small, labeled evaluation dataset and a regression test to
track retrieval quality over time.

## Dataset

`backend/tests/eval/rag_eval_dataset.jsonl` — five documents, each with a
natural-language question and the expected answer fragments plus the source
filename.

## How it's measured

- Each question is embedded and used for top-1 retrieval.
- A hit is counted when the correct source file is retrieved first.
- The test asserts that retrieval finds the right document for **at least half**
  of the questions. The bar is intentionally achievable with the dependency-free
  `hash` embedding provider used in CI (no ML/GPU required), while still
  catching gross regressions.
- `test_answer_faithfulness_helpers` verifies the grounding helpers behave.

## Running

```bash
cd backend
MV_EMBEDDING_PROVIDER=hash MV_LLM_PROVIDER=mock pytest tests/eval
```

## Honest limitations

- This is a **regression check**, not a claim of accuracy. MindVault does not
  publish arbitrary accuracy percentages.
- With `sentence-transformers` embeddings enabled (`mindvault[ml]`), retrieval
  quality is meaningfully higher; the eval suite runs on the hash provider so
  CI needs no downloads.
- Citation correctness and answer faithfulness are enforced by prompt design
  and validated with targeted tests; a full human-eval study is roadmap work.

## Extending

Add a line to the JSONL:

```json
{"document": "...", "question": "...", "answer_contains": ["..."], "source_file": "x.txt"}
```

Keep the threshold in `test_rag_eval.py` honest — raise it only when you can
show the real system passes.
