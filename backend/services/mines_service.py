import random
import json
from redis import asyncio as aioredis
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from shared_models.crud.user import get_user_by_id, update_user_balance

RTP = 0.85  # целевой RTP ~90%
HOUSE_EDGE = 1 - RTP
N = 25  # всего клеток


class MinesService:
    def __init__(self, redis: aioredis.Redis, game_ttl: int = 1200):
        self.redis = redis
        self.game_ttl = game_ttl

    # -----------------------------
    # Генерация ключа Redis
    # -----------------------------
    def _redis_key(self, user_id: int) -> str:
        return f"mines_game:{user_id}"

    # -----------------------------
    # Генерация коэффициентов
    # -----------------------------
    def generate_coefficients(self, mines: int, h: float = 0.1) -> List[float]:
        """
        Возвращает список коэффициентов M_k для всех безопасных клеток.
        """
        if mines < 1 or mines >= N:
            raise ValueError("Количество мин должно быть от 1 до 24")

        s = N - mines
        coeffs = []

        prob_survive = 1.0
        for i in range(s):
            p_i = float(s - i) / float(N - i)   # вероятность безопасной клетки на шаге i
            prob_survive *= p_i                 # вероятность выжить до и включая этот шаг
            F_k = 1.0 / prob_survive            # fair multiplier (>=1)
            M_k = 1.0 + (F_k - 1.0) * (1.0 - h) # уменьшаем премию над 1 на factor (1-h)
            coeffs.append(round(M_k, 6))

        return coeffs


    # -----------------------------
    # Создание игры
    # -----------------------------
    async def create_game(self, db: AsyncSession, user_id: int, bet: float, mines: int, currency: str):
        if mines < 1 or mines > 24:
            raise ValueError("Количество мин должно быть от 1 до 24")

        user = await get_user_by_id(db, user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        if currency == "ton":
            if user.ton_balance < bet:
                raise ValueError("Недостаточно TON для ставки")
            await update_user_balance(db, user_id, ton_balance=user.ton_balance - bet)
        elif currency == "hrpn":
            if user.coins_balance < bet:
                raise ValueError("Недостаточно HRPN для ставки")
            await update_user_balance(db, user_id, coins_balance=user.coins_balance - bet)
        else:
            raise ValueError("Неверная валюта")

        coeffs = self.generate_coefficients(mines, h=HOUSE_EDGE)

        game_data = {
            "user_id": user_id,
            "bet": bet,
            "currency": currency, 
            "mines": mines,
            "opened_cells": 0,
            "remaining_cells": N,
            "remaining_mines": mines,
            "coeffs": coeffs,
        }

        key = self._redis_key(user_id)
        await self.redis.set(key, json.dumps(game_data), ex=self.game_ttl)
        return game_data

    # -----------------------------
    # Проигрыш
    # -----------------------------
    async def process_lose(self, user_id: int) -> dict:
        key = self._redis_key(user_id)
        await self.redis.delete(key)
        return {
            "coeff": 0.0,
            "totalWin": 0.0,
            "cellNumber": None,
            "isEnd": True
        }

    # -----------------------------
    # Вывод выигрыша
    # -----------------------------
    async def process_cashout(self, db: AsyncSession, user_id: int) -> dict:
        key = self._redis_key(user_id)
        data_raw = await self.redis.get(key)
        if not data_raw:
            raise ValueError("Игра не найдена")

        game = json.loads(data_raw)
        bet = game["bet"]
        currency = game["currency"]
        opened = game["opened_cells"]
        coeffs = game["coeffs"]

        if opened == 0:
            await self.redis.delete(key)
            return {"coeff": 0.0, "totalWin": 0.0, "cellNumber": None, "isEnd": True}

        current_coeff = coeffs[opened - 1]
        total_win = round(bet * current_coeff, 2)

        user = await get_user_by_id(db, user_id)
        if user:
            if currency == "ton":
                new_balance = user.ton_balance + total_win
                await update_user_balance(db, user_id, ton_balance=new_balance)
            elif currency == "hrpn":
                new_balance = user.coins_balance + total_win
                await update_user_balance(db, user_id, coins_balance=new_balance)

        await self.redis.delete(key)
        return {
            "coeff": current_coeff,
            "totalWin": total_win,
            "cellNumber": opened,
            "isEnd": True
        }

    # -----------------------------
    # Открытие клетки
    # -----------------------------
    async def process_open_cell(self, db: AsyncSession, user_id: int) -> dict:
        key = self._redis_key(user_id)
        data_raw = await self.redis.get(key)
        if not data_raw:
            raise ValueError("Игра не найдена или завершена")

        game = json.loads(data_raw)
        remaining_cells = game["remaining_cells"]
        remaining_mines = game["remaining_mines"]
        if remaining_cells <= 0:
            raise ValueError("Все клетки уже открыты")

        # Проверяем мину
        p_mine = remaining_mines / remaining_cells
        is_mine = random.random() < p_mine

        if is_mine:
            return await self.process_lose(user_id)

        # Успешное открытие
        game["opened_cells"] += 1
        game["remaining_cells"] -= 1

        idx = game["opened_cells"] - 1
        coeffs = game["coeffs"]
        current_coeff = coeffs[idx]
        total_win = round(game["bet"] * current_coeff, 2)

        game["total_win"] = total_win
        await self.redis.set(key, json.dumps(game), ex=self.game_ttl)

        is_end = game["opened_cells"] >= (N - game["mines"])

        if is_end:
            return await self.process_cashout(db, user_id)

        return {
            "coeff": current_coeff,
            "totalWin": total_win,
            "cellNumber": game["opened_cells"],
            "isEnd": False
        }
