from fastapi import APIRouter, Depends
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
        current_user: UserResponse = Depends(require_role([UserRole.DOCTOR]))
):
    repo = MedicalRecordRepository(db)
    new_record_id = await repo.create_record(record_in)

    return {
        "message": "Медичну картку успішно створено!",
        "record_id": new_record_id
    }