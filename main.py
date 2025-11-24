import os
import requests

# -----------------------
# Если get_gift_price у тебя есть — импортируешь. 
# Пока для теста можно сделать заглушку:
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
# -----------------------
# TONCENTER_API_KEY нужен для запроса
# Можно взять из env или прямо задать для теста
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY", "51a90d6ca08b86307dd012f2f137164f2f8b7855520209762de9be33a27b4f30")

# -----------------------
# Твоя функция
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
        
        lottie = None
        if isinstance(extra, dict):
            lottie = extra.get("lottie")

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
            "price": get_gift_price(token_addr)
        })
    return results

# -----------------------
# Тестирование функции
if __name__ == "__main__":
    owner = "UQCO2zbi9Cg3EXUPUCVd6PcrSMPpg6wgysyzVwGzylTvaQI7"
    gifts = get_all_gifts(owner)
    print(f"Найдено NFT: {len(gifts)}")
    for g in gifts:
        print(g)
