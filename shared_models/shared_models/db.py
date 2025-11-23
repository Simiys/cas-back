import asyncio
from contextlib import asynccontextmanager
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .base import Base
from typing import AsyncGenerator
from .models import *   # ← исправление
# import shared_models.models  # ← обычно уже не нужно

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_NAME = os.getenv("POSTGRES_DB") or "appdb"

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine: "AsyncEngine | None" = None
SessionLocal: "async_sessionmaker[AsyncSession] | None" = None


async def create_engine_with_retry(retries=10, delay=3):
    global engine, SessionLocal

    for attempt in range(1, retries + 1):
        try:
            engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_recycle=120,
            )

            async with engine.begin() as conn:
                await conn.run_sync(lambda conn: None)

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
                raise


async def init_db():
    if engine is None or SessionLocal is None:
        await create_engine_with_retry()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы / проверены")


@asynccontextmanager
async def get_context_manager() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        await create_engine_with_retry()
    async with SessionLocal() as session:
        yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        await create_engine_with_retry()
    async with SessionLocal() as session:
        yield session
