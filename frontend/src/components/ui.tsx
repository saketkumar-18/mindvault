import type { ReactNode } from "react";

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    indexed: "badge-green",
    completed: "badge-green",
    ready: "badge-green",
    processing: "badge-blue",
    indexing: "badge-blue",
    queued: "badge-blue",
    pending: "badge-yellow",
    failed: "badge-red",
    cancelled: "badge-red",
  };
  const cls = colors[status] ?? "badge-gray";
  return <span className={`badge ${cls}`}>{status}</span>;
}

export function Spinner({ size = 18 }: { size?: number }) {
  return (
    <svg
      className="animate-spin"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      role="status"
      aria-label="Loading"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="card p-10 text-center" role="status">
      <p className="text-lg font-semibold">{title}</p>
      {children && <div className="mt-2 text-sm text-[var(--color-mv-muted)]">{children}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry, suggestion }: { message: string; onRetry?: () => void; suggestion?: string }) {
  return (
    <div className="card p-8 text-center" role="alert">
      <p className="text-base font-semibold text-[var(--color-mv-danger)]">{message}</p>
      {suggestion && <p className="mt-2 text-sm text-[var(--color-mv-muted)]">{suggestion}</p>}
      {onRetry && (
        <button className="btn btn-ghost mt-4" onClick={onRetry} type="button">
          Retry
        </button>
      )}
    </div>
  );
}

export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <div className="card w-full max-w-lg p-0" onClick={(e) => e.stopPropagation()}>
        <div className="border-b border-[var(--color-mv-border)] px-5 py-3">
          <h2 className="text-base font-semibold">{title}</h2>
        </div>
        <div className="px-5 py-4">{children}</div>
        {footer && <div className="border-t border-[var(--color-mv-border)] px-5 py-3 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} type="button">
            Cancel
          </button>
          <button className="btn btn-danger" onClick={onConfirm} type="button">
            Delete
          </button>
        </>
      }
    >
      <p className="text-sm">{message}</p>
    </Modal>
  );
}
