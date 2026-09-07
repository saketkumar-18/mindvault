"""Tests for the OpenAI-compatible remote endpoint support in LlamaCppProvider."""
from __future__ import annotations

from mindvault.llm.llamacpp import LlamaCppProvider


def test_base_url_with_v1_suffix_is_normalized():
    """https://api.tokenrouter.com/v1 must not become /v1/v1/models."""
    p = LlamaCppProvider(server_url="https://api.tokenrouter.com/v1", model="m", api_key="k")
    assert p.server_url == "https://api.tokenrouter.com"
    assert p._auth_headers() == {"Authorization": "Bearer k"}


def test_bare_host_url_unchanged():
    p = LlamaCppProvider(server_url="http://127.0.0.1:8080/")
    assert p.server_url == "http://127.0.0.1:8080"


def test_trailing_slash_v1_normalized():
    p = LlamaCppProvider(server_url="https://openrouter.ai/api/v1/")
    assert p.server_url == "https://openrouter.ai/api"


def test_blank_api_key_is_none():
    p = LlamaCppProvider(server_url="http://x", api_key="   ")
    assert p._api_key is None
    assert p._auth_headers() == {}
