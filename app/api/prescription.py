from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.models.prescriptions import PrescriptionCreate
from app.models.user import UserRole, UserResponse
from app.database.db import get_database
from app.services.prescription_service import PrescriptionService
from app.api.dependencies import require_role

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

@router.post("/")
async def create_prescription(
        prescription_in: PrescriptionCreate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = PrescriptionService(db)
    new_prescription_id = await service.create_prescription(prescription_in)
    return {
        "message": "Призначення успішно створено!",
        "prescription_id": new_prescription_id
    }

@router.get("/")
async def get_all_prescriptions(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = PrescriptionService(db)
    return await service.get_all_prescriptions()

@router.get("/{prescription_id}")
async def get_prescription_by_id(
        prescription_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = PrescriptionService(db)
    prescription = await service.get_prescription_by_id(prescription_id)
    return prescription

@router.get("/record/{record_id}")
async def get_prescriptions_by_record(
        record_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT, UserRole.NURSE]))
):
    service = PrescriptionService(db)
    return await service.get_prescriptions_by_record(record_id)

@router.get("/assigned/me")
async def get_my_prescriptions(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.NURSE]))
):
    service = PrescriptionService(db)
    return await service.get_my_prescriptions(current_user.id)

@router.patch("/{prescription_id}/execute")
async def execute_prescription(
        prescription_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.NURSE]))
):
    service = PrescriptionService(db)
    await service.execute_prescription(prescription_id, current_user)
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
    service = PrescriptionService(db)
    await service.update_prescription_assignee(prescription_id, update_data.new_assignee)
    return {"message": "Виконавця успішно змінено!"}

@router.patch("/{prescription_id}/deactivate")
async def deactivate_prescription(
        prescription_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    service = PrescriptionService(db)
    await service.deactivate_prescription(prescription_id, current_user)
    return {"message": "Призначення успішно скасовано"}