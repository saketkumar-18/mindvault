import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useConversations, useKnowledgeBases } from "../hooks/queries";
import { api, AppApiError, streamChat } from "../lib/api";
import { SourceList } from "../components/SourceList";
import { Spinner, ConfirmDialog } from "../components/ui";
import { useToast } from "../components/Toast";
import { t } from "../lib/i18n";
import { Send, Square, RotateCcw, Copy, Check, Trash2, Plus } from "lucide-react";
import type { Conversation, SourceCitation } from "../lib/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  model?: string | null;
  streaming?: boolean;
}

export default function Chat() {
  const { data: conversations } = useConversations();
  const { data: kbs } = useKnowledgeBases();
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [kbId, setKbId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [copied, setCopied] = useState<string | null>(null);

  const invalidateConversations = () => void queryClient.invalidateQueries({ queryKey: ["conversations"] });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function openConversation(id: string) {
    setActiveConv(id);
    setStreaming(false);
    try {
      const detail = await api.get<{ messages: import("../lib/types").Message[] }>(`/api/conversations/${id}`);
      setMessages(
        detail.messages.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          sources: m.sources as SourceCitation[] | undefined,
          model: m.model,
        })),
      );
    } catch {
      setMessages([]);
    }
  }

  async function newConversation() {
    setActiveConv(null);
    setMessages([]);
    setInput("");
  }

  async function send(regenerate = false) {
    const question = (input || "").trim();
    if (!question || streaming) return;
    setInput("");
    setStreaming(true);

    if (!activeConv) {
      try {
        const created = await api.post<Conversation>("/api/conversations", { title: question.slice(0, 60), knowledge_base_id: kbId });
        setActiveConv(created.id);
        invalidateConversations();
      } catch (e) {
        toast(e instanceof AppApiError ? e.message : "Failed to create conversation.", "error");
        setStreaming(false);
        return;
      }
    }

    const conversationId = activeConv!;
    const userMessage: ChatMessage = { id: `user-${Date.now()}`, role: "user", content: question };
    const assistantMessage: ChatMessage = { id: `assistant-${Date.now()}`, role: "assistant", content: "", streaming: true };
    setMessages((prev) => (regenerate ? [...prev, userMessage] : [...prev, userMessage, assistantMessage]));

    abortRef.current = new AbortController();
    await streamChat(
      { message: question, conversation_id: conversationId, knowledge_base_id: kbId },
      {
        onToken: (text) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.streaming) last.content += text;
            return next;
          });
        },
        onSources: (sources) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last) last.sources = sources as SourceCitation[];
            return next;
          });
        },
        onDone: () => {
          setMessages((prev) => prev.map((m) => (m.streaming ? { ...m, streaming: false } : m)));
          setStreaming(false);
          invalidateConversations();
        },
        onError: (message, suggestion) => {
          setMessages((prev) => prev.map((m) => (m.streaming ? { ...m, streaming: false, content: m.content || message } : m)));
          setStreaming(false);
          toast(suggestion || message, "error");
          invalidateConversations();
        },
      },
      abortRef.current.signal,
    );
    setStreaming(false);
  }

  async function regenerateLast() {
    if (!activeConv || streaming) return;
    setStreaming(true);
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser) {
      setStreaming(false);
      return;
    }
    // Keep only messages up to the last user turn (drop trailing assistants).
    const lastUserIndex = messages.findIndex((m) => m.id === lastUser.id);
    setMessages((prev) => [...prev.slice(0, lastUserIndex + 1)]);

    const assistantMessage: ChatMessage = { id: `assistant-${Date.now()}`, role: "assistant", content: "", streaming: true };
    setMessages((prev) => [...prev, assistantMessage]);

    abortRef.current = new AbortController();
    try {
      const res = await fetch(`/api/chat/${activeConv}/regenerate?stream=true`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
        signal: abortRef.current.signal,
      });
      if (!res.ok || !res.body) throw new Error("Regenerate failed");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx: number;
        while ((idx = buffer.indexOf("\n\n")) !== -1) {
          const line = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          const raw = trimmed.slice(6);
          if (!raw || raw === "{}") continue;
          try {
            const event = JSON.parse(raw) as Record<string, unknown>;
            if (event.type === "token") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last && last.streaming) last.content += String(event.text ?? "");
                return next;
              });
            } else if (event.type === "sources") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last) last.sources = event.sources as SourceCitation[];
                return next;
              });
            } else if (event.type === "done") {
              setMessages((prev) => prev.map((m) => (m.streaming ? { ...m, streaming: false } : m)));
              invalidateConversations();
            }
          } catch {
            /* ignore */
          }
        }
      }
    } catch {
      setMessages((prev) => prev.map((m) => (m.streaming ? { ...m, streaming: false } : m)));
    }
    setStreaming(false);
  }

  const stop = () => abortRef.current?.abort();

  async function copyText(id: string, text: string) {
    await navigator.clipboard.writeText(text);
    setCopied(id);
    window.setTimeout(() => setCopied(null), 1500);
  }

  async function deleteConversation(id: string) {
    try {
      await api.delete(`/api/conversations/${id}`);
      if (activeConv === id) {
        setActiveConv(null);
        setMessages([]);
      }
      invalidateConversations();
      toast("Conversation deleted.", "success");
    } catch (e) {
      toast(e instanceof AppApiError ? e.message : "Delete failed.", "error");
    }
    setConfirmDelete(null);
  }

  const convs = conversations?.conversations ?? [];

  return (
    <div className="flex h-[calc(100vh-7.5rem)] gap-4">
      <h1 className="sr-only">{t("chat.title")}</h1>
      {/* Conversation list */}
      <aside className="hidden w-64 shrink-0 flex-col overflow-y-auto rounded-xl border border-[var(--color-mv-border)] bg-[var(--color-mv-surface)] lg:flex">
        <button className="btn btn-primary m-3 justify-center" onClick={newConversation} type="button">
          <Plus size={16} />
          {t("chat.newConversation")}
        </button>
        <div className="flex-1 space-y-1 px-2">
          {convs.map((c) => (
            <div
              key={c.id}
              className={`group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm ${
                activeConv === c.id ? "bg-[var(--color-mv-primary-soft)] text-[var(--color-mv-primary)]" : "hover:bg-[var(--color-mv-bg)]"
              }`}
              onClick={() => void openConversation(c.id)}
            >
              <span className="truncate">{c.title}</span>
              <button
                className="opacity-0 group-hover:opacity-100 p-1 text-[var(--color-mv-muted)] hover:text-[var(--color-mv-danger)]"
                onClick={(e) => {
                  e.stopPropagation();
                  setConfirmDelete(c.id);
                }}
                aria-label={t("common.delete")}
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex min-w-0 flex-1 flex-col rounded-xl border border-[var(--color-mv-border)] bg-[var(--color-mv-surface)]">
        {/* Controls */}
        <div className="flex items-center gap-3 border-b border-[var(--color-mv-border)] px-4 py-2.5">
          <label className="text-xs font-medium text-[var(--color-mv-muted)]">{t("chat.kbFilter")}</label>
          <select className="input w-auto text-xs" value={kbId ?? ""} onChange={(e) => setKbId(e.target.value || null)}>
            <option value="">{t("chat.allKbs")}</option>
            {(kbs?.knowledge_bases ?? []).map((kb) => (
              <option key={kb.id} value={kb.id}>{kb.name}</option>
            ))}
          </select>
          {activeConv && (
            <button className="btn btn-ghost ml-auto px-2 py-1 text-xs" onClick={() => void regenerateLast()} disabled={streaming} type="button">
              <RotateCcw size={14} />
              {t("common.regenerate")}
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center text-[var(--color-mv-muted)]">
              <p className="text-sm">{t("chat.emptyState")}</p>
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] ${m.role === "user" ? "bg-[var(--color-mv-primary)] text-white" : "bg-[var(--color-mv-bg)]"} rounded-xl px-4 py-3`}>
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.content || (m.streaming ? t("common.generating") : "")}</div>
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 border-t border-[var(--color-mv-border)] pt-2">
                    <div className="mb-1 text-xs font-semibold text-[var(--color-mv-muted)]">{t("chat.sources")}</div>
                    <SourceList sources={m.sources} />
                  </div>
                )}
                {m.role === "assistant" && !m.streaming && m.content && (
                  <div className="mt-2 flex items-center gap-1">
                    <button
                      className="flex items-center gap-1 text-xs text-[var(--color-mv-muted)] hover:text-[var(--color-mv-primary)]"
                      onClick={() => void copyText(m.id, m.content)}
                      type="button"
                    >
                      {copied === m.id ? <Check size={12} /> : <Copy size={12} />}
                      {copied === m.id ? t("common.copied") : t("common.copy")}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {streaming && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-xl bg-[var(--color-mv-bg)] px-4 py-3 text-sm text-[var(--color-mv-muted)]">
                <Spinner size={14} />
                {t("common.generating")}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Composer */}
        <div className="border-t border-[var(--color-mv-border)] p-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
            className="flex gap-2"
          >
            <textarea
              className="input min-h-20 flex-1 resize-none"
              placeholder={t("chat.placeholder")}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
              disabled={streaming}
              aria-label={t("chat.placeholder")}
            />
            {streaming ? (
              <button className="btn btn-danger" onClick={stop} type="button" aria-label={t("common.stop")}>
                <Square size={16} />
              </button>
            ) : (
              <button className="btn btn-primary" type="submit" disabled={!input.trim()} aria-label={t("chat.send")}>
                <Send size={16} />
              </button>
            )}
          </form>
        </div>
      </div>

      <ConfirmDialog
        open={confirmDelete !== null}
        onClose={() => setConfirmDelete(null)}
        onConfirm={() => confirmDelete && void deleteConversation(confirmDelete)}
        title={t("common.delete")}
        message="Delete this conversation?"
      />
    </div>
  );
}