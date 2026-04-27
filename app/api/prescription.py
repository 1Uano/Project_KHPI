from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.models.prescriptions import PrescriptionCreate
from app.models.user import UserRole, UserResponse
from app.database.db import get_database
from app.repositories.prescriptions_repository import PrescriptionRepository
from app.api.dependencies import require_role
from datetime import datetime

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

@router.post("/")
async def create_prescription(
        prescription_in: PrescriptionCreate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = PrescriptionRepository(db)
    new_prescription_id = await repo.create_prescription(prescription_in)
    return {
        "message": "Призначення успішно створено!",
        "prescription_id": new_prescription_id
    }

@router.get("/")
async def get_all_prescriptions(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = PrescriptionRepository(db)
    return await repo.get_all()

@router.get("/{prescription_id}")
async def get_prescription_by_id(
        prescription_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = PrescriptionRepository(db)
    prescription = await repo.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Призначення не знайдено")
    return prescription

@router.get("/record/{record_id}")
async def get_prescriptions_by_record(
        record_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT, UserRole.NURSE]))
):
    repo = PrescriptionRepository(db)
    return await repo.get_by_record(record_id)

@router.get("/assigned/me")
async def get_my_prescriptions(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.NURSE]))
):
    repo = PrescriptionRepository(db)
    return await repo.get_assigned_to(current_user.id)

@router.patch("/{prescription_id}/execute")
async def execute_prescription(
        prescription_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.NURSE]))
):
    repo = PrescriptionRepository(db)
    prescription = await repo.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Призначення не знайдено")
        
    p_type = prescription.get("type", "")
    
    # Check permissions
    if current_user.role == UserRole.NURSE and p_type == "SURGERY":
        raise HTTPException(status_code=403, detail="Медсестра не може виконувати операції")
        
    await repo.execute_prescription(prescription_id, datetime.utcnow())
    return {"message": "Призначення виконано!"}

class PrescriptionAssigneeUpdate(BaseModel):
    new_assignee: str

@router.patch("/{prescription_id}/assignee")
async def update_prescription_assignee(
        prescription_id: str,
        update_data: PrescriptionAssigneeUpdate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = PrescriptionRepository(db)
    prescription = await repo.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Призначення не знайдено")
        
    success = await repo.update_assignee(prescription_id, update_data.new_assignee)
    if not success:
        raise HTTPException(status_code=400, detail="Не вдалося змінити виконавця")
        
    return {"message": "Виконавця успішно змінено!"}