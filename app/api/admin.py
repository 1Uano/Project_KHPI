from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserCreate, UserRole, UserResponse
from app.database.db import get_database
from app.repositories.user_repository import UserRepository
from app.api.dependencies import require_role
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin Management"])

@router.post("/users/", summary="Create new user")
async def create_user(
        user_in: UserCreate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN]))
):
    hashed_password = get_password_hash(user_in.password)
    user_dict = user_in.model_dump()
    user_dict["password"] = hashed_password

    repo = UserRepository(db)
    user_to_db = UserCreate(**{**user_dict, "password": hashed_password})
    new_user_id = await repo.create_user(user_to_db)

    return {
        "message": "Користувача успішно створено",
        "user_id": new_user_id
    }