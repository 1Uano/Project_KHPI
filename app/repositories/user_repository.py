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

    async def get_all_users(
        self,
        role: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: int = 1
    ) -> List[UserResponse]:
        query = {}
        if role:
            query["role"] = role
        if search:
            query["full_name"] = {"$regex": search, "$options": "i"}

        if sort_by == "patients_count" and role == "DOCTOR":
            pipeline = [
                {"$match": query},
                {"$lookup": {
                    "from": "medical_records",
                    "let": {"doctor_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$doctor_id", "$$doctor_id"]},
                                    {"$eq": ["$status", "ACTIVE"]}
                                ]
                            }
                        }}
                    ],
                    "as": "active_records"
                }},
                {"$addFields": {
                    "patients_count": {"$size": "$active_records"}
                }},
                {"$sort": {"patients_count": sort_order}},
                {"$skip": skip},
                {"$limit": limit}
            ]
            cursor = self.collection.aggregate(pipeline)
            users = await cursor.to_list(length=limit)
            return [UserResponse(**user) for user in users]

        sort_config = []
        if sort_by:
            if sort_by == "alphabetically":
                sort_config = [("full_name", sort_order)]
            elif sort_by == "birth_date":
                sort_config = [("birth_date", sort_order)]
            elif sort_by == "category":
                sort_config = [("category", sort_order)]
            else:
                sort_config = [(sort_by, sort_order)]

        cursor = self.collection.find(query)
        if sort_config:
            cursor = cursor.sort(sort_config)
            
        cursor = cursor.skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        return [UserResponse(**user) for user in users]

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        if not ObjectId.is_valid(user_id):
            return None
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserResponse(**user)
        return None

    async def update_user_status(self, user_id: str, is_active: bool) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": is_active}}
        )
        return result.modified_count > 0


class TokenBlacklistRepository:
    """
    Репозиторій для управління чорним списком відкликаних JWT токенів.

    Зберігає токени в колекції MongoDB. Кожен токен зберігається
    разом з датою закінчення для можливості очищення застарілих записів.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["token_blacklist"]

    async def add_to_blacklist(self, token: str) -> None:
        """
        Додає токен до чорного списку.

        :param token: JWT токен, який необхідно анулювати.
        """
        from datetime import datetime
        import jwt as pyjwt
        from app.core.config import settings
        try:
            payload = pyjwt.decode(
                token, settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False}
            )
            exp = payload.get("exp")
            expires_at = datetime.utcfromtimestamp(exp) if exp else datetime.utcnow()
        except Exception:
            expires_at = datetime.utcnow()
        await self.collection.update_one(
            {"token": token},
            {"$set": {"token": token, "expires_at": expires_at}},
            upsert=True,
        )

    async def is_blacklisted(self, token: str) -> bool:
        """
        Перевіряє, чи знаходиться токен у чорному списку.

        :param token: JWT токен для перевірки.
        :return: True якщо токен відкликано, False інакше.
        """
        from datetime import datetime
        doc = await self.collection.find_one({"token": token})
        if not doc:
            return False
        expires_at = doc.get("expires_at")
        if expires_at and expires_at < datetime.utcnow():
            await self.collection.delete_one({"token": token})
            return False
        return True