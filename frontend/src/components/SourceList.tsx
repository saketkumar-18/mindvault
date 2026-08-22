import type { SourceCitation } from "../lib/types";
import { truncate } from "../lib/format";

export function SourceList({ sources, onSelect }: { sources: SourceCitation[]; onSelect?: (s: SourceCitation) => void }) {
  if (!sources.length) {
    return (
      <p className="text-sm text-[var(--color-mv-muted)] italic">
        This answer could not be grounded in your documents.
      </p>
    );
  }
  return (
    <ul className="space-y-2" aria-label="Sources">
      {sources.map((s, i) => (
        <li key={`${s.chunk_id}-${i}`}>
          <button
            type="button"
            onClick={() => onSelect?.(s)}
            className="w-full text-left rounded-lg border border-[var(--color-mv-border)] bg-[var(--color-mv-bg)] p-2 hover:border-[var(--color-mv-primary)] transition-colors"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold text-[var(--color-mv-primary)]">{s.filename}</span>
              <span className="text-[10px] text-[var(--color-mv-muted)]">
                {s.page_start ? `page ${s.page_start}${s.page_end && s.page_end !== s.page_start ? `-${s.page_end}` : ""}` : ""}
                {" · "}
                score {s.score.toFixed(2)}
              </span>
            </div>
            <p className="mt-1 text-xs text-[var(--color-mv-text)] line-clamp-2">{truncate(s.excerpt, 160)}</p>
          </button>
        </li>
      ))}
    </ul>
  );
}
