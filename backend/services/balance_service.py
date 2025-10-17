from fastapi import APIRouter, HTTPException, Header, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.crud.user import get_user_by_id, update_user_balance
from api.v1.balance import ExchangeResponse


async def convert_currency_for_user(
    user_id: int,
    in_currency: str,
    amount: float,
    db: AsyncSession
) -> ExchangeResponse:
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rate = 1000  # 1 TON = 1000 HRPN

    if in_currency == "hrpn":
        if user.coins_balance < amount:
            raise HTTPException(status_code=400, detail="Not enough HRPN")
        converted_amount = amount / rate
        new_hrpn = user.coins_balance - amount
        new_ton = user.ton_balance + converted_amount
    elif in_currency == "ton":
        if user.ton_balance < amount:
            raise HTTPException(status_code=400, detail="Not enough TON")
        converted_amount = amount * rate
        new_ton = user.ton_balance - amount
        new_hrpn = user.coins_balance + converted_amount
    else:
        raise HTTPException(status_code=400, detail="Invalid currency")

    # Обновляем баланс в БД
    await update_user_balance(db, user_id, ton_balance=new_ton, coins_balance=new_hrpn)

    return ExchangeResponse(
        from_currency=in_currency,
        to_currency="ton" if in_currency == "hrpn" else "hrpn",
        converted_amount=converted_amount,
        new_ton_balance=new_ton,
        new_hrpn_balance=new_hrpn
    )