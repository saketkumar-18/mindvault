# Third-Party Licenses

MindVault itself is licensed under AGPL-3.0. This file tracks licenses of
third-party software MindVault depends on, and clarifies that **no model
weights are redistributed** by MindVault.

## Model weights

MindVault does **not** bundle, download, or redistribute any AI model weights.
Users obtain models through their chosen local runtime (Ollama, llama.cpp,
Hugging Face), which are subject to each model's own license. Refer to the
license that ships with the model you choose. Examples (verify before use):

- Llama 3.x — Llama Community License (Meta).
- Mistral — Apache-2.0.
- nomic-embed-text — Apache-2.0.
- all-MiniLM-L6-v2 — Apache-2.0.

## Python runtime dependencies

The backend depends on the following packages (see `backend/pyproject.toml`
for versions). License summaries:

| Package | License |
|---|---|
| FastAPI | MIT |
| Starlette | BSD-3-Clause |
| Uvicorn | BSD-3-Clause |
| Pydantic | MIT |
| pydantic-settings | MIT |
| SQLAlchemy | MIT |
| Alembic | MIT |
| pypdf | BSD-3-Clause |
| python-docx | MIT |
| python-multipart | Apache-2.0 |
| httpx | BSD-3-Clause |
| NumPy | BSD-3-Clause |
| sentence-transformers (optional `[ml]`) | Apache-2.0 |
| faiss-cpu (optional `[ml]`) | MIT |
| llama-cpp-python (optional) | MIT |
| pytest (dev) | MIT |
| ruff (dev) | MIT |
| mypy (dev) | MIT |

## Frontend dependencies

| Package | License |
|---|---|
| React | MIT |
| React DOM | MIT |
| TypeScript | Apache-2.0 |
| Vite | MIT |
| Tailwind CSS | MIT |
| @tanstack/react-query | MIT |
| React Router | MIT |
| lucide-react | ISC |
| Vitest | MIT |
| @testing-library/* | MIT |
| Playwright | Apache-2.0 |

> This file is a summary and does not replace each project's license text.
> Full texts are available in the installed packages (e.g. `site-packages/<pkg>/LICENSE`
> or `node_modules/<pkg>/LICENSE`).
