from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.encoders import jsonable_encoder
from app.models.medical_record import MedicalRecordCreate

class MedicalRecordRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["medical_records"]

    async def create_record(self, record_in: MedicalRecordCreate) -> str:
        record_dict = jsonable_encoder(record_in)

        result = await self.collection.insert_one(record_dict)
        return str(result.inserted_id)