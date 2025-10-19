from fastapi import APIRouter, Depends, HTTPException, Header, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.db import get_session
from backend.services.auth_service import AuthService
from typing import Optional

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# --- Pydantic модели ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    username: str
    coins_balance: float
    ton_balance: float

# -----------------------
# Авторизация через Telegram WebApp
# -----------------------
@router.post("", response_model=TokenResponse)
async def login(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_session),
):
    """
    Получает init_data от Telegram WebApp и возвращает JWT.
    """
    init_data = payload.get("init_data")
    if not init_data:
        raise HTTPException(status_code=400, detail="init_data missing")

    auth_service = AuthService()
    async with get_session() as db:
        token = await auth_service.login_via_telegram(db, init_data)

    return TokenResponse(access_token=token)

# -----------------------
# Получение профиля текущего пользователя
# -----------------------
@router.get("/me", response_model=UserResponse)
async def get_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
):
    """
    Возвращает данные пользователя по JWT в заголовке Authorization.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Получаем сам токен из заголовка
    token = authorization.replace("Bearer ", "")
    auth_service = AuthService()

    try:
        # Извлекаем user_id из токена
        user_id = auth_service.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Получаем пользователя из БД по id
    from shared_models.crud.user import get_user_by_id
    async with get_session() as db:
        user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        coins_balance=user.coins_balance,
        ton_balance=user.ton_balance
    )

