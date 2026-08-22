import { Link } from "react-router-dom";
import { useDocuments, useSystemStats, useHealth } from "../hooks/queries";
import { StatusBadge, Spinner, EmptyState } from "../components/ui";
import { formatDate } from "../lib/format";
import { t } from "../lib/i18n";
import { ShieldCheck, FileText, FolderTree, MessageSquare, GraduationCap, WifiOff } from "lucide-react";

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useSystemStats();
  const { data: health } = useHealth();
  const { data: documents } = useDocuments();

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size={24} />
      </div>
    );
  }

  const recentDocs = documents?.documents?.slice(0, 5) ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("dashboard.title")}</h1>
        <div className="flex items-center gap-1.5 rounded-full bg-[var(--color-mv-primary-soft)] px-3 py-1 text-xs font-medium text-[var(--color-mv-primary)]">
          <WifiOff size={14} />
          {t("dashboard.localMode")}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: t("dashboard.statDocuments"), value: stats?.documents ?? 0, icon: FileText, color: "text-blue-600" },
          { label: t("dashboard.statKb"), value: stats?.knowledge_bases ?? 0, icon: FolderTree, color: "text-emerald-600" },
          { label: t("dashboard.statConversations"), value: stats?.conversations ?? 0, icon: MessageSquare, color: "text-violet-600" },
          { label: t("dashboard.statStudy"), value: stats?.study_materials ?? 0, icon: GraduationCap, color: "text-amber-600" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-4">
            <div className="flex items-center gap-3">
              <div className={`rounded-lg p-2 ${color} bg-[var(--color-mv-bg)]`}>
                <Icon size={20} />
              </div>
              <div>
                <div className="text-2xl font-bold">{value}</div>
                <div className="text-xs text-[var(--color-mv-muted)]">{label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Model + Indexing status */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">{t("dashboard.modelStatus")}</h2>
          <div className="flex items-center gap-2 text-sm">
            <span className={`h-3 w-3 rounded-full ${health?.model?.provider ? "bg-[var(--color-mv-success)]" : "bg-[var(--color-mv-warning)]"}`} />
            <span className="font-medium">
              {health?.model?.provider
                ? `${t("dashboard.modelAvailable")} (${health.model.provider})`
                : t("dashboard.modelUnavailable")}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-[var(--color-mv-muted)]">
            <ShieldCheck size={13} />
            <span>{t("dashboard.offline")}</span>
          </div>
        </div>
        <div className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">{t("dashboard.indexingStatus")}</h2>
          {stats ? (
            <div className="text-sm">
              <span className="font-medium">{stats.documents_indexed}</span>
              <span className="text-[var(--color-mv-muted)]"> of </span>
              <span className="font-medium">{stats.documents}</span>
              <span className="text-[var(--color-mv-muted)]"> indexed</span>
              <div className="mt-2 h-2 w-full rounded-full bg-[var(--color-mv-border)]">
                <div
                  className="h-2 rounded-full bg-[var(--color-mv-primary)]"
                  style={{ width: `${stats.documents > 0 ? Math.round((stats.documents_indexed / stats.documents) * 100) : 0}%` }}
                />
              </div>
            </div>
          ) : (
            <span className="text-sm text-[var(--color-mv-muted)]">—</span>
          )}
        </div>
      </div>

      {/* Recent documents */}
      <div className="card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">{t("dashboard.recentDocuments")}</h2>
          <Link to="/documents" className="text-xs text-[var(--color-mv-primary)] hover:underline">
            {t("nav.documents")} →
          </Link>
        </div>
        {recentDocs.length === 0 ? (
          <EmptyState title={t("empty.noDocuments")}>
            <p className="text-sm">{t("empty.uploadCta")}</p>
            <Link to="/documents" className="btn btn-primary mt-3 inline-flex">
              {t("empty.addDocuments")}
            </Link>
          </EmptyState>
        ) : (
          <ul className="divide-y divide-[var(--color-mv-border)]">
            {recentDocs.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between py-2 text-sm">
                <span className="truncate">{doc.filename}</span>
                <span className="flex items-center gap-2 shrink-0">
                  <StatusBadge status={doc.status} />
                  <span className="text-xs text-[var(--color-mv-muted)]">{formatDate(doc.created_at)}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}