export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

export function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatTime(iso?: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function truncate(text: string, length = 240): string {
  if (text.length <= length) return text;
  return text.slice(0, length).trimEnd() + "…";
}

export function statusColor(status: string): "green" | "yellow" | "blue" | "red" | "gray" {
  switch (status) {
    case "indexed":
    case "completed":
      return "green";
    case "processing":
    case "indexing":
    case "queued":
      return "blue";
    case "pending":
      return "yellow";
    case "failed":
    case "cancelled":
      return "red";
    default:
      return "gray";
  }
}
