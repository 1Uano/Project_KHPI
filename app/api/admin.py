from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

# Імпортуємо твої моделі та залежність для бази
from app.models.user import UserCreate
from app.database.db import get_database  # Твій шлях до файлу з базою
from app.repositories.user_repository import UserRepository

# Створюємо роутер із префіксом
router = APIRouter(prefix="/admin", tags=["Admin Testing"])

@router.post("/users/")
async def create_test_user(
        user_in: UserCreate,
        db: AsyncIOMotorDatabase = Depends(get_database)
):
    # 1. Ініціалізуємо репозиторій, передаючи йому підключення до БД
    repo = UserRepository(db)

    # 2. Викликаємо метод створення
    new_user_id = await repo.create_user(user_in)

    # 3. Повертаємо радісну звістку
    return {
        "message": "Ура! Користувач успішно створений у MongoDB!",
        "user_id": new_user_id
    }