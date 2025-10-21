import random
import json
from redis import asyncio as aioredis
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.crud.user import get_user_by_id, update_user_balance

class MinesService:
    def __init__(self, redis: aioredis.Redis, game_ttl: int = 1200):
        """
        redis: асинхронный клиент Redis
        game_ttl: время жизни игры в секундах (по умолчанию 20 минут)
        """
        self.redis = redis
        self.game_ttl = game_ttl  # 20 минут

    # -----------------------------
    # Генерация ключа в Redis
    # -----------------------------
    def _redis_key(self, user_id: int) -> str:
        return f"mines_game:{user_id}"

    # -----------------------------
    # Создание игры
    # -----------------------------
    async def create_game(self, db: AsyncSession, user_id: int, bet_ton: float, mines: int):

        if mines < 1 or mines > 24:
            raise ValueError("Количество мин должно быть от 1 до 24")

        user = await get_user_by_id(db, user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        if user.ton_balance < bet_ton:
            raise ValueError("Недостаточно TON для ставки")

        await update_user_balance(db, user_id, ton_balance=user.ton_balance - bet_ton)

        bet_hrpn = bet_ton * 1000

        game_data = {
            "user_id": user_id,
            "bet": bet_hrpn,
            "mines": mines,
            "opened_cells": 0,
            "total_win": 0.0,
            "remaining_cells": 25,
            "remaining_mines": mines,
            "base_multiplier": 0.6
        }

        key = self._redis_key(user_id)
        await self.redis.set(key, json.dumps(game_data), ex=self.game_ttl)
        return game_data


    async def process_open_cell(self, db: AsyncSession, user_id: int) -> dict:
        key = self._redis_key(user_id)
        data_raw = await self.redis.get(key)
        if not data_raw:
            raise ValueError("Игра не найдена или уже завершена")

        game = json.loads(data_raw)
        remaining_cells = game["remaining_cells"]
        remaining_mines = game["remaining_mines"]
        if remaining_cells <= 0:
            raise ValueError("Все клетки уже открыты")

        p_mine = remaining_mines / remaining_cells
        is_mine = random.random() < p_mine

        if is_mine:
            await self.redis.delete(key)
            return {"win": round(win_per_cell, 2), "isEnd": is_end, "totalWin": round(total_win, 2)}

        bet = game["bet"]
        base_multiplier = game["base_multiplier"]
        mines = game["mines"]

        win_per_cell = bet * base_multiplier * (25 / (25 - mines))

    # Обновляем состояние игры
        game["opened_cells"] += 1
        game["remaining_cells"] -= 1
        game["total_win"] += win_per_cell

    # Проверяем, закончилась ли игра
        is_end = game["opened_cells"] >= (25 - mines)
        total_win = 0.0
        if is_end:
            # Начисляем выигрыш пользователю
            user = await get_user_by_id(db, user_id)
            if user:
                new_balance = user.coins_balance + game["total_win"]
                await update_user_balance(db, user_id, coins_balance=new_balance)
                total_win = game["total_win"]

        # Удаляем игру из Redis
            await self.redis.delete(key)
        else:
            await self.redis.set(key, json.dumps(game), ex=self.game_ttl)

        return {"win": round(win_per_cell, 2), "isEnd": is_end, "totalWin": round(total_win, 2)}
