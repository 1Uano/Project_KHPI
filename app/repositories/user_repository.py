from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.encoders import jsonable_encoder 
from app.models.user import UserCreate

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def create_user(self, user_in: UserCreate) -> str:
        user_dict = jsonable_encoder(user_in)

        result = await self.collection.insert_one(user_dict)
        return str(result.inserted_id)