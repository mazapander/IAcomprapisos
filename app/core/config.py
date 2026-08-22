from pydantic import model_validator
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
    allowed_source_hosts: str = (
        "bde.es,ine.es,transportes.gob.es,vivienda.gob.es,mivau.gob.es"
    )
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def production_secrets_must_be_configured(self):
        if self.app_env.strip().lower() == "production":
            if not self.api_key.strip() or self.api_key == "change-me":
                raise ValueError("API_KEY must be replaced before starting production")
            if not self.analytics_cookie_secure:
                raise ValueError("ANALYTICS_COOKIE_SECURE must be true in production")
            if not self.public_base_url.startswith("https://"):
                raise ValueError("PUBLIC_BASE_URL must use HTTPS in production")
        return self

    @property
    def source_host_suffixes(self) -> tuple[str, ...]:
        return tuple(host.strip().lower() for host in self.allowed_source_hosts.split(",") if host.strip())

settings = Settings()
