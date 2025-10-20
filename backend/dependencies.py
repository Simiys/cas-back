from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
from typing import Optional
from redis import asyncio as aioredis

from config import get_settings
from shared_models.crud import *
from shared_models.models import * 

settings = get_settings()
security = HTTPBearer()

# -----------------------
# Redis
# -----------------------
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Возвращает асинхронное подключение к Redis.
    Создаёт клиент один раз и использует его повторно.
    """
    global _redis_client
    if _redis_client is None:
        if not settings.REDIS_URL:
            raise RuntimeError("REDIS_URL не задан в настройках")
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            # Проверка соединения
            await _redis_client.ping()
        except Exception as e:
            raise RuntimeError(f"Не удалось подключиться к Redis: {e}")
    return _redis_client


async def get_user_from_telegram_auth(auth_token: str = Header(...)) -> dict:
    """
    Если Telegram Mini App передаёт auth_token в заголовке.
    Можно здесь расшифровывать данные, которые Telegram шлёт при WebAppInitData.
    """
    from urllib.parse import parse_qs, unquote
    import hashlib, hmac

    data = {k: v[0] for k, v in parse_qs(auth_token).items()}

    check_hash = data.pop("hash", None)
    auth_data = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(b"WebAppData", settings.SECRET_KEY.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, auth_data.encode(), hashlib.sha256).hexdigest()

    if computed_hash != check_hash:
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")

    return data  

