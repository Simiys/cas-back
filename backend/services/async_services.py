from datetime import datetime, timedelta
import os
from backend.services.wallet_service import get_last_transactions, get_transaction_info, send_nft, send_ton
from shared_models.crud.transactions import get_transaction, update_transaction, get_pending_deposit_transactions
from shared_models.crud.user import get_user_by_id, update_user_balance
from shared_models.crud.wallet import get_wallet_by_user_id
from shared_models.schemas.transactions import TransactionUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
import base64
import binascii

APP_WALLET_ADDRESS = settings.APP_WALLET_ADDRESS


#utils
def ton_to_raw(addr: str) -> str:
    # base64url decode
    data = base64.urlsafe_b64decode(addr + "==")

    flags = data[0]
    workchain = data[1]
    hash_part = data[2:-2]          # remove CRC16 (last 2 bytes)

    return f"{workchain}:{hash_part.hex().upper()}"


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
    try:
        print("started withdraw for tx: ", tx_id)
        tx_hash = await send_ton(dest_address, amount)
        await update_transaction(
            db,
            tx_id,
            TransactionUpdate(status="completed", tx_hash=tx_hash)
        )
    except Exception as e:
        print("withdraw_err", e)
        await update_transaction(
            db,
            tx_id,
            TransactionUpdate(status="rejected")
        )


from datetime import datetime, timedelta, timezone

async def process_pending_deposits(db: AsyncSession):
    """
    Проверяет все pending депозиты:
    - Если транзакция висит > 1 часа → rejected
    - Если транзакция найдена → completed + начисление
    """
    now = datetime.now(timezone.utc)           # <-- UTC-aware
    one_hour_ago = now - timedelta(hours=3)    # <-- тоже UTC-aware

    pending_transactions = await get_pending_deposit_transactions(db)

    
    recent_txs = await get_last_transactions(limit=30)
    for tx in pending_transactions:
        print("processing tx: ", tx.id) 
        # 1) Если висит > часа → rejected
        if tx.created_at < one_hour_ago:
            await update_transaction(db, tx.id, TransactionUpdate(status="rejected"))
            continue

        user = await get_user_by_id(db, tx.user_id)
        wallet = await get_wallet_by_user_id(db, user.id)
        expected_amount_ngr = int(tx.amount * 1e9)
        print("tx sender: ", tx.tx_hash)
        print("tx amount: ", expected_amount_ngr)
        matched_tx = None
        for chain_tx in recent_txs:
            print("chain_tx: ", chain_tx)
            if (
                chain_tx["sender"] == wallet.wallet_address
                and chain_tx["receiver"] == ton_to_raw(APP_WALLET_ADDRESS)
                and chain_tx["amount"] == expected_amount_ngr
                and chain_tx["confirmed"] is True
            ):
                matched_tx = chain_tx
                print("Matched!")
                print(matched_tx)
                break

        if not matched_tx:
            continue

        # 3) Транзакция найдена — completed + баланс
        await update_transaction(db, tx.id, TransactionUpdate(status="completed"))
        new_balance = user.ton_balance + tx.amount
        await update_user_balance(db, user.id, ton_balance=new_balance)
