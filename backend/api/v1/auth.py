from fastapi import APIRouter, Depends, HTTPException, Header, Body
from typing import Optional
from pydantic import BaseModel
from backend.services.auth_service import AuthService
from backend.dependencies import get_redis
from shared_models.db import get_session
from redis import asyncio as aioredis
import json
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# -----------------------
# Получение JWT по Telegram токену
# -----------------------
@router.post("", response_model=TokenResponse)
async def login(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_session),
):
    """
    Получает Telegram auth_token и возвращает JWT для всех последующих запросов.
    """
    auth_token = payload.get("auth_token")
    if not auth_token:
        raise HTTPException(status_code=400, detail="auth_token missing")

    auth_service = AuthService()  # или settings.SECRET_KEY
    token = await auth_service.login_via_telegram(db, auth_token)

    return TokenResponse(access_token=token)