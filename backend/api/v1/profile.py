from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.services.auth_service import AuthService
from shared_models.db import get_session  # предполагаем, что есть зависимости
from shared_models.schemas.user import UserResponse
from shared_models.crud.user import get_top_users_by_coins, get_user_by_id

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

auth_service = AuthService()
# ------------------------
# Эндпоинты профиля
# ------------------------

@router.get("/me", response_model=UserResponse)
async def profile_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        token = authorization.split(" ")[1]
        user_id = auth_service.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/getLadder", response_model=List[UserResponse])
async def profile_get_ladder(
    db: AsyncSession = Depends(get_session),
):

    users = await get_top_users_by_coins(db, limit=100)
    return users

@router.get("/getTasks")
async def profile_get_tasks():
    # Пока пустой метод
    return []

@router.post("/startTask")
async def profile_start_task(id: int):
    # Пока пустой метод
    return {"status": "started", "task_id": id}

@router.post("/finishTask")
async def profile_finish_task(id: int):
    # Пока пустой метод
    return {"status": "finished", "task_id": id}
