from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.prescriptions import PrescriptionCreate
from app.models.user import UserRole, UserResponse
from app.database.db import get_database
from app.repositories.prescriptions_repository import PrescriptionRepository
from app.api.dependencies import require_role

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
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN]))
):
    repo = PrescriptionRepository(db)
    return await repo.get_by_record(record_id)