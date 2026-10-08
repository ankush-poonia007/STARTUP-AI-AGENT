from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import MAX_CONCURRENT_TASKS


class Settings(BaseSettings):
    # ── DATABASE ──────────────────────────────────────────────────────────────
    database_url: str
    test_database_url: str | None = None

    # ── CHROMADB ──────────────────────────────────────────────────────────────
    chroma_persist_directory: str
    chroma_collection_name: str = "cofoundr_documents"
    chroma_memory_collection_name: str = "cofoundr_memories"

    # ── FILE STORAGE ──────────────────────────────────────────────────────────
    file_storage_path: str
    max_file_size_bytes: int = 52_428_800

    # ── AUTHENTICATION ────────────────────────────────────────────────────────
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # ── APPLICATION ──────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    # JSON list in .env
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── CONCURRENCY ───────────────────────────────────────────────────────────
    max_concurrent_tasks: int = MAX_CONCURRENT_TASKS

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        frozen=True,
    )


settings = Settings()


if __name__ == "__main__":
    print("Phase 6 settings loaded successfully.")
    print(f"Environment: {settings.environment}")