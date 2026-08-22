from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mindvault import __version__
from mindvault.api.routers import (
    chat as chat_router,
)
from mindvault.api.routers import (
    documents as documents_router,
)
from mindvault.api.routers import (
    export as export_router,
)
from mindvault.api.routers import (
    health as health_router,
)
from mindvault.api.routers import (
    jobs as jobs_router,
)
from mindvault.api.routers import (
    knowledge_bases as knowledge_bases_router,
)
from mindvault.api.routers import (
    models as models_router,
)
from mindvault.api.routers import (
    search as search_router,
)
from mindvault.api.routers import (
    settings as settings_router,
)
from mindvault.api.routers import (
    study as study_router,
)
from mindvault.api.routers import (
    system as system_router,
)
from mindvault.config import Settings
from mindvault.db.migrate import run_migrations
from mindvault.db.session import create_engine_for, create_session_factory
from mindvault.embeddings.factory import create_embedding_provider
from mindvault.errors import install_exception_handlers
from mindvault.jobs.registry import JobRegistry
from mindvault.logging_setup import setup_logging
from mindvault.rag.rag_service import RAGService
from mindvault.services.chat import ChatService
from mindvault.services.container import ServiceContainer, register_container
from mindvault.services.documents import DocumentService
from mindvault.services.export import ExportService
from mindvault.services.knowledge_bases import KnowledgeBaseService
from mindvault.services.models import ModelsService
from mindvault.services.search import SearchService
from mindvault.services.settings import SettingsService
from mindvault.services.study import StudyService
from mindvault.services.system import SystemService
from mindvault.vectorstore.factory import create_vector_store


def create_app(settings: Settings | None = None, *, testing: bool = False) -> FastAPI:
    settings = settings or Settings()
    setup_logging(settings.debug)
    settings.ensure_directories()

    # Database + migrations.
    database_url = settings.resolve_database_url()
    run_migrations(database_url)
    engine = create_engine_for(database_url)
    session_factory = create_session_factory(engine)

    # Providers.
    embeddings = create_embedding_provider(settings)
    store = create_vector_store(settings, embeddings.dim)

    # Background jobs.
    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mv-job")
    jobs = JobRegistry(executor=executor)

    # Services.
    settings_svc = SettingsService(session_factory)
    search_svc = SearchService(session_factory, embeddings, store, settings_svc)
    documents_svc = DocumentService(settings, session_factory, jobs, embeddings, store, settings_svc)
    kb_svc = KnowledgeBaseService(session_factory)
    rag = RAGService(settings, search_svc, settings_svc)
    chat_svc = ChatService(session_factory, rag)
    study_svc = StudyService(settings, session_factory, rag, settings_svc)
    models_svc = ModelsService(settings, settings_svc)
    system_svc = SystemService(settings, session_factory, store, settings_svc)
    export_svc = ExportService(session_factory, settings.documents_path)

    container = ServiceContainer(
        settings=settings,
        session_factory=session_factory,
        executor=executor,
        jobs=jobs,
        embeddings=embeddings,
        store=store,
        settings_service=settings_svc,
        search_service=search_svc,
        document_service=documents_svc,
        knowledge_base_service=kb_svc,
        chat_service=chat_svc,
        study_service=study_svc,
        models_service=models_svc,
        system_service=system_svc,
        export_service=export_svc,
    )
    register_container(container)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(
        title="MindVault API",
        version=__version__,
        description="Local-first private AI knowledge assistant API.",
        lifespan=lifespan,
    )

    install_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router)
    app.include_router(system_router.router)
    app.include_router(documents_router.router)
    app.include_router(knowledge_bases_router.router)
    app.include_router(chat_router.router)
    app.include_router(search_router.router)
    app.include_router(settings_router.router)
    app.include_router(models_router.router)
    app.include_router(jobs_router.router)
    app.include_router(study_router.router)
    app.include_router(export_router.router)

    # Serve the built frontend when available (production packaging).
    web_dist = settings.web_dist
    if web_dist:
        dist = Path(web_dist)
        if dist.is_dir():
            app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")

    return app