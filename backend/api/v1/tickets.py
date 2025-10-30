from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from shared_models.db import get_session 
from services.ticket_service import buy_ticket
from shared_models.schemas.gift import GiftRead
from typing import List, Optional
from services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.db import get_session
from shared_models.schemas.lottery_ticket import LotteryTicketRead

router = APIRouter()

auth_service = AuthService()  # автоматически берёт SECRET_KEY из settings

@router.post("/tickets/buy")
async def buy_ticket_endpoint(
    ticket_type: str = Query(...),
    currency: str = Query(...),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    try:
        user_id = auth_service.decode_access_token(token)
    except HTTPException as e:
        raise e

    try:
        result = await buy_ticket(db, user_id, ticket_type, currency)
        # result = { "ticket": ..., "wins": ..., "won_items": ... }
        return {
            "ticket": result["ticket"],
            "wins": result["wins"],
            "won_items": result["won_items"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))