import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, AppApiError } from "../lib/api";
import { useFirstRun, useSystemInfo, useModels } from "../hooks/queries";
import { Spinner } from "../components/ui";
import { useToast } from "../components/Toast";
import { t } from "../lib/i18n";
import {
  ShieldCheck,
  HardDrive,
  Cpu,
  Bot,
  FlaskConical,
  UploadCloud,
  MessageSquare,
  CheckCircle2,
  ChevronRight,
} from "lucide-react";

const STEPS = [
  { id: 0, title: "welcome.storage", icon: HardDrive },
  { id: 1, title: "welcome.system", icon: Cpu },
  { id: 2, title: "welcome.model", icon: Bot },
  { id: 3, title: "welcome.testModel", icon: FlaskConical },
  { id: 4, title: "welcome.uploadDoc", icon: UploadCloud },
  { id: 5, title: "welcome.askQuestion", icon: MessageSquare },
] as const;

export default function FirstRun() {
  const { data: firstRun, isLoading: frLoading } = useFirstRun();
  const { data: systemInfo } = useSystemInfo();
  const { data: models } = useModels();
  const [step, setStep] = useState(0);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string; latency_ms: number } | null>(null);
  const [completing, setCompleting] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { toast } = useToast();

  if (frLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  if (firstRun?.completed) {
    navigate("/", { replace: true });
    return null;
  }

  async function testModel() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post<{ ok: boolean; message: string; latency_ms: number }>("/api/models/test");
      setTestResult(res);
    } catch (e) {
      setTestResult({ ok: false, message: e instanceof AppApiError ? e.message : "Test failed.", latency_ms: 0 });
    } finally {
      setTesting(false);
    }
  }

  async function complete() {
    setCompleting(true);
    try {
      await api.post("/api/system/first-run/complete");
      toast("Welcome to MindVault!", "success");
      await queryClient.invalidateQueries({ queryKey: ["first-run"] });
      navigate("/", { replace: true });
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Could not finish setup.", "error");
      setCompleting(false);
    }
  }

  const current = STEPS.find((s) => s.id === step) ?? STEPS[0];
  const StepIcon = current.icon;
  const modelReachable = models?.current.provider && models.current.provider !== "";
  const modelMessage = models?.current.message;

  return (
    <div className="min-h-screen bg-[var(--color-mv-bg)]">
      <div className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center px-4 py-10">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-mv-primary)] text-white">
            <ShieldCheck size={30} />
          </div>
          <h1 className="text-2xl font-bold">{t("welcome.title")}</h1>
          <p className="mt-2 text-sm text-[var(--color-mv-muted)]">{t("welcome.subtitle")}</p>
        </div>

        {/* Progress */}
        <div className="mt-8 flex items-center justify-between" aria-label="Setup progress">
          {STEPS.map((s) => (
            <div
              key={s.id}
              className={`flex h-2.5 flex-1 rounded-full transition-colors ${s.id <= step ? "bg-[var(--color-mv-primary)]" : "bg-[var(--color-mv-border)]"} ${s.id > 0 ? "ml-1.5" : ""}`}
            />
          ))}
        </div>

        <div className="card mt-6 p-6">
          <div className="flex items-center gap-3">
            <StepIcon size={22} className="text-[var(--color-mv-primary)]" />
            <h2 className="text-lg font-semibold">
              {t("welcome.step", { step: String(step + 1) })} — {t(current.title)}
            </h2>
          </div>

          <div className="mt-5 text-sm text-[var(--color-mv-text)]">
            {step === 0 && (
              <div className="space-y-2">
                <p>
                  Your data will be stored locally in{" "}
                  <code className="rounded bg-[var(--color-mv-bg)] px-1.5 py-0.5 text-xs">
                    {systemInfo ? "your MindVault data directory" : "~/.mindvault"}
                  </code>
                </p>
                <p className="text-[var(--color-mv-muted)]">
                  Documents, conversations, indexes and settings stay on this machine — nothing is sent to any cloud
                  service.
                </p>
                <div className="mt-3 rounded-lg bg-[var(--color-mv-primary-soft)] p-3 text-xs text-[var(--color-mv-primary)]">
                  ✅ {t("settings.localDocs")} · ✅ {t("settings.noExternal")} · ✅ {t("settings.telemetryOff")}
                </div>
              </div>
            )}

            {step === 1 && systemInfo && (
              <div className="space-y-2">
                <p>
                  <strong>{systemInfo.os}</strong> {systemInfo.os_release} · {systemInfo.arch}
                </p>
                <p>{systemInfo.cpu_count} CPU cores · {systemInfo.ram_mb ? `${Math.round(systemInfo.ram_mb / 1024)} GB RAM` : "RAM: n/a"}</p>
                {systemInfo.gpus.length > 0 ? (
                  <p className="text-[var(--color-mv-success)]">GPU: {systemInfo.gpus.map((g) => g.name).join(", ")}</p>
                ) : (
                  <p className="text-[var(--color-mv-muted)]">GPU: not detected — CPU mode will be used (fine for small models).</p>
                )}
              </div>
            )}

            {step === 2 && (
              <div className="space-y-3">
                {modelReachable ? (
                  <p className="text-[var(--color-mv-success)]">
                    ✅ {t("dashboard.modelAvailable")}: {models?.current.model || models?.current.provider}
                  </p>
                ) : (
                  <div className="space-y-2">
                    <p className="text-[var(--color-mv-warning)]">{t("model.unavailable")}</p>
                    <p className="text-[var(--color-mv-muted)]">{modelMessage || "Install a local model runtime."}</p>
                    <p className="rounded-lg bg-[var(--color-mv-bg)] p-3 text-xs">
                      Recommended: install <strong>Ollama</strong> and run{" "}
                      <code className="font-mono">ollama pull llama3.2:3b</code>. MindVault will detect it automatically.
                      <br />
                      You can also pick a provider in <strong>Settings → AI</strong> later.
                    </p>
                  </div>
                )}
              </div>
            )}

            {step === 3 && (
              <div className="space-y-3">
                <button className="btn btn-primary" onClick={() => void testModel()} disabled={testing} type="button">
                  <FlaskConical size={16} />
                  {testing ? t("common.generating") : t("settings.testModel")}
                </button>
                {testResult && (
                  <p className={`text-sm ${testResult.ok ? "text-[var(--color-mv-success)]" : "text-[var(--color-mv-danger)]"}`}>
                    {testResult.ok ? `OK (${testResult.latency_ms} ms)` : testResult.message}
                  </p>
                )}
                {!modelReachable && (
                  <p className="text-xs text-[var(--color-mv-muted)]">
                    You can still complete setup and install a model later.
                  </p>
                )}
              </div>
            )}

            {step === 4 && (
              <div className="space-y-2">
                <p>Head to <strong>Documents</strong> to upload your first document (PDF, DOCX, TXT, MD, CSV, JSON).</p>
                <p className="text-[var(--color-mv-muted)]">
                  Files are indexed locally and become searchable in moments.
                </p>
              </div>
            )}

            {step === 5 && (
              <div className="space-y-2">
                <p>Open <strong>Chat</strong> and ask a question about what you uploaded.</p>
                <p className="text-[var(--color-mv-muted)]">
                  Every answer is grounded in your documents and shows its sources.
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <button
            className="btn btn-ghost"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            type="button"
          >
            Back
          </button>

          {step < STEPS.length - 1 ? (
            <button className="btn btn-primary" onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))} type="button">
              Next
              <ChevronRight size={16} />
            </button>
          ) : (
            <button className="btn btn-primary" onClick={() => void complete()} disabled={completing} type="button">
              {completing ? <Spinner size={16} /> : <CheckCircle2 size={16} />}
              {t("welcome.complete")}
            </button>
          )}
        </div>

        <div className="mt-4 text-center">
          <button className="text-xs text-[var(--color-mv-muted)] underline" onClick={() => void complete()} type="button">
            {t("welcome.skip")}
          </button>
        </div>
      </div>
    </div>
  );
}
