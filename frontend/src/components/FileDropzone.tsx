import { useEffect, useState } from "react";
import type { DragEvent } from "react";
import { UploadCloud, FileText } from "lucide-react";
import { uploadDocuments } from "../lib/api";
import { useToast } from "./Toast";
import { t } from "../lib/i18n";

export function FileDropzone({
  knowledgeBaseId,
  onUploaded,
}: {
  knowledgeBaseId?: string | null;
  onUploaded?: (count: number) => void;
}) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    let cancelled = false;
    const handler = () => {
      void cancelled;
    };
    window.addEventListener("mindvault-upload", handler);
    return () => {
      cancelled = true;
      window.removeEventListener("mindvault-upload", handler);
    };
  }, []);

  async function handleFiles(files: FileList | File[]) {
    const list = Array.from(files);
    if (!list.length) return;
    setError(null);
    setUploading(true);
    try {
      await uploadDocuments(list, knowledgeBaseId ?? null, (done, total) => {
        setProgress({ done, total });
      });
      toast(`Uploaded ${list.length} document${list.length > 1 ? "s" : ""}`, "success");
      onUploaded?.(list.length);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed.";
      setError(message);
      toast(message, "error");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    void handleFiles(e.dataTransfer.files);
  }

  return (
    <div>
      <label
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
          dragging ? "border-[var(--color-mv-primary)] bg-[var(--color-mv-primary-soft)]" : "border-[var(--color-mv-border)] hover:border-[var(--color-mv-primary)]"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          type="file"
          className="sr-only"
          multiple
          accept=".pdf,.docx,.txt,.md,.csv,.json"
          onChange={(e) => {
            if (e.target.files) void handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
        {uploading ? (
          <>
            <FileText size={36} className="mb-2 text-[var(--color-mv-primary)]" />
            <p className="text-sm font-medium">
              {t("documents.uploading", { done: String(progress.done), total: String(progress.total) })}
            </p>
          </>
        ) : (
          <>
            <UploadCloud size={36} className="mb-2 text-[var(--color-mv-primary)]" />
            <p className="text-sm font-medium">{t("documents.dropHere")}</p>
            <p className="mt-1 text-xs text-[var(--color-mv-muted)]">PDF · DOCX · TXT · MD · CSV · JSON</p>
          </>
        )}
      </label>
      {error && (
        <p className="mt-2 rounded-lg bg-[var(--color-mv-danger-soft)] px-3 py-2 text-sm text-[var(--color-mv-danger)]" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
