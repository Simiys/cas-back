import asyncio
from shared_models.db import init_db

async def main():
    # Инициализация базы данных
    await init_db()
    print("✅ Shared_models готов и запущен")
    
    # Держим контейнер живым, чтобы его можно было монтировать как volume
    while True:
        await asyncio.sleep(3600)  # спим по часу, пока контейнер жив

if __name__ == "__main__":
    asyncio.run(main())
