from __future__ import annotations

import os
import platform
import shutil
import subprocess

from mindvault.config import Settings
from mindvault.db.models import Conversation, Document, KnowledgeBase, StudyMaterial
from mindvault.db.session import sessionmaker
from mindvault.llm.registry import resolve_llm
from mindvault.services.settings import SettingsService
from mindvault.vectorstore.base import VectorStore


class SystemService:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker,
        store: VectorStore,
        settings_svc: SettingsService,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.store = store
        self.settings_svc = settings_svc

    def _total_ram_mb(self) -> int | None:
        try:
            if platform.system() == "Windows":
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                return int(stat.ullTotalPhys / (1024 * 1024))
            with open("/proc/meminfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) // 1024
        except Exception:
            return None
        return None

    def gpu_info(self) -> list[dict[str, str]]:
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return []
        try:
            out = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            rows = []
            for line in out.stdout.strip().splitlines():
                if not line.strip():
                    continue
                name, mem, driver = [p.strip() for p in line.split(",")]
                rows.append({"name": name, "memory": mem, "driver": driver, "provider": "cuda"})
            return rows
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    def system_info(self) -> dict[str, object]:
        resolution = resolve_llm(self.settings, self.settings_svc)
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "arch": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count() or 0,
            "ram_mb": self._total_ram_mb(),
            "gpus": self.gpu_info(),
            "storage": self.storage_usage(),
            "model": {
                "status": resolution.status,
                "provider": resolution.provider.name if resolution.provider else None,
                "model": resolution.model,
                "message": resolution.message,
            },
            "offline": True,
            "external_apis": False,
        }

    def storage_usage(self) -> dict[str, object]:
        try:
            usage = shutil.disk_usage(self.settings.home_path)
        except OSError:
            return {"available_bytes": 0, "used_bytes": 0, "total_bytes": 0}
        return {
            "available_bytes": usage.free,
            "used_bytes": usage.used,
            "total_bytes": usage.total,
        }

    def stats(self) -> dict[str, object]:
        from sqlalchemy import func, select

        with self.session_factory() as session:
            doc_count = session.execute(select(func.count()).select_from(Document)).scalar_one()
            kb_count = session.execute(select(func.count()).select_from(KnowledgeBase)).scalar_one()
            conv_count = session.execute(select(func.count()).select_from(Conversation)).scalar_one()
            study_count = session.execute(select(func.count()).select_from(StudyMaterial)).scalar_one()
            total_bytes = session.execute(
                select(func.coalesce(func.sum(Document.size_bytes), 0))
            ).scalar_one()
            indexed = session.execute(
                select(func.count()).select_from(Document).where(Document.status == "indexed")
            ).scalar_one()

        resolution = resolve_llm(self.settings, self.settings_svc)
        return {
            "documents": doc_count,
            "documents_indexed": indexed,
            "knowledge_bases": kb_count,
            "conversations": conv_count,
            "study_materials": study_count,
            "document_bytes": int(total_bytes),
            "vector_chunks": self.store.count(),
            "model_status": resolution.status,
            "model_name": resolution.model,
            "offline": True,
        }

    def first_run_state(self) -> dict[str, object]:
        effective = self.settings_svc.get_effective()
        storage_ready = self.settings.home_path.exists()
        model_ready = resolve_llm(self.settings, self.settings_svc).status in ("ollama", "llama.cpp", "mock")
        with self.session_factory() as session:
            has_docs = session.query(Document).count() > 0
        return {
            "storage_ready": storage_ready,
            "model_ready": model_ready,
            "has_documents": has_docs,
            "completed": bool(effective.get("app", {}).get("first_run_completed", False)),
        }

    def mark_first_run_complete(self) -> None:
        self.settings_svc.put({"app": {"first_run_completed": True}})