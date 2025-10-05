from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .gift import GiftRead


class InventoryBase(BaseModel):
    user_id: int
    gift_id: int
    quantity: int = 1


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None


# Расширенная схема с вложенным объектом подарка
class InventoryRead(BaseModel):
    id: int
    user_id: int
    gift: GiftRead
    quantity: int
    received_at: datetime

    class Config:
        orm_mode = True
