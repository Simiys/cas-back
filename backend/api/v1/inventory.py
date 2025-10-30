import asyncio
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.async_services import process_gift_withdrawal
from backend.services.auth_service import AuthService
from shared_models.crud.wallet import get_wallet_by_user_id
from shared_models.db import get_session
from shared_models.crud.inventory import (
    get_gifts_by_user_id,
    get_gift_by_id,
    remove_gift_from_user,
)
from shared_models.crud.user import update_user_balance, get_user_by_id
from shared_models.crud.transactions import create_transaction
from shared_models.schemas.gift import GiftRead
from shared_models.schemas.transactions import TransactionCreate


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"]
)

auth_service = AuthService()  # SECRET_KEY берется из settings


# -----------------------
# Вспомогательная функция (чтобы не дублировать код)
# -----------------------
async def get_current_user_id(authorization: Optional[str]) -> int:
    """
    Достаёт user_id из JWT токена. 
    Поднимает 401, если токен отсутствует или неверен.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = parts[1]
    try:
        user_id = auth_service.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


# -----------------------
# /inventory/ — все предметы пользователя
# -----------------------
@router.get("/", response_model=List[GiftRead])
async def get_inventory(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)

    inventory = await get_gifts_by_user_id(db, user_id)
    return inventory


# -----------------------
# /inventory/getItem?id=
# -----------------------
@router.get("/getItem", response_model=GiftRead)
async def get_item(
    id: int = Query(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)


    item = await get_gift_by_id(db, id)
    if not item or item.user_id != user_id:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


# -----------------------
# /inventory/sellItem?id=
# -----------------------
@router.post("/sellItem")
async def sell_item(
    id: int = Query(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)

    gift = await get_gift_by_id(db, id)
    if not gift or gift.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Item not found")


    if gift.cost_ton is not None:
        gain = gift.cost_ton * 1000  
        currency = "TON"
    else:
        raise HTTPException(status_code=400, detail="This item has no sellable value")
    
    user = await get_user_by_id(db, user_id)
    new_balance = user.coins_balance + gain

    await update_user_balance(db, user_id, coins_balance=new_balance)


    await remove_gift_from_user(db, user_id, gift.id)

    # Создаём транзакцию
    tx = TransactionCreate(
        user_id=user_id,
        type="gift_sale",
        amount=gain,
        gift_id=gift.id,
        status="completed",
   )

    await create_transaction(db, tx)

    return {"message": f"Item sold for {gain} {currency}"}


# -----------------------
# /inventory/withdrawItem?id=
# -----------------------
@router.post("/withdrawItem")
async def withdraw_item(
    id: int = Query(...),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)

    # Проверяем, что подарок принадлежит пользователю
    item = await get_gift_by_id(db, id)
    if not item or item.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Item not found")

    # Получаем кошелёк пользователя
    wallet = await get_wallet_by_user_id(db, user_id)
    if not wallet or not wallet.wallet_address:
        raise HTTPException(status_code=400, detail="Wallet not found")

    wallet_address = wallet.wallet_address

    # Создаём запись о транзакции
    tx = TransactionCreate(
        user_id=user_id,
        type="gift_withdrawal",
        gift_id=item.id,
        status="pending",
    )
    transaction = await create_transaction(db, tx)

    # Фоновая отправка NFT
    asyncio.create_task(process_gift_withdrawal(transaction.id, wallet_address, item.nft_address, db))

    return {"message": "Withdrawal request created and processing started"}

