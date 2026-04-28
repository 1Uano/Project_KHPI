from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.medical_record import MedicalRecordCreate, MedicalRecordDischarge, MedicalRecordDiagnosesUpdate
from app.models.user import UserRole, UserResponse
from app.database.db import get_database
from app.services.record_service import MedicalRecordService
from app.api.dependencies import require_role

router = APIRouter(prefix="/records", tags=["Medical Records"])

@router.post("/")
async def create_medical_record(
        record_in: MedicalRecordCreate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = MedicalRecordService(db)
    new_record_id = await service.create_record(record_in)
    return {
        "message": "Медичну картку успішно створено!",
        "record_id": new_record_id
    }

@router.get("/")
async def get_all_records(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = MedicalRecordService(db)
    return await service.get_all_records()

@router.get("/{record_id}")
async def get_record_by_id(
        record_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = MedicalRecordService(db)
    record = await service.get_record_by_id(record_id)
    return record

@router.put("/{record_id}/diagnoses")
async def update_diagnoses(
        record_id: str,
        diag_data: MedicalRecordDiagnosesUpdate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = MedicalRecordService(db)
    record = await service.get_record_by_id(record_id)
    if current_user.role != UserRole.ADMIN and record.get("doctor_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Тільки адміністратор або лікуючий лікар можуть редагувати діагноз")
    await service.update_diagnoses(record_id, diag_data.diagnosis, diag_data.secondary_diagnoses)
    return {"message": "Діагнози успішно оновлено!"}

@router.get("/patient/{patient_id}")
async def get_records_by_patient(
        patient_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT]))
):
    service = MedicalRecordService(db)
    return await service.get_records_by_patient(patient_id, current_user)

@router.get("/doctor/active")
async def get_active_doctor_records(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR]))
):
    service = MedicalRecordService(db)
    return await service.get_active_doctor_records(current_user.id)

@router.get("/doctor/all")
async def get_all_doctor_records(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR]))
):
    service = MedicalRecordService(db)
    return await service.get_all_doctor_records(current_user.id)

@router.patch("/{record_id}/discharge")
async def discharge_medical_record(
        record_id: str,
        discharge_data: MedicalRecordDischarge,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = MedicalRecordService(db)
    await service.discharge_medical_record(
        record_id, 
        discharge_data.final_diagnosis, 
        discharge_data.discharge_date
    )
    return {"message": "Пацієнта виписано"}

@router.patch("/{record_id}/deactivate")
async def deactivate_medical_record(
        record_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = MedicalRecordService(db)
    await service.deactivate_record(record_id, current_user)
    return {"message": "Медичну картку деактивовано"}