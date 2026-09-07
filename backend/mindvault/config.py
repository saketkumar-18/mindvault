from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Everything is driven by environment variables (prefix ``MV_``).
    No secrets are ever required: MindVault is fully functional offline.
    """

    model_config = SettingsConfigDict(
        env_prefix="MV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    home: str = Field(default_factory=lambda: str(Path.home() / ".mindvault"))
    database_url: str | None = None
    documents_dir: str | None = None
    index_dir: str | None = None

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    web_dist: str | None = None
    host: str = "127.0.0.1"
    port: int = 8000

    max_upload_bytes: int = 100 * 1024 * 1024
    allowed_extensions: str = "pdf,docx,txt,md,csv,json"
    max_pages: int = 2000

    ollama_url: str = "http://127.0.0.1:11434"
    llm_provider: str = "auto"  # auto | ollama | llama_cpp | mock
    llm_model: str = ""
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024
    llama_model_path: str | None = None
    llama_ctx_size: int = 4096
    # OpenAI-compatible remote endpoint for the llama.cpp provider (cloud demo).
    # When set, it overrides the derived localhost:8080 server URL, and the key
    # is sent as a Bearer header. Works with llama-server, vLLM, OpenRouter,
    # Tokenrouter and any /v1/chat/completions endpoint.
    llama_server_url: str | None = None
    llama_api_key: str | None = None

    embedding_provider: str = "auto"  # auto | sentence-transformers | hash
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 8
    similarity_threshold: float = 0.05
    max_context_chars: int = 9000
    rerank_enabled: bool = False

    debug: bool = False

    @property
    def home_path(self) -> Path:
        return Path(self.home).expanduser()

    @property
    def database_path(self) -> Path:
        if self.database_url and self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.removeprefix("sqlite:///"))
        return self.home_path / "mindvault.db"

    def resolve_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.database_path.as_posix()}"

    @property
    def documents_path(self) -> Path:
        if self.documents_dir:
            return Path(self.documents_dir).expanduser()
        return self.home_path / "documents"

    @property
    def index_path(self) -> Path:
        if self.index_dir:
            return Path(self.index_dir).expanduser()
        return self.home_path / "index"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {e.strip().lower().lstrip(".") for e in self.allowed_extensions.split(",") if e.strip()}

    def ensure_directories(self) -> None:
        for path in (self.home_path, self.documents_path, self.index_path, self.database_path.parent):
            path.mkdir(parents=True, exist_ok=True)
