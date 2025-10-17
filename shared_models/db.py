import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .base import Base
from typing import AsyncGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в shared_models/.env")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,       # Лучше выключить SQL-лог на проде
    future=True,
    pool_size=10,
    max_overflow=5
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db():
    """
    Инициализация базы данных.
    Проверка и создание таблиц, если их нет.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы / проверены")
        

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()