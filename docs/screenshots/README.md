# Screenshots

Real screenshots captured with Playwright against a running instance:

- `welcome.png` — first-run onboarding wizard
- `dashboard.png` — stats, model status, indexing status
- `documents.png` — document management with status badges
- `knowledge-bases.png` — knowledge base cards
- `chat.png` — grounded answer with clickable sources
- `search.png` — semantic search results
- `study.png` — study tools (generate / compare / resume analysis)
- `settings.png` — settings sections

Regenerate with:

```bash
# fresh MV_HOME + backend running with mock providers serving frontend/dist
cd frontend
MINDVAULT_E2E_URL=http://127.0.0.1:8010 CAPTURE_SCREENSHOTS=1 npx playwright test screenshots.spec.ts
```
