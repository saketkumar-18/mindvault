import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Modal, Spinner } from "./ui";
import { t } from "../lib/i18n";
import type { ChunkInfo } from "../lib/types";

const PAGE_SIZE = 20;

export function DocumentViewer({ documentId, filename, extension, onClose }: { documentId: string; filename: string; extension?: string | null; onClose: () => void }) {
  const isPdf = (extension ?? filename.split(".").pop() ?? "").toLowerCase() === "pdf";
  const [tab, setTab] = useState<"native" | "chunks">(isPdf ? "native" : "chunks");

  return (
    <Modal open onClose={onClose} title={filename}>
      {isPdf && (
        <div className="mb-3 flex gap-2" role="tablist" aria-label="Document view">
          <button
            role="tab"
            aria-selected={tab === "native"}
            className={`btn ${tab === "native" ? "btn-primary" : "btn-ghost"} text-xs`}
            onClick={() => setTab("native")}
            type="button"
          >
            Rendered PDF
          </button>
          <button
            role="tab"
            aria-selected={tab === "chunks"}
            className={`btn ${tab === "chunks" ? "btn-primary" : "btn-ghost"} text-xs`}
            onClick={() => setTab("chunks")}
            type="button"
          >
            Indexed text
          </button>
        </div>
      )}
      {tab === "native" ? <PdfEmbed key={documentId} documentId={documentId} /> : <ChunkBrowser documentId={documentId} />}
    </Modal>
  );
}

function PdfEmbed({ documentId }: { documentId: string }) {
  const [error, setError] = useState<string | null>(null);
  return (
    <div>
      <p className="mb-2 text-xs text-[var(--color-mv-muted)]">
        Use the browser's PDF controls for page navigation and search. Or switch to <strong>Indexed text</strong>.
      </p>
      {error ? (
        <p className="rounded-lg bg-[var(--color-mv-danger-soft)] px-3 py-2 text-sm text-[var(--color-mv-danger)]">{error}</p>
      ) : (
        <iframe
          title="PDF preview"
          src={`/api/documents/${documentId}/view`}
          className="h-[65vh] w-full rounded-lg border border-[var(--color-mv-border)] bg-white"
          onError={() => setError("Could not render this PDF in the browser.")}
        />
      )}
    </div>
  );
}

function ChunkBrowser({ documentId }: { documentId: string }) {
  const [chunks, setChunks] = useState<ChunkInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<{ chunks: ChunkInfo[]; total: number }>(`/api/documents/${documentId}/chunks?limit=${PAGE_SIZE}&offset=${offset}`)
      .then((data) => {
        setChunks(data.chunks);
        setTotal(data.total);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load chunks."))
      .finally(() => setLoading(false));
  }, [documentId, offset]);

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <div className="flex items-center justify-between text-xs text-[var(--color-mv-muted)]">
        <span>
          {total} {t("documents.chunks", { count: String(total) })}
        </span>
        <span>
          page {page} / {pages}
        </span>
      </div>

      {loading ? (
        <div className="py-10 text-center">
          <Spinner />
        </div>
      ) : error ? (
        <p className="rounded-lg bg-[var(--color-mv-danger-soft)] px-3 py-2 text-sm text-[var(--color-mv-danger)]">{error}</p>
      ) : (
        <div className="mt-3 max-h-96 space-y-3 overflow-y-auto">
          {chunks.map((c) => (
            <div key={c.id} className="rounded-lg border border-[var(--color-mv-border)] p-3">
              <div className="mb-1 flex items-center gap-2 text-[10px] text-[var(--color-mv-muted)]">
                <span className="rounded bg-[var(--color-mv-bg)] px-1.5 py-0.5 font-mono">#{c.ordinal}</span>
                {c.page_start && <span>{t("search.page", { page: String(c.page_start) })}</span>}
                {c.section && <span className="truncate">§ {c.section}</span>}
              </div>
              <p className="whitespace-pre-wrap text-xs leading-relaxed">{c.text}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between">
        <button className="btn btn-ghost text-xs" onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))} disabled={offset === 0} type="button">
          ← Prev
        </button>
        <button className="btn btn-ghost text-xs" onClick={() => setOffset((o) => Math.min(total - PAGE_SIZE, o + PAGE_SIZE))} disabled={offset + PAGE_SIZE >= total} type="button">
          Next →
        </button>
      </div>
    </div>
  );
}
