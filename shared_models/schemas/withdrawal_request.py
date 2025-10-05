from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WithdrawalRequestBase(BaseModel):
    gift_id: Optional[int] = None
    amount: float
    status: Optional[str] = "pending"  # pending, completed, rejected

class WithdrawalRequestCreate(WithdrawalRequestBase):
    user_id: int

class WithdrawalRequestUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None

class WithdrawalRequestRead(WithdrawalRequestBase):
    id: int
    user_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
