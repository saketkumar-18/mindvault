from __future__ import annotations

import logging
from dataclasses import dataclass

from mindvault.config import Settings
from mindvault.llm.base import LLMProvider
from mindvault.llm.mock import MockLLMProvider
from mindvault.llm.ollama import OllamaProvider
from mindvault.services.settings import SettingsService

logger = logging.getLogger("mindvault.llm")


@dataclass
class LLMResolution:
    provider: LLMProvider | None = None
    status: str = "unavailable"
    message: str = "No LLM provider configured."
    model: str = ""


def resolve_llm(settings: Settings, settings_svc: SettingsService | None = None) -> LLMResolution:
    """Choose an LLM provider based on configuration and availability.

    Priority: explicit setting → auto-detect (Ollama → llama.cpp → mock).
    """
    configured = settings.llm_provider.strip().lower()
    effective = settings_svc.get_effective() if settings_svc else None
    model = (effective or {}).get("ai", {}).get("model", settings.llm_model) or ""

    if configured == "mock":
        return LLMResolution(provider=MockLLMProvider(), status="mock", model=model)

    if configured in ("auto", "ollama"):
        try:
            ollama = OllamaProvider(base_url=settings.ollama_url, model=model or None)
            if ollama.available():
                models = ollama.list_models()
                if models:
                    return LLMResolution(
                        provider=ollama,
                        status="ollama",
                        model=model or str(models[0]["name"]),
                    )
                return LLMResolution(
                    status="unavailable",
                    message="Ollama is running but no models are installed. Pull a model via the Settings page.",
                    provider=None,
                    model=model,
                )
        except Exception as exc:
            logger.warning("Ollama check failed: %s", exc)

    if configured in ("auto", "llama_cpp"):
        # Remote OpenAI-compatible endpoint (cloud/demo): explicit URL wins,
        # no local model file required.
        if settings.llama_server_url:
            from mindvault.llm.llamacpp import LlamaCppProvider

            provider = LlamaCppProvider(
                server_url=settings.llama_server_url,
                model=model or None,
                api_key=settings.llama_api_key,
            )
            if provider.available():
                return LLMResolution(provider=provider, status="llama.cpp", model=model)
        if settings.llama_model_path:
            from mindvault.llm.llamacpp import LlamaCppProvider

            server_url = settings.llama_server_url or settings.ollama_url.replace(":11434", ":8080")
            provider = LlamaCppProvider(server_url=server_url, model=model or None,
                                        api_key=settings.llama_api_key)
            if provider.available():
                return LLMResolution(provider=provider, status="llama.cpp", model=model)

    if configured != "auto":
        return LLMResolution(
            status="unavailable",
            message=f"Provider '{configured}' is configured but not reachable.",
            model=model,
        )

    return LLMResolution(
        status="unavailable",
        message="No local LLM provider is available. Start Ollama, install a model, or configure a provider.",
        model=model,
    )