from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from models import MinesGame
from schemas.mines_game import MinesGameCreate, MinesGameUpdate

# ===========================
# CREATE
# ===========================
async def create_game(db: AsyncSession, game_in: MinesGameCreate) -> MinesGame:
    game = MinesGame(
        user_id=game_in.user_id,
        bet=game_in.bet,
        num_mines=game_in.num_mines,
        won_amount=game_in.won_amount,
        result_data=game_in.result_data,
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game

# ===========================
# READ по ID
# ===========================
async def get_game(db: AsyncSession, game_id: int) -> Optional[MinesGame]:
    result = await db.execute(select(MinesGame).where(MinesGame.id == game_id))
    return result.scalar_one_or_none()

# ===========================
# READ все игры
# ===========================
async def get_all_games(db: AsyncSession) -> List[MinesGame]:
    result = await db.execute(select(MinesGame).order_by(MinesGame.started_at.desc()))
    return result.scalars().all()

# ===========================
# READ все игры конкретного пользователя
# ===========================
async def get_user_games(db: AsyncSession, user_id: int) -> List[MinesGame]:
    result = await db.execute(
        select(MinesGame)
        .where(MinesGame.user_id == user_id)
        .order_by(MinesGame.started_at.desc())
    )
    return result.scalars().all()

# ===========================
# UPDATE
# ===========================
async def update_game(db: AsyncSession, game_id: int, game_in: MinesGameUpdate) -> Optional[MinesGame]:
    game = await get_game(db, game_id)
    if not game:
        return None

    if game_in.won_amount is not None:
        game.won_amount = game_in.won_amount
    if game_in.finished_at is not None:
        game.finished_at = game_in.finished_at
    if game_in.result_data is not None:
        game.result_data = game_in.result_data

    await db.commit()
    await db.refresh(game)
    return game

# ===========================
# DELETE
# ===========================
async def delete_game(db: AsyncSession, game_id: int) -> bool:
    game = await get_game(db, game_id)
    if not game:
        return False
    await db.delete(game)
    await db.commit()
    return True
