from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.medical_record import MedicalRecordCreate
from app.models.user import UserRole, UserResponse
from app.database.db import get_database
from app.repositories.medrec_repository import MedicalRecordRepository
from app.api.dependencies import require_role

router = APIRouter(prefix="/records", tags=["Medical Records"])

@router.post("/")
async def create_medical_record(
        record_in: MedicalRecordCreate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = MedicalRecordRepository(db)
    new_record_id = await repo.create_record(record_in)
    return {
        "message": "Медичну картку успішно створено!",
        "record_id": new_record_id
    }

@router.get("/")
async def get_all_records(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = MedicalRecordRepository(db)
    return await repo.get_all()

@router.get("/{record_id}")
async def get_record_by_id(
        record_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = MedicalRecordRepository(db)
    record = await repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Медичну картку не знайдено")
    return record

@router.get("/patient/{patient_id}")
async def get_records_by_patient(
        patient_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = MedicalRecordRepository(db)
    return await repo.get_by_patient(patient_id)