from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from shared_models.db import get_context_manager   # <-- твой файл где код сверху
from services.async_services import process_pending_deposits

scheduler = AsyncIOScheduler()

async def deposit_check_job():
    async with get_context_manager() as session:   # <-- вместо async_sessionmaker
        await process_pending_deposits(session)

def start_scheduler():
    scheduler.add_job(deposit_check_job, IntervalTrigger(minutes=60))
    scheduler.start()
