from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
