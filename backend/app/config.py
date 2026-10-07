# Settings loaded from environment / .env (see ../.env.example)
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    llm_provider: str = "mock"  # mock | anthropic | gemini | openai
    llm_model: str = ""  # user-set; never hardcode model names
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""
    ack_timeout_s: int = 60
    avg_loss_prevented_inr: int = 25000
    data_ttl_hours: int = 24
    frontend_origin: str = "http://localhost:3000"

    @property
    def telegram_mode(self) -> str:
        return "live" if self.telegram_bot_token and self.telegram_bot_username else "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
