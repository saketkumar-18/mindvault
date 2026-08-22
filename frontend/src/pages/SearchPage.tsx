import { useState } from "react";
import { searchDocuments } from "../lib/api";
import { useKnowledgeBases } from "../hooks/queries";
import { Spinner, EmptyState } from "../components/ui";
import { t } from "../lib/i18n";
import { Search } from "lucide-react";
import type { SearchResult } from "../lib/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: kbs } = useKnowledgeBases();
  const [kbFilter, setKbFilter] = useState<string | null>(null);

  async function run() {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchDocuments(q, { knowledge_base_id: kbFilter });
      setResults(res.results ?? []);
      setSearched(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
      setResults([]);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-xl font-bold">{t("search.title")}</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
        className="flex gap-2"
      >
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("search.placeholder")}
          aria-label={t("search.placeholder")}
        />
        <select className="input w-48" value={kbFilter ?? ""} onChange={(e) => setKbFilter(e.target.value || null)}>
          <option value="">{t("chat.allKbs")}</option>
          {(kbs?.knowledge_bases ?? []).map((kb) => (
            <option key={kb.id} value={kb.id}>{kb.name}</option>
          ))}
        </select>
        <button className="btn btn-primary" type="submit" disabled={!query.trim() || loading}>
          <Search size={16} />
          {t("common.search")}
        </button>
      </form>

      {loading && <Spinner />}
      {error && <p className="rounded-lg bg-[var(--color-mv-danger-soft)] px-3 py-2 text-sm text-[var(--color-mv-danger)]">{error}</p>}

      {!loading && searched && results.length === 0 && <EmptyState title={t("search.noResults")} />}

      <div className="space-y-3">
        {results.map((r) => (
          <div key={r.chunk_id} className="card p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[var(--color-mv-primary)]">{r.filename}</span>
              <span className="text-xs text-[var(--color-mv-muted)]">
                {t("search.score", { score: r.score.toFixed(2) })}
                {r.page_start ? ` · ${t("search.page", { page: String(r.page_start) })}` : ""}
              </span>
            </div>
            <p className="mt-2 text-sm text-[var(--color-mv-text)]">{r.text}</p>
            {r.section && <p className="mt-1 text-xs text-[var(--color-mv-muted)]">§ {r.section}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}