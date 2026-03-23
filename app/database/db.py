from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def get_database():
    """Dependency для отримання доступу до бази в роутерах"""
    return db.client[settings.DATABASE_NAME]