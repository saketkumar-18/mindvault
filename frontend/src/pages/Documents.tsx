import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useDocuments, useKnowledgeBases } from "../hooks/queries";
import { api, AppApiError } from "../lib/api";
import { FileDropzone } from "../components/FileDropzone";
import { DocumentViewer } from "../components/DocumentViewer";
import { StatusBadge, Modal, ConfirmDialog, EmptyState, Spinner, ErrorState } from "../components/ui";
import { useToast } from "../components/Toast";
import { formatBytes, formatDate } from "../lib/format";
import { t } from "../lib/i18n";
import { UploadCloud, Trash2, RotateCw, Download, FolderTree, Eye } from "lucide-react";
import type { DocumentInfo } from "../lib/types";

export default function Documents() {
  const { data, isLoading, error, refetch } = useDocuments();
  const { data: kbs } = useKnowledgeBases();
  const [showUpload, setShowUpload] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [moveId, setMoveId] = useState<string | null>(null);
  const [viewId, setViewId] = useState<DocumentInfo | null>(null);
  const [reindexing, setReindexing] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ["documents"] });
  }, [queryClient]);

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await api.delete(`/api/documents/${deleteId}`);
      toast("Document deleted.", "success");
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Delete failed.", "error");
    }
    setDeleteId(null);
  };

  const handleMove = async (targetKbId: string | null) => {
    if (!moveId) return;
    try {
      const kbId = targetKbId ?? "";
      if (kbId) {
        await api.post(`/api/knowledge-bases/${kbId}/documents`, { document_ids: [moveId] });
      } else {
        await api.patch(`/api/documents/${moveId}`, { knowledge_base_id: null });
      }
      toast("Document moved.", "success");
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Move failed.", "error");
    }
    setMoveId(null);
  };

  const handleReindex = async (docId: string) => {
    setReindexing(docId);
    try {
      await api.post(`/api/documents/${docId}/reindex`);
      toast("Re-indexing started.", "success");
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Re-index failed.", "error");
    }
    setReindexing(null);
  };

  const docs: DocumentInfo[] = data?.documents ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("documents.title")}</h1>
        <button className="btn btn-primary" onClick={() => setShowUpload(!showUpload)} type="button">
          <UploadCloud size={16} />
          {t("documents.upload")}
        </button>
      </div>

      {showUpload && (
        <FileDropzone onUploaded={() => { setShowUpload(false); invalidate(); }} />
      )}

      {isLoading && <Spinner />}
      {error && <ErrorState message={t("common.error")} onRetry={() => void refetch()} />}

      {!isLoading && docs.length === 0 && (
        <EmptyState title={t("empty.noDocuments")}>
          <p className="text-sm">{t("empty.uploadCta")}</p>
          <button className="btn btn-primary mt-3" onClick={() => setShowUpload(true)} type="button">
            {t("empty.addDocuments")}
          </button>
        </EmptyState>
      )}

      {docs.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-mv-border)]">
                <th className="px-4 py-2 text-left font-medium text-[var(--color-mv-muted)]">{t("common.name")}</th>
                <th className="px-4 py-2 text-left font-medium text-[var(--color-mv-muted)] hidden md:table-cell">{t("documents.type")}</th>
                <th className="px-4 py-2 text-left font-medium text-[var(--color-mv-muted)] hidden md:table-cell">{t("documents.size")}</th>
                <th className="px-4 py-2 text-left font-medium text-[var(--color-mv-muted)]">{t("common.status")}</th>
                <th className="px-4 py-2 text-left font-medium text-[var(--color-mv-muted)] hidden md:table-cell">{t("documents.date")}</th>
                <th className="px-4 py-2 text-right font-medium text-[var(--color-mv-muted)]">{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id} className="border-b border-[var(--color-mv-border)] hover:bg-[var(--color-mv-bg)]">
                  <td className="max-w-40 truncate px-4 py-3 font-medium">{doc.filename}</td>
                  <td className="px-4 py-3 text-[var(--color-mv-muted)] hidden md:table-cell">.{doc.extension}</td>
                  <td className="px-4 py-3 text-[var(--color-mv-muted)] hidden md:table-cell">{formatBytes(doc.size_bytes)}</td>
                  <td className="px-4 py-3"><StatusBadge status={doc.status} /></td>
                  <td className="px-4 py-3 text-[var(--color-mv-muted)] hidden md:table-cell">{formatDate(doc.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        className="btn btn-ghost px-2 py-1 text-xs"
                        onClick={() => setViewId(doc)}
                        title={t("documents.view")}
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        className="btn btn-ghost px-2 py-1 text-xs"
                        onClick={() => setMoveId(doc.id)}
                        title={t("documents.move")}
                      >
                        <FolderTree size={14} />
                      </button>
                      <button
                        className="btn btn-ghost px-2 py-1 text-xs"
                        onClick={() => void handleReindex(doc.id)}
                        disabled={reindexing === doc.id}
                        title={t("documents.reindex")}
                      >
                        <RotateCw size={14} className={reindexing === doc.id ? "animate-spin" : ""} />
                      </button>
                      <a
                        className="btn btn-ghost px-2 py-1 text-xs"
                        href={`/api/documents/${doc.id}/download`}
                        download={doc.filename}
                        title={t("documents.download")}
                      >
                        <Download size={14} />
                      </a>
                      <button
                        className="btn btn-ghost px-2 py-1 text-xs text-[var(--color-mv-danger)]"
                        onClick={() => setDeleteId(doc.id)}
                        title={t("documents.delete")}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title={t("documents.delete")}
        message={t("documents.confirmDelete")}
      />

      <Modal
        open={moveId !== null}
        onClose={() => setMoveId(null)}
        title={t("documents.move")}
        footer={
          <>
            <button className="btn btn-ghost" onClick={() => setMoveId(null)} type="button">{t("common.cancel")}</button>
          </>
        }
      >
        <div className="space-y-2">
          <button className="btn btn-ghost w-full justify-start text-left" onClick={() => void handleMove(null)} type="button">
            No knowledge base
          </button>
          {(kbs?.knowledge_bases ?? []).map((kb) => (
            <button
              key={kb.id}
              className="btn btn-ghost w-full justify-start text-left text-sm"
              onClick={() => void handleMove(kb.id)}
              type="button"
            >
              {kb.name}
            </button>
          ))}
        </div>
      </Modal>

      {viewId && (
        <DocumentViewer documentId={viewId.id} filename={viewId.filename} onClose={() => setViewId(null)} />
      )}
    </div>
  );
}