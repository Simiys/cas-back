from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Transaction
from ..schemas.transactions import TransactionCreate, TransactionUpdate

# ---------------------------
# CREATE
# ---------------------------
async def create_transaction(db: AsyncSession, tx: TransactionCreate) -> Transaction:
    db_tx = Transaction(**tx.dict())
    db.add(db_tx)
    await db.commit()
    await db.refresh(db_tx)
    return db_tx

# ---------------------------
# READ все транзакции пользователя
# ---------------------------
async def get_transactions_by_user(db: AsyncSession, user_id: int) -> List[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()

# ---------------------------
# READ по ID
# ---------------------------
async def get_transaction(db: AsyncSession, tx_id: int) -> Optional[Transaction]:
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    return result.scalar_one_or_none()

# ---------------------------
# UPDATE
# ---------------------------
async def update_transaction(db: AsyncSession, tx_id: int, data: TransactionUpdate) -> Optional[Transaction]:
    tx = await get_transaction(db, tx_id)
    if not tx:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(tx, key, value)

    await db.commit()
    await db.refresh(tx)
    return tx

# ---------------------------
# DELETE
# ---------------------------
async def delete_transaction(db: AsyncSession, tx_id: int) -> Optional[Transaction]:
    tx = await get_transaction(db, tx_id)
    if not tx:
        return None
    await db.delete(tx)
    await db.commit()
    return tx
