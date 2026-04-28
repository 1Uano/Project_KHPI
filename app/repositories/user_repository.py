from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.encoders import jsonable_encoder
from app.models.user import UserCreate, UserResponse
from app.core.exceptions import UserAlreadyExistsException
from typing import List, Optional
from bson import ObjectId

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def create_user(self, user_in: UserCreate) -> str:
        existing_user = await self.collection.find_one({"email": user_in.email})
        if existing_user:
            raise UserAlreadyExistsException(email=user_in.email)

        user_dict = jsonable_encoder(user_in)
        result = await self.collection.insert_one(user_dict)
        return str(result.inserted_id)

    async def get_all_users(self) -> List[UserResponse]:
        cursor = self.collection.find({})
        users = await cursor.to_list(length=1000)
        return [UserResponse(**user) for user in users]

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        if not ObjectId.is_valid(user_id):
            return None
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserResponse(**user)
        return None