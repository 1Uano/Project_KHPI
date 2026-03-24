from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.encoders import jsonable_encoder
from app.models.prescriptions import PrescriptionCreate

class PrescriptionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["prescriptions"]

    async def create_prescription(self, prescription_in: PrescriptionCreate) -> str:
        prescription_dict = jsonable_encoder(prescription_in)

        result = await self.collection.insert_one(prescription_dict)
        return str(result.inserted_id)