from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserResponse
from app.core.security import get_password_hash
from app.core.logger import get_logger
from typing import List, Optional

logger = get_logger(__name__)

class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = UserRepository(db)

    async def create_user(self, user_in: UserCreate) -> str:
        logger.info(f"Створення нового користувача: {user_in.email}, роль: {user_in.role}")
        hashed_password = get_password_hash(user_in.password)
        
        user_dict = user_in.model_dump()
        user_dict["password"] = hashed_password
        
        user_to_db = UserCreate(**user_dict)
        new_user_id = await self.repo.create_user(user_to_db)
        logger.info(f"Користувача {user_in.email} успішно створено з id: {new_user_id}")
        return new_user_id

    async def get_all_users(self) -> List[UserResponse]:
        logger.info("Отримання списку всіх користувачів")
        return await self.repo.get_all_users()

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        logger.info(f"Отримання користувача за id: {user_id}")
        return await self.repo.get_user_by_id(user_id)

    async def deactivate_user(self, user_id: str) -> bool:
        logger.info(f"Спроба деактивації користувача з id: {user_id}")
        from fastapi import HTTPException
        from app.models.user import UserRole
        from app.services.record_service import MedicalRecordService
        
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Користувача {user_id} не знайдено для деактивації")
            raise HTTPException(status_code=404, detail="Користувача не знайдено")
            
        if user.role != UserRole.PATIENT:
            logger.warning(f"Спроба деактивувати не пацієнта: {user.role}")
            raise HTTPException(status_code=400, detail="Можна деактивувати тільки пацієнтів")

        success = await self.repo.update_user_status(user_id, False)
        if success:
            logger.info(f"Користувача {user_id} успішно деактивовано")
            record_service = MedicalRecordService(self.db)
            await record_service.deactivate_cards_by_patient(user_id)
        else:
            raise HTTPException(status_code=400, detail="Не вдалося деактивувати")
        return True
