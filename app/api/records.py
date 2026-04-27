from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.medical_record import MedicalRecordCreate, MedicalRecordDischarge, MedicalRecordDiagnosesUpdate
from app.models.user import UserRole, UserResponse
from app.database.db import get_database
from app.repositories.medrec_repository import MedicalRecordRepository
from app.repositories.prescriptions_repository import PrescriptionRepository
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

@router.put("/{record_id}/diagnoses")
async def update_diagnoses(
        record_id: str,
        diag_data: MedicalRecordDiagnosesUpdate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = MedicalRecordRepository(db)
    success = await repo.update_record_diagnoses(record_id, diag_data.diagnosis, diag_data.secondary_diagnoses)
    if not success:
        raise HTTPException(status_code=404, detail="Картку не знайдено або дані не змінено")
    return {"message": "Діагнози успішно оновлено!"}

@router.get("/patient/{patient_id}")
async def get_records_by_patient(
        patient_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT]))
):
    if current_user.role == UserRole.PATIENT and str(current_user.id) != patient_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    repo = MedicalRecordRepository(db)
    return await repo.get_by_patient(patient_id)

@router.get("/doctor/active")
async def get_active_doctor_records(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR]))
):
    repo = MedicalRecordRepository(db)
    return await repo.get_active_by_doctor(current_user.id)

@router.get("/doctor/all")
async def get_all_doctor_records(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR]))
):
    repo = MedicalRecordRepository(db)
    return await repo.get_all_by_doctor(current_user.id)

@router.patch("/{record_id}/discharge")
async def discharge_medical_record(
        record_id: str,
        discharge_data: MedicalRecordDischarge,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = MedicalRecordRepository(db)
    success = await repo.discharge_record(
        record_id, 
        discharge_data.final_diagnosis, 
        discharge_data.discharge_date
    )
    if not success:
        raise HTTPException(status_code=404, detail="Картку не знайдено або не змінено")
    
    presc_repo = PrescriptionRepository(db)
    await presc_repo.abort_pending_prescriptions(record_id)
        
    return {"message": "Пацієнта виписано"}