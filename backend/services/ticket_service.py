import random
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.models import Gift
from shared_models.crud.gift import get_all_gifts
from shared_models.crud.user import get_user_by_id
from shared_models.schemas.lottery_ticket import LotteryTicketCreate
from shared_models.crud.lottery_tickets import create_lottery_ticket

# Цены билетов
TICKET_PRICES = {
    "bronze": {"hrpn": 1000, "ton": 1},
    "silver": {"hrpn": 10000, "ton": 10},
    "gold": {"hrpn": 100000, "ton": 100},
}

# Количество возможных выигрышей
TICKET_WIN_COUNTS = {
    "bronze": 1,
    "silver": 2,
    "gold": 4,
}

TON_TO_HRPN = 1000  # курс TON → HRPN

# 🎁 Пул призов в hrpn
PRIZE_POOL_HRPN = [50, 100, 200, 300, 500, 1000, 2000, 5000]

# Вероятности типов призов
PRIZE_TYPE_WEIGHTS = {
    "hrpn": 0.4,   # 45%
    "ton": 0.4,    # 45%
    "gift": 0.20    # 10%
}

async def buy_ticket(db: AsyncSession, user_id: int, ticket_type: str, currency: str):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    # -------------------
    # Проверка баланса
    # -------------------
    ticket_cost = TICKET_PRICES[ticket_type][currency]
    if currency == "hrpn":
        if user.coins_balance < ticket_cost:
            raise ValueError("Not enough coins")
        user.coins_balance -= ticket_cost
    else:
        if user.ton_balance < ticket_cost:
            raise ValueError("Not enough ton")
        user.ton_balance -= ticket_cost

    await db.commit()
    await db.refresh(user)

    # -------------------
    # Генерация выигрышей
    # -------------------
    wins = await generate_wins(db, user_id, ticket_type)

    # Преобразуем выигрыш в формат ["1_ton", "1000_hrpn", "120_gift", "0"]
    won_items = []
    for w in wins:
        if w["type"] == "ton":
            won_items.append(f"{w['value_ton']:.3f}_ton")
        elif w["type"] == "hrpn":
            won_items.append(f"{int(w['value_hrpn'])}_hrpn")
        elif w["type"] == "gift":
            won_items.append(f"{w['gift_id']}_gift")
        else:
            won_items.append("0")

    # Дополняем массив до 4 элементов
    while len(won_items) < 4:
        won_items.append("0")

    ticket_in = LotteryTicketCreate(
        user_id=user_id,
        currency=currency,
        ticket_type=ticket_type,
        price=ticket_cost,
        won_items=won_items
    )

    ticket = await create_lottery_ticket(db, ticket_in)

    return {
        "ticket": ticket,
        "wins": wins,
        "won_items": won_items
    }


async def generate_wins(db: AsyncSession, user_id: int, ticket_type: str):
    """Генерирует список выигрышей с учетом RTP и вероятностей типов призов."""
    result = await get_all_gifts(db)
    gifts = result.scalars().all() or []

    max_prizes = TICKET_WIN_COUNTS[ticket_type]
    ticket_price_hrpn = TICKET_PRICES[ticket_type]["hrpn"]

    # 🎯 RTP — оставляем примерно тот же
    # 80% от стоимости билета возвращается игроку
    target_total_value = ticket_price_hrpn * random.uniform(0.5, 0.9)

    # Делим общий выигрыш на несколько частей
    parts = []
    remaining = target_total_value
    for i in range(max_prizes):
        if i == max_prizes - 1:
            parts.append(remaining)
        else:
            part = remaining * random.uniform(0.2, 0.5)
            parts.append(part)
            remaining -= part

    # 🎯 Теперь определяем тип каждого приза
    wins = []
    for value in parts:
        prize_type = random.choices(
            population=list(PRIZE_TYPE_WEIGHTS.keys()),
            weights=list(PRIZE_TYPE_WEIGHTS.values()),
            k=1
        )[0]

        if prize_type in ("hrpn", "ton"):
            # Выбираем ближайшее значение из пула
            hrpn_value = min(PRIZE_POOL_HRPN, key=lambda x: abs(x - value))
            ton_value = hrpn_value / TON_TO_HRPN
            wins.append({
                "type": prize_type,
                "value_hrpn": hrpn_value,
                "value_ton": ton_value if prize_type == "ton" else None,
                "gift_id": None
            })
        else:  # 🎁 подарок
            if not gifts:
                continue
            suitable = [g for g in gifts if g.cost_ton * TON_TO_HRPN <= value]
            chosen = random.choice(suitable or gifts)
            wins.append({
                "type": "gift",
                "value_hrpn": chosen.cost_ton * TON_TO_HRPN,
                "value_ton": chosen.cost_ton,
                "gift_id": chosen.id
            })

    return wins
