# backend/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.services.async_services import process_pending_deposits
from backend.services.wallet_service import get_all_gifts
from shared_models.crud.gift import create_gift
from shared_models.db import get_context_manager
import asyncio
import os
from dotenv import load_dotenv
from shared_models.schemas.gift import GiftCreate

load_dotenv()

APP_WALLET_ADDRESS = os.getenv("APP_WALLET_ADDRESS", "")


scheduler = AsyncIOScheduler()

def start_scheduler():
    from datetime import timedelta
    from apscheduler.triggers.interval import IntervalTrigger

    async def job_wrapper():
        async with get_context_manager() as db:
            await process_pending_deposits(db)

    # Обёртка для async job
    def job():
        asyncio.create_task(job_wrapper())

    scheduler.add_job(
        job,
        trigger=IntervalTrigger(minutes=10),
        id="process_pending_deposits",
        replace_existing=True
    )


    async def fetch_and_store_gifts_job():
        async with get_context_manager() as db:  
            try:
                gifts = get_all_gifts(APP_WALLET_ADDRESS)
                for gift in gifts:
                    # Проверяем, есть ли уже такой подарок в базе
                    exists = await db.execute(
                        "SELECT 1 FROM gifts WHERE address = :addr",
                        {"addr": gift["address"]}
                    )
                    if not exists.scalar():  # если нет — создаём
                        gift_in = GiftCreate(
                            name=gift["name"],
                            address=gift["address"],
                            cost_ton=gift["price"],
                            image_url=gift["image"],
                            lottie_url=gift["lottie"]
                        )
                        await create_gift(db, gift_in)
            except Exception as e:
                print(f"[Scheduler] Error fetching/storing gifts: {e}")

    def gifts_wrapper():
        asyncio.create_task(fetch_and_store_gifts_job())

    scheduler.add_job(
        gifts_wrapper,
        trigger=IntervalTrigger(hours=1),
        id="fetch_and_store_gifts",
        replace_existing=True
    )

    scheduler.start()