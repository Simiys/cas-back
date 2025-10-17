import random
from sqlalchemy.orm import Session
from shared_models.models import Gift
from shared_models.crud.gift import get_all_gifts
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.crud.user import get_user_by_id
from shared_models.schemas.lottery_ticket import LotteryTicketCreate
from shared_models.crud.lottery_tickets import create_lottery_ticket


TICKET_PRICES = {
    "bronze": {"hrpn": 1000, "ton": 1},
    "silver": {"hrpn": 10000, "ton": 10},
    "gold": {"hrpn": 100000, "ton": 100}
}

TICKET_PRICES = {
    "bronze": 1000,
    "silver": 10000,
    "gold": 100000,
}

TICKET_WIN_COUNTS = {
    "bronze": 1,
    "silver": 2,
    "gold": 4,
}

TON_TO_HRPN = 1000  # курс TON → HRPN

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
    else:  # ton
        if user.ton_balance < ticket_cost:
            raise ValueError("Not enough ton")
        user.ton_balance -= ticket_cost

    await db.commit()
    await db.refresh(user)

    wins = await generate_wins(db, user_id=user_id, ticket_type=ticket_type)

    ticket_in = LotteryTicketCreate(
        user_id=user_id,
        currency=currency,
        ticket_type=ticket_type,
        price=ticket_cost,
        won_gift_ids=[g.id for g in wins] if wins else []
    )
    ticket = await create_lottery_ticket(db, ticket_in)

    return {
        "ticket": ticket,
        "wins": wins
    }

def get_gift_value_hrpn(gift: Gift) -> float:
    """Возвращает стоимость подарка в HRPN."""
    if gift.cost_coins is not None:
        return gift.cost_coins
    if gift.cost_ton is not None:
        return gift.cost_ton * TON_TO_HRPN
    return 0.0


def generate_wins(db: Session, user_id: int, ticket_type: str):
    """Генерация выигрышей: шанс окупиться, но долгосрочный минус."""
    gifts = db.query(Gift).all()
    if not gifts:
        return []

    ticket_price = TICKET_PRICES[ticket_type]
    max_prizes = TICKET_WIN_COUNTS[ticket_type]

    # 🎯 Шаг 1. Определяем мультипликатор выигрыша
    r = random.random()
    if r < 0.10:
        # 10% — ничего
        return []
    elif r < 0.30:
        # 20% — окупаемость/плюс
        multiplier = random.uniform(1.0, 1.5)
    elif r < 0.80:
        # 50% — средний возврат
        multiplier = random.uniform(0.6, 1.0)
    else:
        # 20% — слабый выигрыш
        multiplier = random.uniform(0.2, 0.6)

    total_win_value = ticket_price * multiplier

    # 🎯 Шаг 2. Разбиваем выигрыш на части (если несколько призов)
    parts = []
    remaining = total_win_value
    for i in range(max_prizes):
        if i == max_prizes - 1:
            parts.append(remaining)
        else:
            part = remaining * random.uniform(0.2, 0.5)
            parts.append(part)
            remaining -= part

    # 🎯 Шаг 3. Подбор подарков под каждую часть
    wins = []
    for value in parts:
        # вычисляем стоимость каждого подарка в HRPN
        suitable = [g for g in gifts if get_gift_value_hrpn(g) <= value]

        if suitable:
            chosen = max(suitable, key=lambda g: get_gift_value_hrpn(g))
        else:
            chosen = min(gifts, key=lambda g: get_gift_value_hrpn(g))

        wins.append(chosen)

    return wins