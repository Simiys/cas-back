from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from shared_models.models import TicketTypeEnum, Currency

class LotteryTicketBase(BaseModel):
    ticket_type: TicketTypeEnum
    currency: Currency
    price: float
    won_gift_ids: Optional[List[int]] = []

class LotteryTicketCreate(LotteryTicketBase):
    user_id: int

class LotteryTicketUpdate(BaseModel):
    won_gift_ids: Optional[List[int]] = None

class LotteryTicketRead(LotteryTicketBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
