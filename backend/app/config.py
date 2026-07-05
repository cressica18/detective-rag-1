from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_path: str = "data/detective.db"
    chroma_path: str = "data/chroma"
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"
    max_file_size_mb: int = 20
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Ensure data directories exist
for path in [settings.raw_data_path, settings.processed_data_path, settings.chroma_path]:
    os.makedirs(path, exist_ok=True)
os.makedirs(os.path.dirname(settings.database_path) if os.path.dirname(settings.database_path) else ".", exist_ok=True)
