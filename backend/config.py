import os
from dotenv import load_dotenv
from pydantic_settings  import BaseSettings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings(BaseSettings):
    SECRET_KEY: str
    REDIS_URL: str | None = None
    TOKEN_EXPIRE_MINUTES: int = 60*24*7  # 7 дней по умолчанию

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"

settings = Settings()


def get_settings():
    return settings