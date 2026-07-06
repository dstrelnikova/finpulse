from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DB_ECHO: bool = False

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_EXPIRE_MINUTES: int
    REFRESH_EXPIRE_DAYS: int

    NEWS_USE_LLM: bool = False
    NEWS_LLM_FOR_PUBLIC_RSS: bool = False

    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    OLLAMA_MAX_CONCURRENCY: int = Field(default=1, ge=1, le=8)
    OLLAMA_CHAT_TIMEOUT_SEC: int = Field(default=180, ge=5, le=600)
    OLLAMA_CHAT_NUM_PREDICT: int = Field(default=700, ge=128, le=4096)

    GIGACHAT_AUTH_KEY: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_MODEL: str = "GigaChat"
    GIGACHAT_OAUTH_URL: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    GIGACHAT_API_URL: str = "https://gigachat.devices.sberbank.ru/api/v1"
    GIGACHAT_TIMEOUT_SEC: int = Field(default=60, ge=5, le=300)
    GIGACHAT_VERIFY_SSL: bool = True
    GIGACHAT_CHAT_MAX_TOKENS: int = Field(default=700, ge=128, le=4096)
    GIGACHAT_NEWS_MAX_TOKENS: int = Field(default=700, ge=128, le=4096)
    GIGACHAT_MIN_REQUEST_INTERVAL_SEC: float = Field(default=1.2, ge=0, le=30)
    GIGACHAT_MAX_RETRIES: int = Field(default=2, ge=0, le=5)
    NEWS_PUBLIC_RSS_LLM_LIMIT: int = Field(default=8, ge=0, le=50)
    NEWS_PUBLIC_MAX_AGE_DAYS: int = Field(default=7, ge=1, le=60)
    NEWS_PUBLIC_MIN_FACTS: int = Field(default=2, ge=0, le=5)
    NEWS_PUBLIC_MIN_CONFIDENCE: str = "medium"
    NEWS_PUBLIC_HIDE_RSS_ONLY_LOW_INFO: bool = True
    NEWS_PUBLIC_AUTO_REFRESH_ENABLED: bool = True
    NEWS_PUBLIC_AUTO_REFRESH_INTERVAL_HOURS: int = Field(default=24, ge=1, le=168)
    NEWS_PUBLIC_AUTO_REFRESH_STARTUP_DELAY_SEC: int = Field(default=30, ge=0, le=3600)

    ADMIN_EMAIL: str
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"


settings = Settings()
