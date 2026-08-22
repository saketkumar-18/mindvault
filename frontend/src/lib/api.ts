import type { DocumentInfo, SearchResponse } from "../lib/types";

export interface ChatEventMap {
  onSources?: (sources: unknown[]) => void;
  onToken?: (text: string) => void;
  onDone?: (payload: Record<string, unknown>) => void;
  onError?: (message: string, suggestion?: string) => void;
}

export interface ApiError extends Error {
  status?: number;
  code?: string;
  suggestion?: string;
}

export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export class AppApiError extends Error implements ApiError {
  status?: number;
  code?: string;
  suggestion?: string;

  constructor(message: string, opts: { status?: number; code?: string; suggestion?: string } = {}) {
    super(message);
    this.status = opts.status;
    this.code = opts.code;
    this.suggestion = opts.suggestion;
  }
}

async function parseError(res: Response): Promise<AppApiError> {
  let message = `Request failed (${res.status}).`;
  let code: string | undefined;
  let suggestion: string | undefined;
  try {
    const body = await res.json();
    const err = body?.error;
    if (err) {
      message = err.message ?? message;
      code = err.code;
      suggestion = err.suggestion;
    }
  } catch {
    /* not JSON */
  }
  return new AppApiError(message, { status: res.status, code, suggestion });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw await parseError(res);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export async function uploadDocuments(
  files: File[],
  knowledgeBaseId: string | null,
  onProgress?: (done: number, total: number) => void,
): Promise<DocumentInfo[]> {
  const created: DocumentInfo[] = [];
  let done = 0;
  const total = files.length;

  for (const file of files) {
    const form = new FormData();
    form.append("file", file);
    if (knowledgeBaseId) form.append("knowledge_base_id", knowledgeBaseId);

    const res = await fetch(`${API_BASE}/api/documents`, { method: "POST", body: form });
    done += 1;
    onProgress?.(done, total);
    if (!res.ok) {
      const err = await parseError(res);
      throw err;
    }
    const data = await res.json();
    created.push({ ...(data as DocumentInfo), filename: file.name, size_bytes: file.size });
  }
  return created;
}

export function streamChat(
  payload: { message: string; conversation_id?: string; knowledge_base_id?: string | null },
  handlers: ChatEventMap,
  signal?: AbortSignal,
): Promise<void> {
  return new Promise((resolve, reject) => {
    fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    })
      .then(async (res) => {
        if (!res.ok || !res.body) {
          throw await parseError(res);
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        const processLine = (line: string) => {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) return;
          const raw = trimmed.slice(6);
          if (!raw || raw === "{}") return;
          try {
            const event = JSON.parse(raw) as Record<string, unknown>;
            switch (event.type) {
              case "sources":
                handlers.onSources?.(Array.isArray(event.sources) ? event.sources : []);
                break;
              case "token":
                handlers.onToken?.(String(event.text ?? ""));
                break;
              case "done":
                handlers.onDone?.(event);
                resolve();
                break;
              case "error":
                handlers.onError?.(String(event.message ?? "Unknown error"), event.suggestion ? String(event.suggestion) : undefined);
                resolve();
                break;
            }
          } catch {
            /* skip malformed */
          }
        };

        const loop = async () => {
          for (;;) {
            const { done, value } = await reader.read();
            if (done) {
              resolve();
              break;
            }
            buffer += decoder.decode(value, { stream: true });
            let idx: number;
            while ((idx = buffer.indexOf("\n\n")) !== -1) {
              const line = buffer.slice(0, idx);
              buffer = buffer.slice(idx + 2);
              processLine(line);
            }
          }
        };
        void loop();
      })
      .catch((err) => {
        if (err?.name === "AbortError") {
          resolve();
        } else {
          reject(err instanceof AppApiError ? err : new AppApiError(String(err?.message ?? err)));
        }
      });
  });
}

export function searchDocuments(query: string, filters?: {
  knowledge_base_id?: string | null;
  document_ids?: string[];
  file_types?: string[];
  global_scope?: boolean;
}): Promise<SearchResponse> {
  return api.post<SearchResponse>("/api/search", { query, ...filters });
}
