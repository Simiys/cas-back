import asyncio
import shared_models.models
from shared_models.db import init_db, create_engine_with_retry

async def main():
    await create_engine_with_retry()  # создаём движок и sessionmaker
    await init_db()                   # создаём таблицы
    print("✅ Shared_models готов и таблицы созданы")
    
    while True:
        await asyncio.sleep(3600)    # держим контейнер живым

if __name__ == "__main__":
    asyncio.run(main())
