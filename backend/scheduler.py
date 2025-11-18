# backend/scheduler.py
import os
import asyncio
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.services.async_services import process_pending_deposits
from backend.services.wallet_service import get_all_gifts
from shared_models.db import get_context_manager
from shared_models.schemas.gift import GiftCreate
from shared_models.crud.gift import create_gift

load_dotenv()
APP_WALLET_ADDRESS = os.getenv("APP_WALLET_ADDRESS", "")

scheduler = AsyncIOScheduler()


def start_scheduler():

    # -----------------------
    # 1) ПЕРВАЯ async задача
    # -----------------------
    async def process_deposits_job():
        async with get_context_manager() as db:
            await process_pending_deposits(db)

    scheduler.add_job(
        process_deposits_job,
        trigger=IntervalTrigger(minutes=10),
        id="process_pending_deposits",
        replace_existing=True
    )

    # -----------------------
    # 2) Вторая async задача
    # -----------------------
    async def fetch_and_store_gifts_job():
        async with get_context_manager() as db:
            try:
                gifts = get_all_gifts(APP_WALLET_ADDRESS)

                for gift in gifts:
                    exists = await db.execute(
                        "SELECT 1 FROM gifts WHERE address = :addr",
                        {"addr": gift["address"]}
                    )

                    if not exists.scalar():
                        gift_in = GiftCreate(
                            name=gift["name"],
                            address=gift["address"],
                            cost_ton=gift["price"],
                            image_url=gift["image"],
                            lottie_url=gift["lottie"],
                        )
                        await create_gift(db, gift_in)

            except Exception as e:
                print(f"[Scheduler] Error fetching/storing gifts: {e}")

    scheduler.add_job(
        fetch_and_store_gifts_job,
        trigger=IntervalTrigger(hours=1),
        id="fetch_and_store_gifts",
        replace_existing=True
    )

    scheduler.start()
