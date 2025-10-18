from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Базовая схема (общие поля)
class GiftBase(BaseModel):
    name: str
    telegram_gift_id: str
    cost_coins: float
    cost_ton: Optional[float] = None
    image_url: str


# Создание подарка (админом или системой)
class GiftCreate(GiftBase):
    pass


# Обновление подарка
class GiftUpdate(BaseModel):
    name: Optional[str] = None
    cost_coins: Optional[float] = None
    cost_ton: Optional[float] = None


# Схема для отображения (чтения)
class GiftRead(GiftBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
