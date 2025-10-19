from fastapi import APIRouter, HTTPException, Header, Body, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import AuthService
from shared_models.db import get_session
from services.balance_service import ExchangeRequest, ExchangeResponse, convert_currency_for_user

router = APIRouter(
    prefix="/balance",
    tags=["balance"]
)

auth_service = AuthService()


# ------------------------
# /balance/convert
# ------------------------
@router.post("/convert", response_model=ExchangeResponse)
async def convert(
    payload: ExchangeRequest = Body(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    """
    Конвертирует валюту (например, TON → COINS) для пользователя по токену.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # ⚙️ Безопасно извлекаем токен
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = parts[1]

    try:
        user_id = auth_service.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 💰 Конвертация валюты
    return await convert_currency_for_user(
        user_id=user_id,
        in_currency=payload.inCurrency,
        amount=payload.amount,
        db=db,
    )


# ------------------------
# Методы /ton (заглушки)
# ------------------------
@router.get("/ton/history")
async def ton_history():
    return []

@router.post("/ton/withdraw")
async def ton_withdraw():
    return []

@router.post("/ton/deposit")
async def ton_deposit():
    return []

@router.post("/ton/wallet/connect")
async def ton_wallet_connect():
    return []

@router.post("/ton/wallet/disconnect")
async def ton_wallet_disconnect():
    return []
