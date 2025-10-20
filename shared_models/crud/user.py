from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.models import User
from shared_models.models import Inventory
from shared_models.schemas.user import UserCreate

# ---------------------------
# CREATE
# ---------------------------
async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    db_user = User(
        tg_id=user_in.tg_id,
        username=user_in.username,
        name=user_in.name,
        avatar_url=user_in.avatar_url,
        chat_id=user_in.chat_id,
        ref_code=user_in.ref_code,
        ref_by=user_in.ref_by
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# ---------------------------
# READ
# ---------------------------
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.inventory).selectinload(Inventory.gift),  # inventory + gift
            selectinload(User.wallets),
            selectinload(User.games),
            selectinload(User.lottery_tickets),
            selectinload(User.transactions),
        )
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_user_by_tg_id(db: AsyncSession, tg_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_users_by_ref_by(db: AsyncSession, ref_by_username: str) -> List[User]:
    result = await db.execute(select(User).where(User.ref_by == ref_by_username))
    return result.scalars().all()

async def get_top_users_by_coins(db: AsyncSession, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).order_by(User.coins_balance.desc()).limit(limit))
    return result.scalars().all()

# ---------------------------
# UPDATE баланса
# ---------------------------
async def update_user_balance(
    db: AsyncSession,
    user_id: int,
    ton_balance: Optional[float] = None,
    coins_balance: Optional[float] = None
) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    if ton_balance is not None:
        user.ton_balance = ton_balance
    if coins_balance is not None:
        user.coins_balance = coins_balance

    await db.commit()
    await db.refresh(user)
    return user
