from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransactionBase(BaseModel):
    type: str  # deposit, ton_withdrawal, gift_withdrawal, gift_sale, 
    amount: Optional[float] = None
    tx_hash: Optional[str] = None
    gift_id: Optional[int] = None
    status: Optional[str] = "pending"

class TransactionCreate(TransactionBase):
    user_id: int

class TransactionUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    tx_hash: Optional[str] = None

class TransactionRead(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True
