from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime
from fastapi import HTTPException

from app.models.prescriptions import PrescriptionCreate, PrescriptionResponse
from app.models.user import UserRole, UserResponse
from app.repositories.prescriptions_repository import PrescriptionRepository
from app.core.logger import get_logger

logger = get_logger(__name__)

class PrescriptionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = PrescriptionRepository(db)

    async def create_prescription(self, prescription_in: PrescriptionCreate) -> str:
        logger.info(f"Створення нового призначення для картки: {prescription_in.record_id}")
        new_prescription_id = await self.repo.create_prescription(prescription_in)
        return new_prescription_id

    async def get_all_prescriptions(self) -> List[PrescriptionResponse]:
        logger.info("Отримання списку всіх призначень")
        return await self.repo.get_all()

    async def get_prescription_by_id(self, prescription_id: str) -> PrescriptionResponse:
        logger.info(f"Отримання призначення: {prescription_id}")
        prescription = await self.repo.get_by_id(prescription_id)
        if not prescription:
            logger.warning(f"Призначення {prescription_id} не знайдено")
            raise HTTPException(status_code=404, detail="Призначення не знайдено")
        return prescription

    async def get_prescriptions_by_record(self, record_id: str) -> List[PrescriptionResponse]:
        logger.info(f"Отримання призначень для картки: {record_id}")
        return await self.repo.get_by_record(record_id)

    async def get_my_prescriptions(self, user_id: str) -> List[PrescriptionResponse]:
        logger.info(f"Отримання призначень для користувача: {user_id}")
        return await self.repo.get_assigned_to(user_id)

    async def execute_prescription(self, prescription_id: str, current_user: UserResponse) -> bool:
        logger.info(f"Спроба виконання призначення {prescription_id} користувачем {current_user.id}")
        prescription = await self.repo.get_by_id(prescription_id)
        if not prescription:
            logger.warning(f"Призначення {prescription_id} не знайдено")
            raise HTTPException(status_code=404, detail="Призначення не знайдено")
            
        if isinstance(prescription, dict):
            p_type = prescription.get("type")
        else:
            p_type = getattr(prescription, "type", None)
            if p_type and hasattr(p_type, "value"):
                p_type = p_type.value # handle enum
        
        # Check permissions
        if current_user.role == UserRole.NURSE and p_type == "SURGERY":
            logger.warning(f"Медсестра {current_user.id} намагалась виконати операцію {prescription_id}")
            raise HTTPException(status_code=403, detail="Медсестра не може виконувати операції")
            
        await self.repo.execute_prescription(prescription_id, datetime.utcnow())
        logger.info(f"Призначення {prescription_id} успішно виконано")
        return True

    async def update_prescription_assignee(self, prescription_id: str, new_assignee: str) -> bool:
        logger.info(f"Оновлення виконавця для призначення {prescription_id} на {new_assignee}")
        prescription = await self.repo.get_by_id(prescription_id)
        if not prescription:
            raise HTTPException(status_code=404, detail="Призначення не знайдено")
            
        success = await self.repo.update_assignee(prescription_id, new_assignee)
        if not success:
            logger.error(f"Не вдалося змінити виконавця для призначення {prescription_id}")
            raise HTTPException(status_code=400, detail="Не вдалося змінити виконавця")
            
        return True

    async def deactivate_prescription(self, prescription_id: str, current_user: UserResponse) -> bool:
        logger.info(f"Деактивація призначення: {prescription_id}")
        prescription = await self.repo.get_by_id(prescription_id)
        if not prescription:
            raise HTTPException(status_code=404, detail="Призначення не знайдено")
            
        # Permission check
        if current_user.role != UserRole.ADMIN and prescription.get("prescribed_by") != current_user.email:
            raise HTTPException(status_code=403, detail="Тільки адміністратор або лікар, який призначив, можуть деактивувати")
            
        success = await self.repo.update_status(prescription_id, "CANCELLED")
        if not success:
            raise HTTPException(status_code=400, detail="Не вдалося зберегти зміни")
        return success
