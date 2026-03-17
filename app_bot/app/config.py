import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator

load_dotenv()


class Settings(BaseModel):
    bot_token: str = Field(alias="BOT_TOKEN")
    admin_chat_id: str = Field(alias="ADMIN_CHAT_ID")
    allowed_origins_raw: str = Field(default="*", alias="ALLOWED_ORIGINS")

    @field_validator("bot_token", "admin_chat_id")
    @classmethod
    def validate_required_value(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Missing required environment variable")
        return value

    @property
    def telegram_api_base(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}"

    @property
    def allowed_origins(self) -> list[str]:
        raw_value = self.allowed_origins_raw.strip()
        if not raw_value or raw_value == "*":
            return ["*"]

        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    raw_settings = {
        "BOT_TOKEN": os.getenv("BOT_TOKEN", ""),
        "ADMIN_CHAT_ID": os.getenv("ADMIN_CHAT_ID", ""),
        "ALLOWED_ORIGINS": os.getenv("ALLOWED_ORIGINS", "*"),
    }

    try:
        return Settings.model_validate(raw_settings)
    except ValidationError as exc:
        raise RuntimeError(
            "Invalid environment configuration. Check BOT_TOKEN, ADMIN_CHAT_ID, and ALLOWED_ORIGINS."
        ) from exc
