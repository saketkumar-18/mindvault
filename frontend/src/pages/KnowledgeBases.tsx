import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useKnowledgeBases } from "../hooks/queries";
import { api, AppApiError } from "../lib/api";
import { Modal, ConfirmDialog, EmptyState, Spinner, ErrorState } from "../components/ui";
import { useToast } from "../components/Toast";
import { t } from "../lib/i18n";
import { FolderTree, Plus, Trash2, Pencil } from "lucide-react";
import type { KnowledgeBase } from "../lib/types";

export default function KnowledgeBases() {
  const { data, isLoading, error, refetch } = useKnowledgeBases();
  const [showCreate, setShowCreate] = useState(false);
  const [showRename, setShowRename] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] });

  const kbs: KnowledgeBase[] = data?.knowledge_bases ?? [];

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      await api.post("/api/knowledge-bases", { name: name.trim(), description: description.trim() || null });
      toast("Knowledge base created.", "success");
      setName("");
      setDescription("");
      setShowCreate(false);
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Creation failed.", "error");
    }
  };

  const handleRename = async () => {
    if (!showRename || !name.trim()) return;
    try {
      await api.patch(`/api/knowledge-bases/${showRename}`, { name: name.trim() });
      toast("Renamed.", "success");
      setName("");
      setShowRename(null);
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Rename failed.", "error");
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await api.delete(`/api/knowledge-bases/${deleteId}`);
      toast("Knowledge base deleted.", "success");
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Delete failed.", "error");
    }
    setDeleteId(null);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("kbs.title")}</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)} type="button">
          <Plus size={16} />
          {t("kbs.create")}
        </button>
      </div>

      {isLoading && <Spinner />}
      {error && <ErrorState message={t("common.error")} onRetry={() => void refetch()} />}

      {!isLoading && kbs.length === 0 && (
        <EmptyState title={t("common.empty")}>
          <button className="btn btn-primary mt-3" onClick={() => setShowCreate(true)} type="button">
            {t("kbs.create")}
          </button>
        </EmptyState>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {kbs.map((kb) => (
          <div key={kb.id} className="card p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderTree size={18} className="text-[var(--color-mv-primary)]" />
                <span className="font-semibold">{kb.name}</span>
              </div>
              <div className="flex gap-1">
                <button
                  className="btn btn-ghost px-2 py-1 text-xs"
                  onClick={() => { setShowRename(kb.id); setName(kb.name); }}
                  title={t("common.rename")}
                >
                  <Pencil size={14} />
                </button>
                <button
                  className="btn btn-ghost px-2 py-1 text-xs text-[var(--color-mv-danger)]"
                  onClick={() => setDeleteId(kb.id)}
                  title={t("common.delete")}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            {kb.description && <p className="mt-1 text-xs text-[var(--color-mv-muted)]">{kb.description}</p>}
          </div>
        ))}
      </div>

      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title={t("kbs.create")}
        footer={
          <>
            <button className="btn btn-ghost" onClick={() => setShowCreate(false)} type="button">{t("common.cancel")}</button>
            <button className="btn btn-primary" onClick={handleCreate} type="button" disabled={!name.trim()}>{t("common.create")}</button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="label">{t("kbs.name")}</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
          </div>
          <div>
            <label className="label">{t("kbs.description")}</label>
            <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
        </div>
      </Modal>

      <Modal
        open={showRename !== null}
        onClose={() => setShowRename(null)}
        title={t("common.rename")}
        footer={
          <>
            <button className="btn btn-ghost" onClick={() => setShowRename(null)} type="button">{t("common.cancel")}</button>
            <button className="btn btn-primary" onClick={handleRename} type="button" disabled={!name.trim()}>{t("common.save")}</button>
          </>
        }
      >
        <div>
          <label className="label">{t("kbs.name")}</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
        </div>
      </Modal>

      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title={t("common.delete")}
        message={t("kbs.confirmDelete")}
      />
    </div>
  );
}