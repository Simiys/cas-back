# backend/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.services.async_services import process_pending_deposits
from shared_models.db import get_context_manager
import asyncio

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
        trigger=IntervalTrigger(hours=1),
        id="process_pending_deposits",
        replace_existing=True
    )
    scheduler.start()
