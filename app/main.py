from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.database.db import db

from app.api.admin import router as admin_router
from app.api.records import router as records_router
from app.api.prescription import router as precription_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    print(f"🚀 Connected to MongoDB: {settings.DATABASE_NAME}")
    yield
    db.client.close()
    print("💤 MongoDB connection closed")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(admin_router)
app.include_router(precription_router)
app.include_router(records_router)
@app.get("/health")
async def health_check():
    return {"status": "ok", "database": settings.DATABASE_NAME}