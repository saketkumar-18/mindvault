import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useDocuments, useKnowledgeBases, useStudyMaterials } from "../hooks/queries";
import { api, AppApiError } from "../lib/api";
import { Spinner, EmptyState, ErrorState } from "../components/ui";
import { useToast } from "../components/Toast";
import { t } from "../lib/i18n";
import { formatDate } from "../lib/format";
import type { TranslationKey } from "../lib/i18n";

type Mode = "generate" | "compare" | "resume";

const KINDS = ["summary", "flashcards", "mcq", "short_answer", "interview", "concepts", "revision"] as const;
const KIND_LABEL: Record<(typeof KINDS)[number], TranslationKey> = {
  summary: "study.kind.summary",
  flashcards: "study.kind.flashcards",
  mcq: "study.kind.mcq",
  short_answer: "study.kind.short_answer",
  interview: "study.kind.interview",
  concepts: "study.kind.concepts",
  revision: "study.kind.revision",
};

interface GeneratedContent {
  text?: string;
  items?: Array<{ front?: string; back?: string; question?: string; options?: string[]; answer?: string }>;
  parse_warning?: string;
}

export default function Study() {
  const { data: docs } = useDocuments();
  const { data: kbs } = useKnowledgeBases();
  const { data: materials, isLoading, refetch, error } = useStudyMaterials();

  const [mode, setMode] = useState<Mode>("generate");
  const [kind, setKind] = useState<(typeof KINDS)[number]>("summary");
  const [scope, setScope] = useState<"document" | "kb">("document");
  const [documentId, setDocumentId] = useState("");
  const [kbId, setKbId] = useState("");

  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [resumeId, setResumeId] = useState("");
  const [jobDescId, setJobDescId] = useState("");

  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<{ id: string; kind: string; title: string; content: string } | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const allDocs = docs?.documents ?? [];

  async function generate() {
    const payload: Record<string, string> = { kind };
    if (scope === "document") {
      if (!documentId) return;
      payload.document_id = documentId;
    } else {
      if (!kbId) return;
      payload.knowledge_base_id = kbId;
    }
    await run(payload, "/api/study/generate");
  }

  async function compare() {
    if (compareIds.length < 2) return;
    await run({ document_ids: compareIds }, "/api/study/compare");
  }

  async function resume() {
    if (!resumeId || !jobDescId) return;
    await run({ resume_document_id: resumeId, job_description_document_id: jobDescId }, "/api/study/resume-analysis");
  }

  async function run(payload: Record<string, unknown>, path: string) {
    setGenerating(true);
    setResult(null);
    try {
      const res = await api.post<{ id: string; kind: string; title: string; content: string }>(path, payload);
      setResult(res);
      toast("Generated.", "success");
      void queryClient.invalidateQueries({ queryKey: ["study-materials"] });
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Generation failed.", "error");
    } finally {
      setGenerating(false);
    }
  }

  const canGenerate = mode === "generate" && (scope === "document" ? !!documentId : !!kbId);
  const canCompare = mode === "compare" && compareIds.length >= 2;
  const canResume = mode === "resume" && !!resumeId && !!jobDescId;
  const canSubmit = mode === "generate" ? canGenerate : mode === "compare" ? canCompare : canResume;

  function toggleCompare(id: string) {
    setCompareIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  let content: GeneratedContent | null = null;
  if (result) {
    try {
      content = JSON.parse(result.content) as GeneratedContent;
    } catch {
      content = { text: result.content };
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-xl font-bold">{t("study.title")}</h1>

      {/* Mode selector */}
      <div className="flex gap-2" role="tablist" aria-label="Study tools">
        {(["generate", "compare", "resume"] as Mode[]).map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            className={`btn ${mode === m ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setMode(m)}
            type="button"
          >
            {m === "generate" ? "Generate Study Material" : m === "compare" ? "Compare Documents" : "Resume Analysis"}
          </button>
        ))}
      </div>

      <div className="card p-5">
        {mode === "generate" && (
          <>
            <h2 className="mb-4 text-sm font-semibold">{t("study.generate")}</h2>
            <div className="grid gap-3 md:grid-cols-4">
              <div>
                <label className="label">Type</label>
                <select className="input" value={kind} onChange={(e) => setKind(e.target.value as (typeof KINDS)[number])}>
                  {KINDS.map((k) => (
                    <option key={k} value={k}>{t(KIND_LABEL[k])}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Scope</label>
                <select className="input" value={scope} onChange={(e) => setScope(e.target.value as "document" | "kb")}>
                  <option value="document">{t("study.scopeDoc")}</option>
                  <option value="kb">{t("study.scopeKb")}</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="label">Source</label>
                {scope === "document" ? (
                  <select className="input" value={documentId} onChange={(e) => setDocumentId(e.target.value)}>
                    <option value="">Select document…</option>
                    {allDocs.map((d) => (
                      <option key={d.id} value={d.id}>{d.filename}</option>
                    ))}
                  </select>
                ) : (
                  <select className="input" value={kbId} onChange={(e) => setKbId(e.target.value)}>
                    <option value="">Select knowledge base…</option>
                    {(kbs?.knowledge_bases ?? []).map((kb) => (
                      <option key={kb.id} value={kb.id}>{kb.name}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          </>
        )}

        {mode === "compare" && (
          <>
            <h2 className="mb-2 text-sm font-semibold">Compare Documents</h2>
            <p className="mb-3 text-xs text-[var(--color-mv-muted)]">
              Select 2–5 documents to compare similarities, differences, and missing concepts.
            </p>
            <div className="space-y-1.5">
              {allDocs.map((d) => (
                <label key={d.id} className="flex cursor-pointer items-center gap-2 rounded-lg border border-[var(--color-mv-border)] px-3 py-2 text-sm hover:border-[var(--color-mv-primary)]">
                  <input
                    type="checkbox"
                    checked={compareIds.includes(d.id)}
                    onChange={() => toggleCompare(d.id)}
                    className="accent-[var(--color-mv-primary)]"
                  />
                  <span className="truncate">{d.filename}</span>
                </label>
              ))}
              {allDocs.length === 0 && <p className="text-sm text-[var(--color-mv-muted)]">Upload documents first.</p>}
            </div>
          </>
        )}

        {mode === "resume" && (
          <>
            <h2 className="mb-2 text-sm font-semibold">Resume Compatibility Analysis</h2>
            <p className="mb-3 text-xs text-[var(--color-mv-muted)]">
              Compare a resume against a job description. Informational only — not an official ATS score.
            </p>
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="label">Resume document</label>
                <select className="input" value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
                  <option value="">Select resume…</option>
                  {allDocs.map((d) => (
                    <option key={d.id} value={d.id}>{d.filename}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Job description document</label>
                <select className="input" value={jobDescId} onChange={(e) => setJobDescId(e.target.value)}>
                  <option value="">Select job description…</option>
                  {allDocs.map((d) => (
                    <option key={d.id} value={d.id}>{d.filename}</option>
                  ))}
                </select>
              </div>
            </div>
          </>
        )}

        <button
          className="btn btn-primary mt-4"
          onClick={() => void (mode === "generate" ? generate() : mode === "compare" ? compare() : resume())}
          disabled={generating || !canSubmit}
          type="button"
        >
          {generating ? t("common.generating") : mode === "generate" ? t("study.generate") : "Generate"}
        </button>
      </div>

      {result && content && (
        <div className="card p-5">
          <h3 className="mb-3 text-base font-semibold">{result.title}</h3>
          {content.parse_warning && (
            <p className="mb-2 text-xs text-[var(--color-mv-warning)]">{content.parse_warning}</p>
          )}
          {content.items && content.items.length > 0 ? (
            <div className="space-y-4">
              {content.items.map((item, i) => (
                <div key={i} className="rounded-lg border border-[var(--color-mv-border)] p-3">
                  <p className="text-sm font-medium">{item.question ?? item.front}</p>
                  {item.options && (
                    <ul className="mt-1 list-disc pl-5 text-xs text-[var(--color-mv-muted)]">
                      {item.options.map((opt, j) => (
                        <li key={j}>{opt}</li>
                      ))}
                    </ul>
                  )}
                  {(item.answer ?? item.back) && (
                    <p className="mt-2 text-sm text-[var(--color-mv-success)]">→ {item.answer ?? item.back}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{content.text}</p>
          )}
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-sm font-semibold">{t("study.history")}</h2>
        {isLoading && <Spinner />}
        {error && <ErrorState message={t("common.error")} onRetry={() => void refetch()} />}
        {!isLoading && (materials?.materials?.length ?? 0) === 0 && (
          <EmptyState title={t("common.empty")} />
        )}
        {(materials?.materials ?? []).map((m) => {
          const label =
            m.kind === "comparison"
              ? "Comparison"
              : m.kind === "resume_analysis"
                ? "Resume Analysis"
                : t(KIND_LABEL[m.kind as (typeof KINDS)[number]] ?? "study.kind.summary");
          return (
            <div key={m.id} className="card flex items-center justify-between p-3">
              <div>
                <span className="text-sm font-medium">{label}</span>
                <span className="ml-2 text-xs text-[var(--color-mv-muted)]">{m.title}</span>
              </div>
              <span className="text-xs text-[var(--color-mv-muted)]">{formatDate(m.created_at)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
