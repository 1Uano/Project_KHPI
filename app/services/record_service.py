from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException

from app.models.medical_record import MedicalRecordCreate, MedicalRecordResponse
from app.models.user import UserRole, UserResponse
from app.repositories.medrec_repository import MedicalRecordRepository
from app.repositories.prescriptions_repository import PrescriptionRepository
from app.core.logger import get_logger

logger = get_logger(__name__)

class MedicalRecordService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = MedicalRecordRepository(db)
        self.presc_repo = PrescriptionRepository(db)

    async def create_record(self, record_in: MedicalRecordCreate) -> str:
        logger.info(f"Створення медичної картки для пацієнта: {record_in.patient_id} лікарем: {record_in.doctor_id}")
        new_record_id = await self.repo.create_record(record_in)
        return new_record_id

    async def get_all_records(self) -> List[MedicalRecordResponse]:
        logger.info("Отримання списку всіх медичних карток")
        return await self.repo.get_all()

    async def get_record_by_id(self, record_id: str) -> MedicalRecordResponse:
        logger.info(f"Отримання медичної картки: {record_id}")
        record = await self.repo.get_by_id(record_id)
        if not record:
            logger.warning(f"Медичну картку {record_id} не знайдено")
            raise HTTPException(status_code=404, detail="Медичну картку не знайдено")
        return record

    async def update_diagnoses(self, record_id: str, diagnosis: str, secondary_diagnoses: List[str]) -> bool:
        logger.info(f"Оновлення діагнозів для картки: {record_id}")
        success = await self.repo.update_record_diagnoses(record_id, diagnosis, secondary_diagnoses)
        if not success:
            logger.warning(f"Не вдалося оновити діагнози для картки: {record_id}")
            raise HTTPException(status_code=404, detail="Картку не знайдено або дані не змінено")
        return True

    async def get_records_by_patient(self, patient_id: str, current_user: UserResponse) -> List[MedicalRecordResponse]:
        logger.info(f"Отримання карток пацієнта: {patient_id} користувачем: {current_user.id}")
        if current_user.role == UserRole.PATIENT and str(current_user.id) != patient_id:
            logger.warning(f"Пацієнт {current_user.id} намагався отримати доступ до чужих карток ({patient_id})")
            raise HTTPException(status_code=403, detail="Доступ заборонено")
            
        return await self.repo.get_by_patient(patient_id)

    async def get_active_doctor_records(self, doctor_id: str) -> List[MedicalRecordResponse]:
        logger.info(f"Отримання активних карток для лікаря: {doctor_id}")
        return await self.repo.get_active_by_doctor(doctor_id)

    async def get_all_doctor_records(self, doctor_id: str) -> List[MedicalRecordResponse]:
        logger.info(f"Отримання всіх карток для лікаря: {doctor_id}")
        return await self.repo.get_all_by_doctor(doctor_id)

    async def discharge_medical_record(self, record_id: str, final_diagnosis: str, discharge_date: datetime) -> bool:
        logger.info(f"Виписка пацієнта за карткою: {record_id}")
        success = await self.repo.discharge_record(record_id, final_diagnosis, discharge_date)
        if not success:
            logger.warning(f"Не вдалося виписати пацієнта за карткою: {record_id}")
            raise HTTPException(status_code=404, detail="Картку не знайдено або не змінено")
        
        logger.info(f"Скасування невиконаних призначень для картки: {record_id}")
        await self.presc_repo.abort_pending_prescriptions(record_id)
        return True

    async def deactivate_record(self, record_id: str, current_user: Optional[UserResponse] = None) -> bool:
        logger.info(f"Деактивація картки: {record_id}")
        record = await self.repo.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Картку не знайдено")
        
        if current_user and current_user.role != UserRole.ADMIN and record.get('doctor_id') != str(current_user.id):
            raise HTTPException(status_code=403, detail="Ви не можете деактивувати цю картку")
            
        success = await self.repo.update_status(record_id, "DEACTIVATED")
        if success:
            logger.info(f"Скасування призначень для картки: {record_id} через деактивацію")
            await self.presc_repo.abort_pending_prescriptions(record_id)
        return success
        
    async def deactivate_cards_by_patient(self, patient_id: str) -> bool:
        logger.info(f"Каскадна деактивація карток пацієнта: {patient_id}")
        records = await self.repo.get_by_patient(patient_id)
        for r in records:
            if r.get('status') == 'ACTIVE':
                await self.deactivate_record(str(r['_id']))
        return True
