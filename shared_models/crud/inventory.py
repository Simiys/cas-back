from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.models import Inventory
from shared_models.schemas.inventory import InventoryCreate

# ---------------------------
# CREATE
# ---------------------------
async def add_gift_to_user(db: AsyncSession, inventory_in: InventoryCreate) -> Inventory:
    db_item = Inventory(
        user_id=inventory_in.user_id,
        gift_id=inventory_in.gift_id
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

# ---------------------------
# READ все подарки пользователя
# ---------------------------
async def get_inventory_by_user_id(db: AsyncSession, user_id: int) -> List[Inventory]:
    result = await db.execute(select(Inventory).where(Inventory.user_id == user_id))
    return result.scalars().all()

# ---------------------------
# READ конкретный элемент
# ---------------------------
async def get_inventory_item(db: AsyncSession, inventory_id: int) -> Optional[Inventory]:
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    return result.scalar_one_or_none()

# ---------------------------
# DELETE
# ---------------------------
async def remove_gift_from_user(db: AsyncSession, user_id: int, gift_id: int) -> bool:
    result = await db.execute(
        select(Inventory).where(
            Inventory.user_id == user_id,
            Inventory.gift_id == gift_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True
