import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { SystemStats, SystemInfo, ModelsResponse, SettingsResponse, HealthResponse, FirstRunState } from "../lib/types";

export const QUERY_KEYS = {
  documents: ["documents"],
  document: (id: string) => ["document", id],
  knowledgeBases: ["knowledge-bases"],
  conversations: ["conversations"],
  settings: ["settings"],
  stats: ["stats"],
  systemInfo: ["system-info"],
  models: ["models"],
  health: ["health"],
  jobs: ["jobs"],
  studyMaterials: ["study-materials"],
  firstRun: ["first-run"],
} as const;

export function useDocuments() {
  return useQuery({
    queryKey: QUERY_KEYS.documents,
    queryFn: () =>
      api.get<{ documents: import("../lib/types").DocumentInfo[]; total: number }>("/api/documents"),
    // Poll while any document is still being indexed so status badges update live.
    refetchInterval: (query) => {
      const data = query.state.data?.documents;
      if (data && data.some((d) => d.status === "pending" || d.status === "indexing")) {
        return 3000;
      }
      return false;
    },
  });
}

export function useKnowledgeBases() {
  return useQuery({ queryKey: QUERY_KEYS.knowledgeBases, queryFn: () => api.get<{ knowledge_bases: import("../lib/types").KnowledgeBase[] }>("/api/knowledge-bases") });
}

export function useConversations() {
  return useQuery({ queryKey: QUERY_KEYS.conversations, queryFn: () => api.get<{ conversations: import("../lib/types").Conversation[] }>("/api/conversations") });
}

export function useSystemStats() {
  return useQuery({ queryKey: QUERY_KEYS.stats, queryFn: () => api.get<SystemStats>("/api/system/stats") });
}

export function useSystemInfo() {
  return useQuery({ queryKey: QUERY_KEYS.systemInfo, queryFn: () => api.get<SystemInfo>("/api/system/info") });
}

export function useSettings() {
  return useQuery({ queryKey: QUERY_KEYS.settings, queryFn: () => api.get<SettingsResponse>("/api/settings") });
}

export function useModels() {
  return useQuery({ queryKey: QUERY_KEYS.models, queryFn: () => api.get<ModelsResponse>("/api/models") });
}

export function useHealth(refetchMs = 30_000) {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: () => api.get<HealthResponse>("/health"),
    refetchInterval: refetchMs,
  });
}

export function useJobs() {
  return useQuery({ queryKey: QUERY_KEYS.jobs, queryFn: () => api.get<{ jobs: import("../lib/types").JobInfo[] }>("/api/jobs"), refetchInterval: 4000 });
}

export function useFirstRun() {
  return useQuery({ queryKey: QUERY_KEYS.firstRun, queryFn: () => api.get<FirstRunState>("/api/system/first-run") });
}

export function useStudyMaterials() {
  return useQuery({ queryKey: QUERY_KEYS.studyMaterials, queryFn: () => api.get<{ materials: import("../lib/types").StudyMaterial[] }>("/api/study/materials") });
}

export function useInvalidate() {
  const queryClient = useQueryClient();
  return (keys: readonly string[][]) => {
    for (const key of keys) void queryClient.invalidateQueries({ queryKey: key });
  };
}

export function useRefreshOnMount() {
  const queryClient = useQueryClient();
  useEffect(() => {
    const handler = () => {
      void queryClient.invalidateQueries();
    };
    window.addEventListener("focus", handler);
    return () => window.removeEventListener("focus", handler);
  }, [queryClient]);
}
