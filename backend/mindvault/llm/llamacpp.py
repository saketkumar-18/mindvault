from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx

from mindvault.llm.base import InterruptedGeneration, LLMRequest


class LlamaCppProvider:
    """llama.cpp server via the OpenAI-compatible ``/v1/chat/completions`` endpoint.

    Assumes ``llama-server`` is running locally (e.g. ``llama-server -m model.gguf --host 127.0.0.1``).
    GGUF models are loaded directly by the server; no model weights are bundled
    in MindVault.
    """

    name = "llama.cpp"

    def __init__(self, server_url: str = "http://127.0.0.1:8080", model: str | None = None,
                 api_key: str | None = None) -> None:
        # Accept both a bare host (llama-server) and an OpenAI-compatible base
        # URL ending in /v1 (vLLM, OpenRouter, ...) — the provider itself
        # appends /v1/models and /v1/chat/completions.
        server_url = server_url.rstrip("/")
        if server_url.endswith("/v1"):
            server_url = server_url[: -len("/v1")]
        self.server_url = server_url
        self._model = model
        self._api_key = (api_key or "").strip() or None
        self._http = httpx.Client(timeout=httpx.Timeout(connect=10.0, read=300.0, write=60.0, pool=5.0))

    @property
    def model(self) -> str:
        return self._model or ""

    # -- interface --------------------------------------------------------
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

    def available(self) -> bool:
        try:
            r = self._http.get(f"{self.server_url}/v1/models", timeout=10.0,
                               headers=self._auth_headers())
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[dict[str, object]]:
        try:
            r = self._http.get(f"{self.server_url}/v1/models", timeout=15.0,
                               headers=self._auth_headers())
            r.raise_for_status()
            data = r.json()
            models = data.get("data", data)
            return [
                {
                    "name": m.get("id", m.get("model", "unknown")),
                    "provider": "llama.cpp",
                    "status": "available",
                }
                for m in (models if isinstance(models, list) else [])
            ]
        except httpx.HTTPError:
            return []

    def generate(self, request: LLMRequest) -> Iterator[str]:
        if not self.available():
            raise InterruptedGeneration("llama.cpp server is not reachable.")

        messages: list[dict[str, str]] = [
            {"role": msg["role"], "content": msg["content"]} for msg in request.messages
        ]
        if request.system:
            messages.insert(0, {"role": "system", "content": request.system})

        payload: dict[str, Any] = {
            "messages": messages,
            "stream": True,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if self._model:
            payload["model"] = self._model
        if request.stop:
            payload["stop"] = request.stop

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

        try:
            with self._http.stream(
                "POST", f"{self.server_url}/v1/chat/completions", json=payload,
                headers=headers, timeout=300.0
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    # some providers emit keep-alive/error frames with empty choices
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        yield token
        except httpx.HTTPError as exc:
            raise InterruptedGeneration("llama.cpp server returned an error.") from exc