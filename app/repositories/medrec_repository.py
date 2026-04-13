from bson import ObjectId
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

    async def get_all(self) -> list:
        records = []
        async for doc in self.collection.find():
            doc["_id"] = str(doc["_id"])
            records.append(doc)
        return records

    async def get_by_id(self, record_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": ObjectId(record_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_by_patient(self, patient_id: str) -> list:
        records = []
        async for doc in self.collection.find({"patient_id": patient_id}):
            doc["_id"] = str(doc["_id"])
            records.append(doc)
        return records