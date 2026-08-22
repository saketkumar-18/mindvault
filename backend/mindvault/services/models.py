from __future__ import annotations

from pathlib import Path

from mindvault.config import Settings
from mindvault.llm.registry import resolve_llm
from mindvault.services.settings import SettingsService


class ModelsService:
    """Manage and inspect local LLM providers and their models."""

    def __init__(self, settings: Settings, settings_svc: SettingsService) -> None:
        self.settings = settings
        self.settings_svc = settings_svc

    def list_models(self) -> dict[str, object]:
        resolution = resolve_llm(self.settings, self.settings_svc)

        # Collect candidates from all available providers.
        candidates: list[dict[str, object]] = []
        ollama_models: list[dict[str, object]] = []
        from mindvault.llm.ollama import OllamaProvider

        ollama = OllamaProvider(base_url=self.settings.ollama_url)
        if ollama.available():
            ollama_models = ollama.list_models()
            for m in ollama_models:
                m["provider"] = "ollama"
            candidates.extend(ollama_models)

        if self.settings.llama_model_path:
            p = Path(self.settings.llama_model_path)
            candidates.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "size": p.stat().st_size if p.exists() else 0,
                    "provider": "llama.cpp",
                    "status": "available" if p.exists() else "not found",
                }
            )

        return {
            "current": {
                "provider": resolution.status,
                "model": resolution.model,
                "message": resolution.message,
            },
            "candidates": candidates,
            "ollama": {
                "reachable": ollama.available(),
                "models": ollama_models,
            },
            "llama_cpp": {
                "configured": bool(self.settings.llama_model_path),
                "path": self.settings.llama_model_path,
            },
        }

    def test_model(self, provider: str | None = None, model: str | None = None) -> dict[str, object]:
        import time

        from mindvault.llm.base import LLMRequest

        resolution = resolve_llm(self.settings, self.settings_svc)
        if resolution.provider is None:
            return {"ok": False, "message": resolution.message, "latency_ms": 0}
        llm = resolution.provider
        start = time.perf_counter()
        try:
            text = "".join(
                llm.generate(
                    LLMRequest(
                        messages=[{"role": "user", "content": "Reply with the single word: OK"}],
                        max_tokens=16,
                        temperature=0.1,
                    )
                )
            )
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "ok": True,
                "text": text.strip(),
                "model": resolution.model,
                "provider": llm.name,
                "latency_ms": latency,
            }
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "ok": False,
                "message": str(exc),
                "latency_ms": latency,
                "model": resolution.model,
                "provider": llm.name,
            }