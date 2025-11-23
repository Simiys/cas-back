import os
from dotenv import load_dotenv
from pydantic_settings  import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings(BaseSettings):

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    SECRET_KEY: str
    REDIS_URL: str | None = None
    TOKEN_EXPIRE_MINUTES: int = 60*24*7  # 7 дней по умолчанию
    TELEGRAM_BOT_TOKEN: str | None = None


    APP_WALLET_ADDRESS: str
    MNEMONIC: str
    TONCENTER_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"  # игнорируем лишние переменные в окружении
    )

settings = Settings()


def get_settings():
    return settings