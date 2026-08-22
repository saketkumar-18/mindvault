from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from sqlalchemy.orm import sessionmaker

from mindvault.config import Settings
from mindvault.embeddings.base import EmbeddingProvider
from mindvault.jobs.registry import JobRegistry
from mindvault.services.chat import ChatService
from mindvault.services.documents import DocumentService
from mindvault.services.export import ExportService
from mindvault.services.knowledge_bases import KnowledgeBaseService
from mindvault.services.models import ModelsService
from mindvault.services.search import SearchService
from mindvault.services.settings import SettingsService
from mindvault.services.study import StudyService
from mindvault.services.system import SystemService
from mindvault.vectorstore.base import VectorStore


@dataclass
class ServiceContainer:
    settings: Settings
    session_factory: sessionmaker
    executor: ThreadPoolExecutor
    jobs: JobRegistry
    embeddings: EmbeddingProvider
    store: VectorStore
    settings_service: SettingsService
    search_service: SearchService
    document_service: DocumentService
    knowledge_base_service: KnowledgeBaseService
    chat_service: ChatService
    study_service: StudyService
    models_service: ModelsService
    system_service: SystemService
    export_service: ExportService


_instance: ServiceContainer | None = None


def register_container(container: ServiceContainer) -> None:
    global _instance
    _instance = container


def get_container() -> ServiceContainer:
    global _instance
    if _instance is None:
        raise RuntimeError("Service container not initialized.")
    return _instance