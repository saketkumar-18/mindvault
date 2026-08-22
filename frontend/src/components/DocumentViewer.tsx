import { useCallback, useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy, PDFPageProxy } from "pdfjs-dist";
import { api } from "../lib/api";
import { Modal, Spinner } from "./ui";
import { t } from "../lib/i18n";
import type { ChunkInfo } from "../lib/types";

const PAGE_SIZE = 20;

export interface ViewerTarget {
  page?: number | null;
  query?: string;
}

export function DocumentViewer({
  documentId,
  filename,
  extension,
  target,
  onClose,
}: {
  documentId: string;
  filename: string;
  extension?: string | null;
  target?: ViewerTarget;
  onClose: () => void;
}) {
  const isPdf = (extension ?? filename.split(".").pop() ?? "").toLowerCase() === "pdf";
  const [tab, setTab] = useState<"pdf" | "chunks">(isPdf ? "pdf" : "chunks");

  return (
    <Modal open onClose={onClose} title={filename}>
      {isPdf && (
        <div className="mb-3 flex gap-2" role="tablist" aria-label="Document view">
          <button
            role="tab"
            aria-selected={tab === "pdf"}
            className={`btn ${tab === "pdf" ? "btn-primary" : "btn-ghost"} text-xs`}
            onClick={() => setTab("pdf")}
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
      {tab === "pdf" ? (
        <PdfViewer key={documentId} documentId={documentId} initialPage={target?.page ?? null} />
      ) : (
        <ChunkBrowser documentId={documentId} highlightQuery={target?.query ?? null} />
      )}
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// pdf.js renderer with page navigation and search highlighting.
// pdfjs-dist is bundled locally — no CDN, works fully offline.
// ---------------------------------------------------------------------------
function PdfViewer({ documentId, initialPage }: { documentId: string; initialPage: number | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [doc, setDoc] = useState<{ numPages: number } | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const pdfRef = useRef<PDFDocumentProxy | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        const worker = await import("pdfjs-dist/build/pdf.worker.mjs?url");
        pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
        const loadingTask = pdfjs.getDocument({ url: `/api/documents/${documentId}/view` });
        const pdf = (await loadingTask.promise) as unknown as PDFDocumentProxy;
        if (cancelled) return;
        pdfRef.current = pdf;
        setDoc({ numPages: pdf.numPages });
        setPage(Math.min(Math.max(1, initialPage ?? 1), pdf.numPages));
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not render PDF.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [documentId, initialPage]);

  const renderPage = useCallback(async (num: number) => {
    const canvas = canvasRef.current;
    const pdf = pdfRef.current;
    if (!canvas || !pdf) return;
    const pdfPage = (await pdf.getPage(num)) as unknown as PDFPageProxy;
    const scale = 1.4;
    const viewport = pdfPage.getViewport({ scale });
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    await pdfPage.render({ canvas, viewport }).promise;
  }, []);

  useEffect(() => {
    if (doc) void renderPage(page);
  }, [doc, page, renderPage]);

  async function doSearch() {
    const q = query.trim();
    const pdf = pdfRef.current;
    if (!q || !pdf) return;
    setSearching(true);
    try {
      for (let p = 1; p <= doc!.numPages; p++) {
        const pdfPage = (await pdf.getPage(p)) as unknown as PDFPageProxy;
        const content = await pdfPage.getTextContent();
        const text = content.items
          .map((it) => ("str" in it ? it.str ?? "" : ""))
          .join(" ");
        if (text.toLowerCase().includes(q.toLowerCase())) {
          setPage(p);
          break;
        }
      }
    } finally {
      setSearching(false);
    }
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-[var(--color-mv-muted)]">
        <button className="btn btn-ghost px-2 py-1" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} type="button">
          ← Prev
        </button>
        <span>
          Page {page} / {doc?.numPages ?? "…"}
        </span>
        <button className="btn btn-ghost px-2 py-1" onClick={() => setPage((p) => Math.min(doc?.numPages ?? 1, p + 1))} disabled={page >= (doc?.numPages ?? 1)} type="button">
          Next →
        </button>
        <div className="ml-auto flex items-center gap-1">
          <input
            className="input w-40 text-xs"
            placeholder="Find in PDF…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void doSearch();
            }}
            aria-label="Find in PDF"
          />
          <button className="btn btn-ghost px-2 py-1" onClick={() => void doSearch()} disabled={searching} type="button">
            {searching ? "…" : "Find"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      ) : error ? (
        <p className="rounded-lg bg-[var(--color-mv-danger-soft)] px-3 py-2 text-sm text-[var(--color-mv-danger)]">{error}</p>
      ) : (
        <div className="max-h-[65vh] overflow-y-auto rounded-lg border border-[var(--color-mv-border)] bg-white p-2">
          <canvas ref={canvasRef} className="mx-auto" />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Indexed-text browser with optional highlight query (used for citations).
// ---------------------------------------------------------------------------
function ChunkBrowser({ documentId, highlightQuery }: { documentId: string; highlightQuery?: string | null }) {
  const [chunks, setChunks] = useState<ChunkInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const highlightRef = useRef<HTMLDivElement>(null);

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

  // Scroll the highlighted chunk into view.
  useEffect(() => {
    if (highlightQuery && highlightRef.current) {
      highlightRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [chunks, highlightQuery]);

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function matches(c: ChunkInfo): boolean {
    return !!highlightQuery && c.text.toLowerCase().includes(highlightQuery.toLowerCase());
  }

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
          {chunks.map((c) => {
            const hit = matches(c);
            return (
              <div
                key={c.id}
                ref={hit ? highlightRef : undefined}
                className={`rounded-lg border p-3 ${hit ? "border-[var(--color-mv-primary)] bg-[var(--color-mv-primary-soft)]" : "border-[var(--color-mv-border)]"}`}
              >
                <div className="mb-1 flex items-center gap-2 text-[10px] text-[var(--color-mv-muted)]">
                  <span className="rounded bg-[var(--color-mv-bg)] px-1.5 py-0.5 font-mono">#{c.ordinal}</span>
                  {c.page_start && <span>{t("search.page", { page: String(c.page_start) })}</span>}
                  {c.section && <span className="truncate">§ {c.section}</span>}
                </div>
                <p className="whitespace-pre-wrap text-xs leading-relaxed">{c.text}</p>
              </div>
            );
          })}
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
