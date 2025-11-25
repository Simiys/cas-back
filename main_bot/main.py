import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import uuid

# Подключаем общие модели
from shared_models.db import get_context_manager, create_engine_with_retry, init_db
from shared_models.crud.user import create_user
from shared_models.schemas.user import UserCreate

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

AVATAR_DIR = Path("/app/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)



# ---------- Хелпер для загрузки аватара ----------
async def download_avatar(file_id: str, tg_id: int):
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        avatar_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        save_path = AVATAR_DIR / f"{tg_id}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    with open(save_path, "wb") as f:
                        f.write(await resp.read())
                    return str(save_path)
    except Exception as e:
        print(f"Ошибка при загрузке аватара: {e}")
    return None


# ---------- Генерация реферального кода ----------
def generate_ref_code():
    return str(uuid.uuid4())[:8]


# ---------- Команда /start ----------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
   async with get_context_manager() as db:  # получаем сессию
        tg_user = message.from_user
        username = tg_user.username or f"user_{tg_user.id}"
        name = tg_user.full_name
        chat_id = message.chat.id
        tg_id = tg_user.id

        # Получаем реферальный код из ссылки, если есть
        ref_by = None
        if message.text:
            parts = message.text.split(maxsplit=1)
            if len(parts) > 1:
                ref_by = parts[1].strip()  # сохраняем код

        # Загружаем аватар (если есть)
        avatar_url = None
        try:
            photos = await bot.get_user_profile_photos(tg_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id  # берем фото максимального качества
                avatar_url = await download_avatar(file_id, tg_id)
        except Exception as e:
            print(f"Ошибка получения аватара: {e}")

        # Создаём объект пользователя
        user_data = UserCreate(
            username=username,
            tg_id=tg_id,
            name=name,
            chat_id=chat_id,
            avatar_url=avatar_url,
            ref_code=generate_ref_code(),
            ref_by=ref_by,
            coins_balance=10000,
            ton_balance=1000                
        )
        


        
        try:
            new_user = await create_user(db, user_data)
            await message.answer(
                f"✅ Привет, {name}!\n"
                f"Ты успешно зарегистрирован 🎉\n\n"
                f"💎 Баланс: {user_data.coins_balance} HRPN\n"
                f"⚪ Баланс: {user_data.ton_balance} TON"
            )
        except Exception as e:
            await message.answer("⚠️ Пользователь уже существует или произошла ошибка.")


# ---------- Точка входа ----------
async def main():
    await create_engine_with_retry()
    await init_db()      
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
