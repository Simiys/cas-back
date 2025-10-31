import asyncio
from datetime import time
from fastapi import APIRouter, HTTPException, Header, Body, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.v1.inventory import get_current_user_id
from backend.services.async_services import process_ton_withdraw
from services.auth_service import AuthService
from shared_models.crud.transactions import create_transaction, get_ton_history
from shared_models.crud.user import get_user_by_id
from shared_models.crud.wallet import create_wallet, get_wallet_by_user_id
from shared_models.db import get_session
from services.balance_service import ExchangeRequest, ExchangeResponse, convert_currency_for_user
from shared_models.schemas.transactions import TransactionCreate, TransactionRead
from os import getenv



APP_WALLET = getenv("APP_WALLET")


router = APIRouter(
    prefix="/balance",
    tags=["balance"]
)

auth_service = AuthService()

class TonWithdrawRequest(BaseModel):
    amount: float 

class WalletConnectRequest(BaseModel):
    wallet_address: str

class TonDepositRequest(BaseModel):
    amount: float 
    tx_hash: str 

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


    return await convert_currency_for_user(
        user_id=user_id,
        in_currency=payload.inCurrency,
        amount=payload.amount,
        db=db,
    )


# ------------------------
# Методы /ton (заглушки)
# ------------------------
@router.get("/ton/history", response_model=List[TransactionRead])
async def ton_history(
    db: AsyncSession = Depends(get_session),
    authorization: Optional[str] = Header(None),
):
    user_id = await get_current_user_id(authorization)
    """
    Возвращает историю TON транзакций (депозиты и выводы) пользователя.
    """
    transactions = await get_ton_history(db, user_id)
    return transactions



@router.post("/ton/withdraw")
async def ton_withdraw(
    payload: TonWithdrawRequest = Body(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    # Получаем user_id
    user_id = await get_current_user_id(authorization)

    # Получаем пользователя
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем баланс
    if user.ton_balance < payload.amount:
        raise HTTPException(status_code=400, detail="Not enough TON balance")

    # Снимаем TON сразу (чтобы избежать гонок)
    user.ton_balance -= payload.amount
    await db.commit()
    await db.refresh(user)

    # Получаем кошелек пользователя
    wallet = await get_wallet_by_user_id(db, user_id)
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet not found")

    # Создаем транзакцию
    tx = TransactionCreate(
        user_id=user_id,
        type="ton_withdrawal",
        amount=payload.amount,
        status="pending",
    )
    transaction = await create_transaction(db, tx)

    # Запускаем фоновую задачу на отправку TON
    asyncio.create_task(
        process_ton_withdraw(db, transaction.id, payload.amount, wallet.wallet_address)
    )

    return {"message": "TON withdrawal started", "transaction_id": transaction.id}


@router.post("/ton/deposit")
async def ton_deposit(
    payload: TonDepositRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)
    wallet = await get_wallet_by_user_id(db, user_id)
    # Создаём транзакцию в статусе pending
    tx = await create_transaction(
        db,
        TransactionCreate(
            user_id=user_id,
            type="deposit",
            tx_hash=wallet.wallet_address,
            amount=payload.amount,
            status="pending"
        ),
    )

    ton_tx = {
    "validUntil": int(time.time()) + 600,  # 10 минут
    "messages": [
        {
            "address": APP_WALLET,
            "amount": str(int(payload.amount * 1e9)), # TON -> nanoton
        }
    ],
    "metadata": {
        "transaction_id": tx.id
    }
}

    return {
        "transaction_id": tx.id,
        "ton_tx": ton_tx
    }



@router.post("/ton/wallet/connect")
async def ton_wallet_connect(
    payload: WalletConnectRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = get_current_user_id(authorization)

    existing_wallet = await get_wallet_by_user_id(db, user_id)
    if existing_wallet:
        return {"message": "Wallet already exists" }

    # Создаем новый кошелек
    wallet = await create_wallet(db, user_id=user_id, wallet_address=payload.wallet_address)
    return {"message": "Wallet connected", "wallet_address": wallet.wallet_address}
