from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.database.db import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Дії при старті:
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    print(f"🚀 Connected to MongoDB: {settings.DATABASE_NAME}")
    yield
    # Дії при вимкненні:
    db.client.close()
    print("💤 MongoDB connection closed")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": settings.DATABASE_NAME}