from fastapi import APIRouter, HTTPException, Header, Body, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import AuthService
from shared_models.db import get_session
from services.balance_service import ExchangeRequest, ExchangeResponse, convert_currency_for_user

router = APIRouter(
    prefix="balance",
    tags=["currency"]
)

auth_service = AuthService()

# ------------------------
# Схемы
# ------------------------


# ------------------------
# /hrpn/exchange
# ------------------------
@router.post("/convert", response_model=ExchangeResponse)
async def convert(
    payload: ExchangeRequest = Body(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        token = authorization.split(" ")[1]
        user_id = auth_service.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Вызываем вынесенный метод
    return await convert_currency_for_user(
        user_id=user_id,
        in_currency=payload.inCurrency,
        amount=payload.amount,
        db=db
    )

# ------------------------
# Методы /ton (пока пустые)
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
