from pydantic import BaseModel
from datetime import datetime
from shared_models.schemas.gift import GiftRead


class InventoryBase(BaseModel):
    user_id: int
    gift_id: int


class InventoryCreate(InventoryBase):
    pass


# Расширенная схема с вложенным объектом подарка
class InventoryRead(BaseModel):
    id: int
    user_id: int
    gift: GiftRead
    received_at: datetime

    class Config:
        orm_mode = True
