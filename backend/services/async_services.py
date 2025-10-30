from datetime import datetime, timedelta
from backend.services.wallet_service import get_transaction_info, get_wallet_transactions, send_nft, send_ton
from shared_models.crud.transactions import get_transaction, update_transaction, get_pending_deposit_transactions
from shared_models.crud.user import get_user_by_id, update_user_balance
from shared_models.schemas.transactions import TransactionUpdate
from sqlalchemy.ext.asyncio import AsyncSession


async def process_gift_withdrawal(
    transaction_id: int,
    destination_address: str,
    nft_address: str,
    db: AsyncSession
):
    """Фоновая отправка NFT и обновление транзакции."""
    try:
        tx_hash = await send_nft(destination_address, nft_address)

        update_data = TransactionUpdate(
            status="completed",
            tx_hash=tx_hash,
            completed_at=datetime.utcnow()
        )
        await update_transaction(db, transaction_id, update_data)

    except Exception as e:
        # Если произошла ошибка, ставим статус failed
        update_data = TransactionUpdate(status="failed")
        await update_transaction(db, transaction_id, update_data)
        # Можно логировать ошибку для отладки
        print(f"Failed to send NFT for tx {transaction_id}: {e}")


async def process_ton_withdraw(
    db: AsyncSession,
    tx_id: int,
    amount: float,
    dest_address: str
):
    """
    Фоновая обработка вывода TON.
    Обновляет статус транзакции после завершения.
    """
    try:
        tx_hash = await send_ton(dest_address, amount)
        await update_transaction(
            db,
            tx_id,
            TransactionUpdate(status="completed", tx_hash=tx_hash)
        )
    except Exception as e:
        # При ошибке отмечаем транзакцию как rejected
        await update_transaction(
            db,
            tx_id,
            TransactionUpdate(status="rejected")
        )


async def process_pending_deposits(db: AsyncSession):
    """
    Проверяет все pending депозиты:
    - Если транзакция найдена и успешна → ставим completed и начисляем TON пользователю
    - Если транзакция в pending > 1 часа → ставим rejected
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # Получаем все pending депозиты
    
    pending_transactions = await get_pending_deposit_transactions(db)

    for tx in pending_transactions:
        if tx.created_at < one_hour_ago:
            # помечаем как rejected
            await update_transaction(db, tx.id, TransactionUpdate(status="rejected"))
            continue

        # Проверяем транзакцию по хэшу через Toncenter
        tx_info = await get_transaction_info(tx.tx_hash)
        if not tx_info:
            continue

        if tx_info["status"] == "success" and abs(tx_info["amount"] - tx.amount) < 1e-6:
            # успешная транзакция → начисляем баланс и закрываем транзакцию
            await update_transaction(db, tx.id, TransactionUpdate(status="completed"))

            # Начисляем пользователю баланс
            user = await get_user_by_id(db, tx.user_id)
            new_balance = user.ton_balance + tx.amount
            await update_user_balance(db, user.id,ton_balance=new_balance )
