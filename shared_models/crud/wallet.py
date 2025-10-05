from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Wallet
from ..schemas.wallet import WalletCreate

# ---------------------------
# CREATE
# ---------------------------
async def create_wallet(db: AsyncSession, wallet_in: WalletCreate) -> Wallet:
    db_wallet = Wallet(
        user_id=wallet_in.user_id,
        wallet_address=wallet_in.wallet_address,
        wallet_type=wallet_in.wallet_type
    )
    db.add(db_wallet)
    await db.commit()
    await db.refresh(db_wallet)
    return db_wallet

# ---------------------------
# READ все кошельки пользователя
# ---------------------------
async def get_wallets_by_user_id(db: AsyncSession, user_id: int) -> List[Wallet]:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalars().all()

# ---------------------------
# READ по ID
# ---------------------------
async def get_wallet_by_id(db: AsyncSession, wallet_id: int) -> Optional[Wallet]:
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    return result.scalar_one_or_none()

# ---------------------------
# DELETE
# ---------------------------
async def delete_wallet(db: AsyncSession, wallet_id: int) -> bool:
    wallet = await get_wallet_by_id(db, wallet_id)
    if not wallet:
        return False
    await db.delete(wallet)
    await db.commit()
    return True
