from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Базовая схема (общие поля)
class GiftBase(BaseModel):
    name: str
    address: str
    cost_ton: float
    image_url: str
    lottie_url: str
    owner_id: Optional[int] = None


# Создание подарка (админом или системой)
class GiftCreate(GiftBase):
    pass


# Обновление подарка
class GiftUpdate(BaseModel):
    name: Optional[str] = None
    cost_ton: Optional[float] = None


# Схема для отображения (чтения)
class GiftRead(GiftBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
