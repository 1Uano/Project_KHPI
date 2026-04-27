from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.encoders import jsonable_encoder
from app.models.prescriptions import PrescriptionCreate
from datetime import datetime

class PrescriptionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["prescriptions"]

    async def create_prescription(self, prescription_in: PrescriptionCreate) -> str:
        prescription_dict = jsonable_encoder(prescription_in)
        result = await self.collection.insert_one(prescription_dict)
        return str(result.inserted_id)

    async def get_all(self) -> list:
        prescriptions = []
        async for doc in self.collection.find():
            doc["_id"] = str(doc["_id"])
            prescriptions.append(doc)
        return prescriptions

    async def get_by_id(self, prescription_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": ObjectId(prescription_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_by_record(self, record_id: str) -> list:
        prescriptions = []
        async for doc in self.collection.find({"record_id": record_id}):
            doc["_id"] = str(doc["_id"])
            prescriptions.append(doc)
        return prescriptions

    async def get_assigned_to(self, user_id: str) -> list:
        prescriptions = []
        async for doc in self.collection.find({"assigned_to": user_id}):
            doc["_id"] = str(doc["_id"])
            prescriptions.append(doc)
        return prescriptions

    async def execute_prescription(self, prescription_id: str, execution_date: datetime) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(prescription_id)},
            {"$set": {
                "status": "COMPLETED",
                "completed_at": execution_date
            }}
        )
        return result.modified_count > 0

    async def abort_pending_prescriptions(self, record_id: str) -> bool:
        result = await self.collection.update_many(
            {"record_id": record_id, "status": "PENDING"},
            {"$set": {
                "status": "ABORTED"
            }}
        )
        return True

    async def update_assignee(self, prescription_id: str, new_assignee: str) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(prescription_id)},
            {"$set": {
                "assigned_to": new_assignee
             }}
        )
        return result.modified_count > 0