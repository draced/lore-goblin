from dataclasses import dataclass, field
from functools import lru_cache
import os


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("LORE_GOBLIN_DATABASE_PATH", "data/lore_goblin.sqlite3")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    resolution_confidence_threshold: float = float(
        os.getenv("LORE_GOBLIN_RESOLUTION_THRESHOLD", "0.75")
    )
    max_extraction_retries: int = int(os.getenv("LORE_GOBLIN_MAX_EXTRACTION_RETRIES", "3"))
    extraction_auto_run: bool = field(
        default_factory=lambda: not _env_flag("LORE_GOBLIN_DISABLE_EXTRACTION_AUTO_RUN")
    )
    allow_migrate: bool = field(default_factory=lambda: _env_flag("LORE_GOBLIN_ALLOW_MIGRATE"))
    cors_origins: list[str] = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("LORE_GOBLIN_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ])


@lru_cache
def get_settings() -> Settings:
    return Settings()
