from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MinesGameBase(BaseModel):
    bet: float
    num_mines: int
    won_amount: Optional[float] = None
    result_data: Optional[str] = None  # JSON строка с состоянием игры

class MinesGameCreate(MinesGameBase):
    user_id: int

class MinesGameUpdate(BaseModel):
    won_amount: Optional[float] = None
    finished_at: Optional[datetime] = None
    result_data: Optional[str] = None

class MinesGameRead(MinesGameBase):
    id: int
    user_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        orm_mode = True
