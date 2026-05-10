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

    async def get_all_users(
        self,
        role: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: int = 1
    ) -> List[UserResponse]:
        logger.info(f"Отримання списку користувачів з фільтрами: role={role}, search={search}, sort_by={sort_by}")
        return await self.repo.get_all_users(
            role=role, search=search, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order
        )

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        logger.info(f"Отримання користувача за id: {user_id}")
        return await self.repo.get_user_by_id(user_id)

    async def deactivate_user(self, user_id: str, new_doctor_id: Optional[str] = None) -> bool:
        logger.info(f"Спроба деактивації користувача з id: {user_id}")
        from fastapi import HTTPException
        from app.models.user import UserRole
        from app.services.record_service import MedicalRecordService
        from app.services.prescription_service import PrescriptionService
        
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Користувача {user_id} не знайдено для деактивації")
            raise HTTPException(status_code=404, detail="Користувача не знайдено")
            
        if user.role == UserRole.DOCTOR:
            if not new_doctor_id:
                raise HTTPException(status_code=400, detail="Для деактивації лікаря необхідно вказати нового лікуючого лікаря для його пацієнтів")
            new_doctor = await self.repo.get_user_by_id(new_doctor_id)
            if not new_doctor or new_doctor.role != UserRole.DOCTOR or not new_doctor.is_active:
                raise HTTPException(status_code=400, detail="Новий лікар не знайдений, не є лікарем або деактивований")

        success = await self.repo.update_user_status(user_id, False)
        if success:
            logger.info(f"Користувача {user_id} успішно деактивовано")
            if user.role == UserRole.PATIENT:
                record_service = MedicalRecordService(self.db)
                await record_service.deactivate_cards_by_patient(user_id)
            elif user.role == UserRole.DOCTOR:
                record_service = MedicalRecordService(self.db)
                await record_service.reassign_doctor_records(user_id, new_doctor_id)
            elif user.role == UserRole.NURSE:
                prescription_service = PrescriptionService(self.db)
                await prescription_service.reassign_nurse_prescriptions(user_id)
        else:
            raise HTTPException(status_code=400, detail="Не вдалося деактивувати")
        return True
