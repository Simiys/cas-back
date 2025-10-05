from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Базовая схема (общие поля)
class WalletBase(BaseModel):
    wallet_address: str
    wallet_type: str  # ton, ethereum и т.д.


# Создание кошелька
class WalletCreate(WalletBase):
    user_id: int


# Обновление кошелька (например, смена типа или адреса)
class WalletUpdate(BaseModel):
    wallet_address: Optional[str] = None
    wallet_type: Optional[str] = None


# Схема для отображения (чтения)
class WalletRead(WalletBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
