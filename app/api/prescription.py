from fastapi import APIRouter, Depends
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
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR]))
):
    repo = PrescriptionRepository(db)
    new_prescription_id = await repo.create_prescription(prescription_in)

    return {
        "message": "Призначення успішно створено!",
        "prescription_id": new_prescription_id
    }