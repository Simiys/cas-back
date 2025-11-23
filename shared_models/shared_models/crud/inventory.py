from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.models import Gift


# ---------------------------
# CREATE (передача подарка пользователю)
# ---------------------------
async def assign_gift_to_user(db: AsyncSession, gift_id: int, user_id: int) -> Optional[Gift]:
    """
    Привязывает подарок к пользователю.
    """
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    gift = result.scalar_one_or_none()

    if not gift:
        return None

    gift.owner_id = user_id
    db.add(gift)
    await db.commit()
    await db.refresh(gift)
    return gift


# ---------------------------
# READ — все подарки пользователя
# ---------------------------
async def get_gifts_by_user_id(db: AsyncSession, user_id: int) -> List[Gift]:
    result = await db.execute(select(Gift).where(Gift.owner_id == user_id))
    return result.scalars().all()


# ---------------------------
# READ — один подарок по ID
# ---------------------------
async def get_gift_by_id(db: AsyncSession, gift_id: int) -> Optional[Gift]:
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    return result.scalar_one_or_none()


# ---------------------------
# DELETE (удаление привязки пользователя)
# ---------------------------
async def remove_gift_from_user(db: AsyncSession, gift_id: int) -> bool:
    """
    Сбрасывает владельца подарка (подарок больше никому не принадлежит).
    """
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    gift = result.scalar_one_or_none()

    if not gift or gift.owner_id is None:
        return False

    gift.owner_id = None
    db.add(gift)
    await db.commit()
    return True


# ---------------------------
# READ — список всех подарков (например, для магазина)
# ---------------------------
async def get_all_gifts(db: AsyncSession) -> List[Gift]:
    result = await db.execute(select(Gift))
    return result.scalars().all()
