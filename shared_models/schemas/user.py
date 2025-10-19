from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from shared_models.schemas.inventory import InventoryRead  # <-- импортируем вложенную схему

class UserBase(BaseModel):
    name: Optional[str] = None
    username: str
    tg_id: int
    ref_code: str
    ref_by: Optional[str] = None
    ton_balance: float = 0.0
    coins_balance: float = 0.0

class UserCreate(BaseModel):
    username: str
    tg_id: int
    name: Optional[str] = None
    chat_id: int
    avatar_url: str
    ref_code: str
    ref_by: Optional[str] = None
    ton_balance: float = 0.0
    coins_balance: float = 0.0

class UserUpdate(BaseModel):
    ton_balance: Optional[float] = None
    coins_balance: Optional[float] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    avatar_url: str
    ref_code: str
    ref_by: Optional[str] = None
    inventory: Optional[List[InventoryRead]] = [] 

    class Config:
        orm_mode = True
