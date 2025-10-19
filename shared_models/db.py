import asyncio
from contextlib import asynccontextmanager
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .base import Base
from typing import AsyncGenerator
from shared_models.models import * 
import shared_models.models  

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine: "AsyncEngine | None" = None
SessionLocal: "async_sessionmaker[AsyncSession] | None" = None


async def create_engine_with_retry(retries=10, delay=3):
    """
    Создаёт асинхронный движок и sessionmaker с повторными попытками подключения.
    """
    global engine, SessionLocal
    for attempt in range(1, retries + 1):
        try:
            engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                future=True,
            )

            # Тестовое подключение
            async with engine.begin() as conn:
                await conn.run_sync(lambda conn: None)

            # Асинхронный sessionmaker
            SessionLocal = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            print("✅ Подключение к базе установлено")
            return
        except Exception as e:
            print(f"⚠️ Попытка {attempt} не удалась: {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                raise e


async def init_db():
    """
    Инициализация базы данных: создаёт таблицы.
    """
    if engine is None or SessionLocal is None:
        await create_engine_with_retry()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы / проверены")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        await create_engine_with_retry()
    async with SessionLocal() as session:
        yield session