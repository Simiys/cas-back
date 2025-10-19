from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.models import Gift
from shared_models.schemas.gift import GiftCreate, GiftUpdate

# ---------------------------
# CREATE
# ---------------------------
async def create_gift(db: AsyncSession, gift_in: GiftCreate) -> Gift:
    db_gift = Gift(
        name=gift_in.name,
        telegram_gift_id=gift_in.telegram_gift_id,
        cost_coins=gift_in.cost_coins,
        cost_ton=gift_in.cost_ton
    )
    db.add(db_gift)
    await db.commit()
    await db.refresh(db_gift)
    return db_gift

# ---------------------------
# READ по ID
# ---------------------------
async def get_gift_by_id(db: AsyncSession, gift_id: int) -> Optional[Gift]:
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    return result.scalar_one_or_none()

# ---------------------------
# READ все подарки
# ---------------------------
async def get_all_gifts(db: AsyncSession) -> List[Gift]:
    result = await db.execute(select(Gift))
    return result.scalars().all()

# ---------------------------
# UPDATE
# ---------------------------
async def update_gift(db: AsyncSession, gift_id: int, gift_in: GiftUpdate) -> Optional[Gift]:
    gift = await get_gift_by_id(db, gift_id)
    if not gift:
        return None

    if gift_in.name is not None:
        gift.name = gift_in.name
    if gift_in.cost_coins is not None:
        gift.cost_coins = gift_in.cost_coins
    if gift_in.cost_ton is not None:
        gift.cost_ton = gift_in.cost_ton

    await db.commit()
    await db.refresh(gift)
    return gift

# ---------------------------
# DELETE
# ---------------------------
async def delete_gift(db: AsyncSession, gift_id: int) -> bool:
    gift = await get_gift_by_id(db, gift_id)
    if not gift:
        return False
    await db.delete(gift)
    await db.commit()
    return True
