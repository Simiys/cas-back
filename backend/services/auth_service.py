import os
import jwt
import json
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from shared_models.crud.user import get_user_by_tg_id
from dependencies import get_user_from_telegram_auth  # выносится отдельно

class AuthService:
    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        token_expire_minutes: int = 60*24*7  # 7 дней по умолчанию
    ):
        # Берём ключ из параметра, если передан, иначе из переменных окружения
        self.secret_key = secret_key or os.getenv("SECRET_KEY")
        if not self.secret_key:
            raise ValueError("SECRET_KEY is not set in environment variables!")

        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
    # --- Проверка Telegram-токена ---
    async def verify_telegram_token(self, auth_token: str) -> dict:
        """
        Проверяет Telegram токен и возвращает user-данные (dict)
        """
        try:
            user_data = await get_user_from_telegram_auth(auth_token)
        except HTTPException as e:
            raise e
        return user_data


    # --- Создание JWT ---
    def create_access_token(self, user_id: int, expires_delta: timedelta | None = None) -> str:
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.token_expire_minutes))
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


    # --- Декодирование JWT ---
    def decode_access_token(self, token: str) -> int:
        from jwt import ExpiredSignatureError, InvalidTokenError
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = int(payload.get("sub"))
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return user_id
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        

    # --- Telegram login ---
    async def login_via_telegram(self, db: AsyncSession, auth_token: str) -> str:
        """
        Проверяет Telegram токен, ищет пользователя в БД и выдаёт JWT.
        """
        data = await self.verify_telegram_token(auth_token)
        tg_user = json.loads(data["user"])  # Telegram JSON-строка
        tg_id = tg_user["id"]

        db_user = await get_user_by_tg_id(db, tg_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        token = self.create_access_token(user_id=db_user.id)
        return token
