# file: wallet_service.py
from datetime import datetime, timedelta
import os
from typing import Dict, Optional
import aiohttp
import requests
from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import TransferNFTMessage
from config import settings




IS_TESTNET = False
MNEMONIC = settings.MNEMONIC
APP_WALLET_ADDRESS = settings.APP_WALLET_ADDRESS
TONCENTER_API_KEY = settings.TONCENTER_API_KEY


# --------------------------
# 1. Получение цены NFT
# --------------------------
def get_gift_price(nft_address: str, limit=10, min_value_threshold=2.0):
    """Возвращает последнюю продажную цену NFT (TON), если >= min_value_threshold"""
    url = (
        f"https://toncenter.com/api/v2/getTransactions"
        f"?address={nft_address}"
        f"&limit={limit}"
        f"&api_key={TONCENTER_API_KEY}"
    )
    resp = requests.get(url)
    if resp.status_code != 200:
        return None

    data = resp.json()
    transactions = data.get("result", [])
    for tx in transactions:
        for msg in tx.get("out_msgs", []):
            value_ton = int(msg.get("value", 0)) / 1e9
            if value_ton >= min_value_threshold:
                return value_ton
        in_msg = tx.get("in_msg")
        if in_msg:
            value_ton = int(in_msg.get("value", 0)) / 1e9
            if value_ton >= min_value_threshold:
                return value_ton
    return None


# --------------------------
# 2. Получение всех подарков NFT
# --------------------------
def get_all_gifts(owner_address: str, limit: int = 50, offset: int = 0):
    """Возвращает массив NFT с обязательными полями: owner_id, name, desc, image, lottie, price"""
    headers = {"accept": "application/json", "X-Api-Key": TONCENTER_API_KEY}
    params = {"owner_address": owner_address, "limit": limit, "offset": offset}
    resp = requests.get("https://toncenter.com/api/v3/nft/items", headers=headers, params=params)
    resp.raise_for_status()
    payload = resp.json()
    nft_items = payload.get("nft_items", [])
    metadata_map = payload.get("metadata", {}) or {}

    results = []
    for item in nft_items:
        token_addr = item.get("address")
        meta_for_token = metadata_map.get(token_addr, {})
        token_info_list = meta_for_token.get("token_info") or []
        token_info = token_info_list[0] if token_info_list else {}

        name = token_info.get("name")
        description = token_info.get("description")
        image = token_info.get("image")
        extra = token_info.get("extra") or {}
        
        # Извлечение lottie из extra
        lottie = None
        if isinstance(extra, dict):
            lottie = extra.get("lottie")

        # Если image не указан, пробуем взять из extra
        if not image and isinstance(extra, dict):
            for k in ("_image_medium", "_image_small", "_image_big", "image"):
                if extra.get(k):
                    image = extra.get(k)
                    break

        results.append({
            "owner_id": owner_address,
            "name": name,
            "desc": description,
            "image": image,   
            "lottie": lottie, 
            "price": get_gift_price(token_addr),
            "address":token_addr
        })
    return results



# --------------------------
# 3. Передача NFT
# --------------------------
async def send_nft(destination_address: str, nft_address: str, comment: str = ""):
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)
    tx_hash = await wallet.transfer_message(
        message=TransferNFTMessage(
            destination=destination_address,
            nft_address=nft_address,
            forward_payload=comment,
        )
    )
    return tx_hash


# --------------------------
# 4. Перевод TON
# --------------------------
async def send_ton(destination_address: str, amount: float, comment: str = ""):
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)
    tx_hash = await wallet.transfer(
        destination=destination_address,
        amount=amount,
        body=comment
    )
    return tx_hash


# --------------------------
# 5. Получение информации о транзакции
# --------------------------
async def get_transaction_info(tx_hash: str) -> Optional[Dict]:
    url = f"https://toncenter.com/api/v3/transactions?hash={tx_hash}&limit=1&sort=desc"
    headers = {
        "accept": "application/json",
        "X-API-Key": TONCENTER_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()

    txs = data.get("transactions", [])
    if not txs:
        return None

    tx = txs[0]
    out_msgs = tx.get("out_msgs", [])

    received_msg = next(
        (msg for msg in out_msgs if msg.get("destination") == APP_WALLET_ADDRESS),
        None
    )

    amount = int(received_msg.get("value", 0)) / 1e9 if received_msg else 0
    status = "success" if tx.get("description", {}).get("action", {}).get("success") else "failed"
    sender = tx.get("in_msg", {}).get("source")
    receiver = received_msg.get("destination") if received_msg else None
    timestamp = tx.get("now")

    return {
        "hash": tx_hash,
        "amount": amount,
        "status": status,
        "sender": sender,
        "receiver": receiver,
        "timestamp": timestamp,
        "out_msgs": out_msgs,
        "description": tx.get("description")
    }


async def get_last_transactions(limit: int = 10):
    """
    Получение последних транзакций кошелька за последние 20 минут через TonCenter v3 API (async).
    Возвращает список словарей:
    {
        'sender': str,
        'receiver': str,
        'hash': str,
        'amount': int,  # в нанограммах
        'time': datetime,
        'confirmed': bool
    }
    """

    twenty_minutes_ago = int((datetime.utcnow() - timedelta(minutes=20)).timestamp())

    url = "https://toncenter.com/api/v3/transactions"

    params = {
        "account": APP_WALLET_ADDRESS,
        "limit": limit,
        "offset": 0,
        "sort": "desc",
        "start_lt": twenty_minutes_ago,
    }

    headers = {
        "accept": "application/json",
        "X-API-Key": TONCENTER_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()

    transactions = []

    for tx in data.get("transactions", []):
        in_msg = tx.get("in_msg", {})
        if not in_msg:
            continue

        sender = in_msg.get("source")
        receiver = in_msg.get("destination")
        hash_ = tx.get("hash")

        raw_amount = in_msg.get("value")
        amount = int(raw_amount or 3)

        time = datetime.fromtimestamp(tx.get("now", 0))
        confirmed = tx.get("end_status") == "active"

        transactions.append({
            "sender": sender,
            "receiver": receiver,
            "hash": hash_,
            "amount": amount,
            "time": time,
            "confirmed": confirmed
        })

    return transactions

def check_transaction(transactions, sender_address: str, amount: int):
    """
    Проверяет, есть ли среди транзакций транзакция с указанным
    отправителем и суммой (в нанограммах).
    """
    for tx in transactions:
        if tx["sender"] == sender_address and tx["amount"] == amount:
            return True
    return False