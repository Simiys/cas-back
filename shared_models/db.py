import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .base import Base
from typing import AsyncGenerator

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = None
SessionLocal = None

async def create_engine_with_retry(retries=10, delay=3):
    global engine, SessionLocal
    for attempt in range(1, retries + 1):
        try:
            engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                future=True,
                pool_size=10,
                max_overflow=5
            )
            # Тестовое подключение
            async with engine.begin() as conn:
                await conn.run_sync(lambda conn: None)
            
            SessionLocal = sessionmaker(
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
    Инициализация базы данных с повторными попытками подключения.
    """
    if engine is None or SessionLocal is None:
        await create_engine_with_retry()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы / проверены")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        await create_engine_with_retry()
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
