from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.auth_service import AuthService
from shared_models.db import get_session
from shared_models.crud.inventory import (
    get_inventory_by_user_id,
    get_inventory_item,
    remove_gift_from_user,
)
from shared_models.crud.user import update_user_balance, get_user_by_id
from shared_models.crud.transactions import create_transaction
from shared_models.schemas.inventory import InventoryRead
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
@router.get("/", response_model=List[InventoryRead])
async def get_inventory(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)
    async with get_session() as db:
        inventory = await get_inventory_by_user_id(db, user_id)
    return inventory


# -----------------------
# /inventory/getItem?id=
# -----------------------
@router.get("/getItem", response_model=InventoryRead)
async def get_item(
    id: int = Query(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)

    async with get_session() as db:
        item = await get_inventory_item(db, id)
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
    async with get_session() as db:
        item = await get_inventory_item(db, id)
    if not item or item.user_id != user_id:
        raise HTTPException(status_code=404, detail="Item not found")

    gift = item.gift
    if gift.cost_coins is not None:
        gain = gift.cost_coins
        currency = "HRPN"
    elif gift.cost_ton is not None:
        gain = gift.cost_ton * 1000  # примерная конвертация
        currency = "TON"
    else:
        raise HTTPException(status_code=400, detail="This item has no sellable value")
    
    async with get_session() as db:
        user = await get_user_by_id(db, user_id)
        new_balance = user.coins_balance + gain

    async with get_session() as db:
        await update_user_balance(db, user_id, coins_balance=new_balance)

    async with get_session() as db:
        await remove_gift_from_user(db, user_id, gift.id)

    # Создаём транзакцию
    tx = TransactionCreate(
        user_id=user_id,
        type="gift_sale",
        amount=gain,
        gift_id=gift.id,
        status="completed",
    )
    async with get_session() as db:
        await create_transaction(db, tx)

    return {"message": f"Item sold for {gain} {currency}"}


# -----------------------
# /inventory/withdrawItem?id=
# -----------------------
@router.post("/withdrawItem")
async def withdraw_item(
    id: int = Query(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    user_id = await get_current_user_id(authorization)

    async with get_session() as db:
        item = await get_inventory_item(db, id)
    if not item or item.user_id != user_id:
        raise HTTPException(status_code=404, detail="Item not found")

    tx = TransactionCreate(
        user_id=user_id,
        type="gift_withdrawal",
        gift_id=item.gift_id,
        status="pending",
    )
    async with get_session() as db:
        await create_transaction(db, tx)

    return {"message": "Withdrawal request created"}
