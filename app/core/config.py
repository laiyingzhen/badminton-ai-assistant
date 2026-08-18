from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "AI Badminton Equipment Assistant"
    app_version: str = "1.0.0"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # Recommendation
    racket_candidate_limit: int = 3

    # Voice input
    voice_audio_max_bytes: int = 10 * 1024 * 1024

    # Google Cloud / Vertex AI
    google_cloud_project: str
    google_cloud_location: str = "global"
    gemini_model: str = "gemini-2.5-flash"

    # Embedding
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 768

    # Database
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()