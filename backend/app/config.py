from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    ACK_TIMEOUT_S: int = 60
    AVG_LOSS_PREVENTED_INR: int = 25000
    DATA_TTL_HOURS: int = 24
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    DATABASE_URL: str = "sqlite+aiosqlite:///./scamshield.db"


settings = Settings()
