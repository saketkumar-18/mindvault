import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";

interface ToastItem {
  id: number;
  message: string;
  kind: "success" | "error" | "info";
}

interface ToastContextValue {
  toast: (message: string, kind?: ToastItem["kind"]) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => undefined });

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const toast = useCallback((message: string, kind: ToastItem["kind"] = "info") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, message, kind }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`card px-4 py-2 text-sm shadow-lg ${
              t.kind === "error" ? "text-[var(--color-mv-danger)]" : t.kind === "success" ? "text-[var(--color-mv-success)]" : ""
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
