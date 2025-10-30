from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from shared_models.models import TicketTypeEnum, Currency


# ---------------------------
# Базовая схема
# ---------------------------
class LotteryTicketBase(BaseModel):
    ticket_type: TicketTypeEnum
    currency: Currency
    price: float
    won_items: List[str] = Field(
        default_factory=lambda: ["0", "0", "0", "0"],
        description="Массив из 4 элементов. Формат элементов: '<value>_<type>' (пример: '1_ton', '120_gift', '0')"
    )


# ---------------------------
# Создание билета
# ---------------------------
class LotteryTicketCreate(LotteryTicketBase):
    user_id: int


# ---------------------------
# Обновление (например, при выдаче выигрыша)
# ---------------------------
class LotteryTicketUpdate(BaseModel):
    won_items: Optional[List[str]] = None


# ---------------------------
# Чтение (из БД наружу)
# ---------------------------
class LotteryTicketRead(LotteryTicketBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
