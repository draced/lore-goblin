from dataclasses import dataclass, field
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("LORE_GOBLIN_DATABASE_PATH", "data/lore_goblin.sqlite3")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
    cors_origins: list[str] = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("LORE_GOBLIN_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ])


@lru_cache
def get_settings() -> Settings:
    return Settings()
