"""Environment-driven settings. Nothing here is a real secret — every
credential defaults to an empty string and must be supplied via .env."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cyron_api_key: str = ""
    database_url: str = "postgresql+asyncpg://cyron:cyron@db:5432/cyron"
    cors_origins: str = "http://localhost:5173"
    tool_timeout_seconds: int = 300
    scan_output_dir: str = "/data/scan-output"

    shodan_api_key: str = ""
    censys_api_id: str = ""
    censys_api_secret: str = ""
    fofa_email: str = ""
    fofa_api_key: str = ""
    nvd_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
