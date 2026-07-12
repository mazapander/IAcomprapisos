from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "IA Compra Pisos API"
    app_env: str = "local"
    log_level: str = "INFO"
    api_key: str = "change-me"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/ia_compra_pisos"
    http_timeout_seconds: int = 60
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
