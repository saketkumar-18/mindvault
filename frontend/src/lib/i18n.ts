export const translations = {
  en: {
    "app.name": "MindVault",
    "app.tagline": "Private AI Knowledge Assistant",
    "nav.dashboard": "Dashboard",
    "nav.documents": "Documents",
    "nav.knowledgeBases": "Knowledge Bases",
    "nav.chat": "Chat",
    "nav.search": "Search",
    "nav.study": "Study",
    "nav.settings": "Settings",
    "common.loading": "Loading…",
    "common.error": "Something went wrong.",
    "common.empty": "Nothing here yet.",
    "common.cancel": "Cancel",
    "common.delete": "Delete",
    "common.save": "Save",
    "common.confirm": "Confirm",
    "common.create": "Create",
    "common.rename": "Rename",
    "common.search": "Search",
    "common.retry": "Retry",
    "common.close": "Close",
    "common.copy": "Copy",
    "common.copied": "Copied",
    "common.generating": "Generating…",
    "common.regenerate": "Regenerate",
    "common.stop": "Stop",
    "common.status": "Status",
    "common.name": "Name",
    "common.actions": "Actions",
    "status.indexed": "Indexed",
    "status.indexing": "Indexing",
    "status.pending": "Pending",
    "status.failed": "Failed",
    "status.queued": "Queued",
    "status.processing": "Processing",
    "status.completed": "Completed",
    "status.cancelled": "Cancelled",
    "empty.noDocuments": "No documents yet",
    "empty.uploadCta": "Upload your first document to start building your private knowledge base.",
    "empty.addDocuments": "Add Documents",
    "dashboard.title": "Dashboard",
    "dashboard.statDocuments": "Documents",
    "dashboard.statKb": "Knowledge Bases",
    "dashboard.statConversations": "Conversations",
    "dashboard.statStudy": "Study Materials",
    "dashboard.modelStatus": "AI Model",
    "dashboard.modelAvailable": "Available",
    "dashboard.modelUnavailable": "Unavailable",
    "dashboard.localMode": "Local Mode",
    "dashboard.offline": "Local-only operation",
    "dashboard.recentDocuments": "Recent Documents",
    "dashboard.indexingStatus": "Indexing Status",
    "dashboard.storage": "Storage Usage",
    "documents.title": "Documents",
    "documents.upload": "Upload Documents",
    "documents.dropHere": "Drag & drop files here, or click to browse",
    "documents.uploading": "Uploading {done}/{total}…",
    "documents.view": "View",
    "documents.download": "Download",
    "documents.delete": "Delete",
    "documents.reindex": "Re-index",
    "documents.move": "Move to KB",
    "documents.rename": "Rename",
    "documents.confirmDelete": "Delete this document and all of its indexed data?",
    "documents.pages": "{count} pages",
    "documents.chunks": "{count} chunks",
    "documents.type": "Type",
    "documents.size": "Size",
    "documents.date": "Uploaded",
    "documents.errors": "Errors",
    "kbs.title": "Knowledge Bases",
    "kbs.create": "Create Knowledge Base",
    "kbs.name": "Name",
    "kbs.description": "Description",
    "kbs.documents": "Documents",
    "kbs.confirmDelete": "Delete this knowledge base? Documents will be unassigned (kept).",
    "kbs.addDocuments": "Add Documents",
    "chat.title": "Chat",
    "chat.newConversation": "New Conversation",
    "chat.placeholder": "Ask about your documents…",
    "chat.send": "Send",
    "chat.emptyState": "Ask a question about your documents.",
    "chat.sources": "Sources",
    "chat.insufficient": "I couldn't find enough information in your documents.",
    "chat.kbFilter": "Knowledge base",
    "chat.allKbs": "All knowledge bases",
    "chat.model": "Model",
    "chat.grounded": "Grounded in documents",
    "chat.ungrounded": "Not grounded in documents",
    "search.title": "Search",
    "search.placeholder": "Search your documents semantically…",
    "search.results": "Results",
    "search.noResults": "No results found.",
    "search.score": "Score {score}",
    "search.page": "Page {page}",
    "study.title": "Study",
    "study.generate": "Generate Study Material",
    "study.kind.summary": "Summary",
    "study.kind.flashcards": "Flashcards",
    "study.kind.mcq": "Multiple Choice",
    "study.kind.short_answer": "Short Answer",
    "study.kind.interview": "Interview",
    "study.kind.concepts": "Concepts",
    "study.kind.revision": "Revision Notes",
    "study.scopeDoc": "Document",
    "study.scopeKb": "Knowledge base",
    "study.history": "Generated Materials",
    "settings.title": "Settings",
    "settings.ai": "AI",
    "settings.embeddings": "Embeddings",
    "settings.retrieval": "Retrieval",
    "settings.privacy": "Privacy",
    "settings.appearance": "Appearance",
    "settings.storage": "Storage",
    "settings.model": "Model",
    "settings.temperature": "Temperature",
    "settings.topK": "Top-K",
    "settings.threshold": "Similarity threshold",
    "settings.chunkSize": "Chunk size",
    "settings.chunkOverlap": "Chunk overlap",
    "settings.maxContext": "Max context characters",
    "settings.theme": "Theme",
    "settings.theme.light": "Light",
    "settings.theme.dark": "Dark",
    "settings.theme.system": "System",
    "settings.telemetryOff": "Telemetry disabled",
    "settings.localDocs": "Documents stored locally",
    "settings.localConversations": "Conversations stored locally",
    "settings.noExternal": "External AI APIs disabled by default",
    "settings.rebuildIndex": "Rebuild Index",
    "settings.indexRebuildRequired": "Index rebuild required after embedding model change.",
    "settings.models": "Model Management",
    "settings.testModel": "Test Model",
    "settings.dataExport": "Export Data",
    "settings.exportConversations": "Export Conversations",
    "settings.exportKbs": "Export Knowledge Bases",
    "settings.exportAll": "Export All",
    "settings.dangerZone": "Danger Zone",
    "settings.clearAll": "Clear All Data",
    "settings.clearConfirm": "This permanently deletes all documents, conversations, study materials, indexes and settings. This cannot be undone. Type DELETE to confirm.",
    "settings.clearAllDone": "All data cleared.",
    "welcome.title": "Welcome to MindVault",
    "welcome.subtitle": "Your private AI knowledge assistant. Your knowledge, your machine, your privacy.",
    "welcome.step": "Step {step}",
    "welcome.storage": "Storage location is ready",
    "welcome.system": "System capabilities detected",
    "welcome.model": "Choose or install a local model",
    "welcome.modelNote": "Model selection is available in Settings.",
    "welcome.testModel": "Test the model",
    "welcome.uploadDoc": "Upload your first document",
    "welcome.askQuestion": "Ask your first question",
    "welcome.getStarted": "Get Started",
    "welcome.skip": "Skip for now",
    "welcome.complete": "Start using MindVault",
    "model.unavailable": "Your local AI model is not currently available.",
    "model.check": "Check Model",
    "model.settings": "Open Settings",
  },
} as const;
export type TranslationKey = keyof typeof translations.en;

export type Locale = keyof typeof translations;

const SUPPORTED_LOCALES: Locale[] = ["en"];

export function detectLocale(): Locale {
  const stored = localStorage.getItem("mindvault-locale");
  if (stored && stored in translations) return stored as Locale;
  const nav = (navigator.language || "en").toLowerCase();
  const base = nav.split("-")[0] as Locale;
  return SUPPORTED_LOCALES.includes(base) ? base : "en";
}

const cache = new Map<Locale, (key: TranslationKey, params?: Record<string, string | number>) => string>();

function makeT(locale: Locale) {
  const dict = translations[locale];
  return (key: TranslationKey, params?: Record<string, string | number>): string => {
    let value: string = dict[key] ?? translations.en[key] ?? String(key);
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        value = value.replace(`{${k}}`, String(v));
      }
    }
    return value;
  };
}

export function setLocale(locale: Locale): void {
  localStorage.setItem("mindvault-locale", locale);
  cache.clear();
}

export function getLocale(): Locale {
  return detectLocale();
}

export function t(key: TranslationKey, params?: Record<string, string | number>): string {
  const locale = detectLocale();
  if (!cache.has(locale)) {
    cache.set(locale, makeT(locale));
  }
  return cache.get(locale)!(key, params);
}
