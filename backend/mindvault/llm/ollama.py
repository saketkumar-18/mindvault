from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx

from mindvault.llm.base import InterruptedGeneration, LLMRequest


class OllamaProvider:
    """Local Ollama server via its REST API.

    Connects to ``http://127.0.0.1:11434`` by default. No external network
    requests are made; the server is expected to run locally.
    """

    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._model = model
        self._http = httpx.Client(timeout=httpx.Timeout(connect=3.0, read=300.0, write=60.0, pool=5.0))

    @property
    def model(self) -> str:
        if self._model:
            return self._model
        models = self.list_models()
        if models:
            return str(models[0]["name"])
        return ""

    # -- interface --------------------------------------------------------
    def available(self) -> bool:
        try:
            r = self._http.get(f"{self.base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[dict[str, object]]:
        try:
            r = self._http.get(f"{self.base_url}/api/tags", timeout=5.0)
            r.raise_for_status()
            data = r.json()
            return [
                {"name": m["name"], "size": m.get("size", 0), "provider": "ollama", "status": "available"}
                for m in data.get("models", [])
            ]
        except httpx.HTTPError:
            return []

    def generate(self, request: LLMRequest) -> Iterator[str]:
        """Stream tokens from the Ollama chat endpoint."""
        if not self.available():
            raise InterruptedGeneration("Ollama server is not reachable.")

        model = self.model or "llama3.2:3b"
        messages: list[dict[str, str]] = [
            {"role": msg["role"], "content": msg["content"]} for msg in request.messages
        ]
        if request.system:
            messages.insert(0, {"role": "system", "content": request.system})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.stop:
            payload["options"]["stop"] = request.stop

        try:
            with self._http.stream("POST", f"{self.base_url}/api/chat", json=payload, timeout=300.0) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("done"):
                        break
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
        except httpx.HTTPError as exc:
            raise InterruptedGeneration("Ollama server returned an error.") from exc