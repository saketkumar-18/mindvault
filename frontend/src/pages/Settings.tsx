import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useSettings, useModels, useSystemInfo } from "../hooks/queries";
import { api, AppApiError } from "../lib/api";
import { Spinner, ErrorState, Modal } from "../components/ui";
import { useToast } from "../components/Toast";
import { t } from "../lib/i18n";
import { formatBytes } from "../lib/format";
import { useTheme } from "../hooks/useTheme";
import { Download, Trash2, RefreshCcw, TestTube2, Moon, Sun, Monitor } from "lucide-react";
import type { TranslationKey } from "../lib/i18n";

export default function Settings() {
  const { data, isLoading, error, refetch } = useSettings();
  const { data: models } = useModels();
  const { data: systemInfo } = useSystemInfo();
  const { theme, setTheme } = useTheme();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [ai, setAi] = useState({ provider: "auto", model: "", temperature: 0.2, max_tokens: 1024 });
  const [retrieval, setRetrieval] = useState({ top_k: 8, similarity_threshold: 0.05, chunk_size: 900, chunk_overlap: 120, max_context_chars: 9000 });
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string; latency_ms: number } | null>(null);
  const [testing, setTesting] = useState(false);
  const [clearConfirm, setClearConfirm] = useState("");
  const [showClear, setShowClear] = useState(false);

  useEffect(() => {
    if (data?.settings) {
      setAi(data.settings.ai);
      setRetrieval(data.settings.retrieval);
    }
  }, [data]);

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ["settings"] });

  async function saveSettings() {
    try {
      await api.put("/api/settings", { ai, retrieval });
      toast("Settings saved.", "success");
      invalidate();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Save failed.", "error");
    }
  }

  async function testModel() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post<{ ok: boolean; message: string; latency_ms: number; text?: string }>("/api/models/test");
      setTestResult(res);
    } catch (e) {
      setTestResult({ ok: false, message: e instanceof AppApiError ? e.message : "Test failed.", latency_ms: 0 });
    } finally {
      setTesting(false);
    }
  }

  async function clearAllData() {
    if (clearConfirm !== "DELETE") return;
    try {
      await api.delete("/api/system/data?confirm=DELETE");
      toast("All data cleared.", "success");
      setShowClear(false);
      setClearConfirm("");
      void queryClient.invalidateQueries();
      window.location.reload();
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Failed to clear data.", "error");
    }
  }

  if (isLoading) return <div className="py-20 text-center"><Spinner /></div>;
  if (error) return <ErrorState message={t("common.error")} onRetry={() => void refetch()} />;

  const themeOptions: { value: typeof theme; label: TranslationKey; icon: typeof Moon }[] = [
    { value: "light", label: "settings.theme.light", icon: Sun },
    { value: "dark", label: "settings.theme.dark", icon: Moon },
    { value: "system", label: "settings.theme.system", icon: Monitor },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-xl font-bold">{t("settings.title")}</h1>

      {/* AI */}
      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold">{t("settings.ai")}</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="label">{t("settings.model")}</label>
            <select
              className="input"
              value={ai.model}
              onChange={(e) => setAi({ ...ai, model: e.target.value })}
            >
              <option value="">{models?.current?.model || "Default"}</option>
              {(models?.candidates ?? []).map((m) => (
                <option key={`${m.provider}-${m.name}`} value={m.name}>{m.name} ({m.provider})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">{t("settings.temperature")}</label>
            <input
              type="number"
              className="input"
              step={0.1}
              min={0}
              max={2}
              value={ai.temperature}
              onChange={(e) => setAi({ ...ai, temperature: parseFloat(e.target.value) || 0 })}
            />
          </div>
        </div>
        <div className="mt-4 flex items-center gap-2">
          <button className="btn btn-primary" onClick={() => void saveSettings()} type="button">{t("common.save")}</button>
          <button className="btn btn-ghost" onClick={() => void testModel()} disabled={testing} type="button">
            <TestTube2 size={16} />
            {t("settings.testModel")}
          </button>
        </div>
        {testResult && (
          <p className={`mt-3 text-sm ${testResult.ok ? "text-[var(--color-mv-success)]" : "text-[var(--color-mv-danger)]"}`}>
            {testResult.ok ? `OK (${testResult.latency_ms}ms)` : testResult.message}
          </p>
        )}
        {models && !models.current.provider && (
          <p className="mt-3 rounded-lg bg-[var(--color-mv-warning)]/10 px-3 py-2 text-sm text-[var(--color-mv-warning)]">
            {t("model.unavailable")} — {models.current.message}
          </p>
        )}
      </section>

      {/* Model management */}
      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold">{t("settings.models")}</h2>
        {!models ? <Spinner /> : (
          <div className="space-y-2">
            <div className="text-xs text-[var(--color-mv-muted)]">
              Ollama: {models.ollama.reachable ? `${models.ollama.models.length} model(s)` : "not reachable"}
            </div>
            {models.candidates.length === 0 ? (
              <p className="text-sm text-[var(--color-mv-muted)]">{t("common.empty")}</p>
            ) : (
              <ul className="divide-y divide-[var(--color-mv-border)] text-sm">
                {models.candidates.map((m) => (
                  <li key={`${m.provider}-${m.name}`} className="flex items-center justify-between py-2">
                    <span className="font-medium">{m.name}</span>
                    <span className="text-xs text-[var(--color-mv-muted)]">
                      {m.provider} · {m.size ? formatBytes(m.size) : ""} · {m.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {models.ollama.reachable && (
              <p className="text-xs text-[var(--color-mv-muted)]">
                Install models with: <code className="font-mono">ollama pull llama3.2:3b</code>
              </p>
            )}
          </div>
        )}
      </section>

      {/* Retrieval */}
      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold">{t("settings.retrieval")}</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="label">{t("settings.topK")}</label>
            <input type="number" className="input" min={1} max={50} value={retrieval.top_k}
              onChange={(e) => setRetrieval({ ...retrieval, top_k: parseInt(e.target.value, 10) || 1 })} />
          </div>
          <div>
            <label className="label">{t("settings.threshold")}</label>
            <input type="number" className="input" step={0.01} min={0} max={1} value={retrieval.similarity_threshold}
              onChange={(e) => setRetrieval({ ...retrieval, similarity_threshold: parseFloat(e.target.value) || 0 })} />
          </div>
          <div>
            <label className="label">{t("settings.chunkSize")}</label>
            <input type="number" className="input" min={200} max={8000} value={retrieval.chunk_size}
              onChange={(e) => setRetrieval({ ...retrieval, chunk_size: parseInt(e.target.value, 10) || 200 })} />
          </div>
          <div>
            <label className="label">{t("settings.chunkOverlap")}</label>
            <input type="number" className="input" min={0} max={4000} value={retrieval.chunk_overlap}
              onChange={(e) => setRetrieval({ ...retrieval, chunk_overlap: parseInt(e.target.value, 10) || 0 })} />
          </div>
          <div className="md:col-span-2">
            <label className="label">{t("settings.maxContext")}</label>
            <input type="number" className="input" min={500} max={60000} value={retrieval.max_context_chars}
              onChange={(e) => setRetrieval({ ...retrieval, max_context_chars: parseInt(e.target.value, 10) || 500 })} />
          </div>
        </div>
        <button className="btn btn-primary mt-4" onClick={() => void saveSettings()} type="button">{t("common.save")}</button>
        {data?.rebuild_required && (
          <p className="mt-3 flex items-center gap-2 text-sm text-[var(--color-mv-warning)]">
            <RefreshCcw size={14} />
            {t("settings.indexRebuildRequired")}
          </p>
        )}
      </section>

      {/* Privacy */}
      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold">{t("settings.privacy")}</h2>
        <ul className="space-y-2 text-sm">
          <li className="flex items-center gap-2">✅ {t("settings.localDocs")}</li>
          <li className="flex items-center gap-2">✅ {t("settings.localConversations")}</li>
          <li className="flex items-center gap-2">✅ {t("settings.noExternal")}</li>
          <li className="flex items-center gap-2">✅ {t("settings.telemetryOff")}</li>
        </ul>
        {systemInfo && (
          <div className="mt-4 border-t border-[var(--color-mv-border)] pt-3 text-xs text-[var(--color-mv-muted)]">
            <p>{systemInfo.os} {systemInfo.os_release} · {systemInfo.cpu_count} CPU · {systemInfo.ram_mb ? `${Math.round(systemInfo.ram_mb / 1024)} GB RAM` : "RAM n/a"}</p>
            {systemInfo.gpus.length > 0 && <p className="mt-1">{systemInfo.gpus.map((g) => g.name).join(", ")}</p>}
            <p className="mt-1">Storage available: {formatBytes(systemInfo.storage.available_bytes)}</p>
          </div>
        )}
      </section>

      {/* Appearance */}
      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold">{t("settings.appearance")}</h2>
        <div className="flex gap-2">
          {themeOptions.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              className={`btn ${theme === value ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setTheme(value)}
              type="button"
            >
              <Icon size={16} />
              {t(label)}
            </button>
          ))}
        </div>
      </section>

      {/* Export */}
      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold">{t("settings.dataExport")}</h2>
        <div className="flex flex-wrap gap-2">
          <a className="btn btn-ghost" href="/api/export/conversations" download>
            <Download size={16} />
            {t("settings.exportConversations")}
          </a>
          <a className="btn btn-ghost" href="/api/export/knowledge-bases" download>
            <Download size={16} />
            {t("settings.exportKbs")}
          </a>
          <a className="btn btn-ghost" href="/api/export/all" download>
            <Download size={16} />
            {t("settings.exportAll")}
          </a>
        </div>
      </section>

      {/* Danger zone */}
      <section className="card border-[var(--color-mv-danger)]/30 p-5">
        <h2 className="mb-4 text-sm font-semibold text-[var(--color-mv-danger)]">{t("settings.dangerZone")}</h2>
        <button className="btn btn-danger" onClick={() => setShowClear(true)} type="button">
          <Trash2 size={16} />
          {t("settings.clearAll")}
        </button>
      </section>

      <Modal
        open={showClear}
        onClose={() => setShowClear(false)}
        title={t("settings.clearAll")}
        footer={
          <>
            <button className="btn btn-ghost" onClick={() => setShowClear(false)} type="button">{t("common.cancel")}</button>
            <button className="btn btn-danger" onClick={() => void clearAllData()} disabled={clearConfirm !== "DELETE"} type="button">
              {t("common.confirm")}
            </button>
          </>
        }
      >
        <p className="text-sm">{t("settings.clearConfirm")}</p>
        <input
          className="input mt-3"
          value={clearConfirm}
          onChange={(e) => setClearConfirm(e.target.value)}
          placeholder="DELETE"
        />
      </Modal>
    </div>
  );
}