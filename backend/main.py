
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from backend.dependencies import get_redis
# from config import get_settings


#импорт роутеров
from backend.api.v1 import profile
from backend.api.v1 import mines
from backend.api.v1 import tickets
from backend.api.v1 import balance
from backend.api.v1 import auth
from backend.api.v1 import inventory



# settings = get_settings()

app = FastAPI(
    title="Telegram Mini App Backend",
    version="1.0.0",
    description="Backend API for Telegram Mini App"
)

# -----------------------
# CORS
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Startup / Shutdown events
# -----------------------
@app.on_event("startup")
async def startup_event():
    """
    Здесь можно инициализировать Redis и другие сервисы
    """
    redis = await get_redis()
    if redis:
        print("Redis connected")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Здесь можно закрыть соединения с Redis и другими сервисами
    """
    redis = await get_redis()
    if redis:
        await redis.close()
        print("Redis disconnected")

#подключение
app.include_router(profile.router)
app.include_router(mines.router)
app.include_router(tickets.router)
app.include_router(balance.router)
app.include_router(auth.router)
app.include_router(inventory.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
