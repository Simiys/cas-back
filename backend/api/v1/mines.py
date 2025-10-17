from fastapi import APIRouter, Depends, HTTPException, Header, Body
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.auth_service import AuthService
from shared_models.db import get_session

from backend.services.mines_service import MinesService  

router = APIRouter(
    prefix="/mines",
    tags=["mines"]
)

auth_service = AuthService()  
mines_service = MinesService()  

# -----------------------
# Schemas
# -----------------------
class StartGameRequest(BaseModel):
    mines: int
    bet: float

class OpenCellResponse(BaseModel):
    win: float
    isEnd: bool
    totalWin: Optional[float]

class EndGameResponse(BaseModel):
    totalWin: float


# -----------------------
# /mines/startGame
# -----------------------
@router.post("/startGame")
async def start_game(
    payload: StartGameRequest = Body(...),
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
        game = await mines_service.create_game(db, user_id, payload.bet, payload.mines)
        return {"message": "Game started", "gameId": game.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
# /mines/openCell
# -----------------------
@router.post("/openCell", response_model=OpenCellResponse)
async def open_cell(
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

    result = await mines_service.process_open_cell(db, user_id)
    return result
