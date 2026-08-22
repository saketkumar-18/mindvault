export interface DocumentInfo {
  id: string;
  filename: string;
  extension: string;
  mime_type?: string | null;
  size_bytes: number;
  content_hash?: string;
  status: string;
  error?: string | null;
  page_count?: number | null;
  chunk_count: number;
  knowledge_base_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
}

export interface ChunkInfo {
  id: string;
  ordinal: number;
  text: string;
  page_start?: number | null;
  page_end?: number | null;
  section?: string | null;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
}

export interface KnowledgeBaseDetail extends KnowledgeBase {
  statistics: {
    document_count: number;
    chunk_count: number;
    total_bytes: number;
  };
}

export interface SourceCitation {
  chunk_id: string;
  document_id: string;
  filename: string;
  score: number;
  page_start?: number | null;
  page_end?: number | null;
  section?: string | null;
  excerpt: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  model?: string | null;
  created_at?: string | null;
}

export interface Conversation {
  id: string;
  title: string;
  knowledge_base_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  message_count?: number;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  score: number;
  text: string;
  page_start?: number | null;
  page_end?: number | null;
  section?: string | null;
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface SettingsResponse {
  settings: {
    ai: { provider: string; model: string; temperature: number; max_tokens: number; context_size: number };
    embeddings: { provider: string; model: string; dim: number; rebuild_required?: boolean };
    retrieval: {
      top_k: number;
      similarity_threshold: number;
      chunk_size: number;
      chunk_overlap: number;
      max_context_chars: number;
      rerank_enabled: boolean;
    };
    privacy: { telemetry_enabled: boolean; external_apis_enabled: boolean };
    appearance: { theme: string };
    storage: Record<string, unknown>;
  };
  rebuild_required: boolean;
}

export interface ModelInfo {
  name: string;
  provider: string;
  size?: number;
  status: string;
}

export interface ModelsResponse {
  current: { provider: string; model: string; message: string };
  candidates: ModelInfo[];
  ollama: { reachable: boolean; models: ModelInfo[] };
  llama_cpp: { configured: boolean; path?: string | null };
}

export interface SystemInfo {
  os: string;
  os_release: string;
  arch: string;
  python_version: string;
  cpu_count: number;
  ram_mb: number | null;
  gpus: { name: string; memory: string; driver: string; provider: string }[];
  storage: { available_bytes: number; used_bytes: number; total_bytes: number };
  model: { status: string; provider?: string | null; model?: string; message: string };
  offline: boolean;
  external_apis: boolean;
}

export interface SystemStats {
  documents: number;
  documents_indexed: number;
  knowledge_bases: number;
  conversations: number;
  study_materials: number;
  document_bytes: number;
  vector_chunks: number;
  model_status: string;
  model_name: string;
  offline: boolean;
}

export interface JobInfo {
  id: string;
  kind: string;
  status: string;
  progress: number;
  message: string;
  document_id?: string | null;
  error?: string | null;
  created_at: string;
  finished_at?: string | null;
}

export interface FirstRunState {
  storage_ready: boolean;
  model_ready: boolean;
  has_documents: boolean;
  completed: boolean;
}

export interface HealthResponse {
  status: string;
  database: boolean;
  vector_store: number;
  model: { provider: string; model: string; message: string };
}

export interface StudyMaterial {
  id: string;
  kind: string;
  title: string;
  document_id?: string | null;
  created_at?: string | null;
}
