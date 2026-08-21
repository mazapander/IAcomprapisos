from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "IA Compra Pisos API"
    app_env: str = "local"
    log_level: str = "INFO"
    api_key: str = "change-me"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/ia_compra_pisos"
    http_timeout_seconds: int = 60
    analytics_cookie_secure: bool = False
    analytics_cookie_max_age_days: int = 180
    product_data_retention_days: int = 365
    public_base_url: str = "http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
