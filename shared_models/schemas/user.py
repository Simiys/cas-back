from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from inventory import InventoryRead  # <-- импортируем вложенную схему

class UserBase(BaseModel):
    name: Optional[str] = None
    username: str
    tg_id: int
    ton_balance: float = 0.0
    coins_balance: float = 0.0

class UserCreate(BaseModel):
    username: str
    tg_id: int
    name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    ton_balance: Optional[float] = None
    coins_balance: Optional[float] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    inventory: Optional[List[InventoryRead]] = [] 

    class Config:
        orm_mode = True
