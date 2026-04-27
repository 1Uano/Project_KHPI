from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.models.user import UserCreate, UserRole, UserResponse
from app.database.db import get_database
from app.repositories.user_repository import UserRepository
from app.api.dependencies import require_role
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin Testing"])

@router.post("/users/")
async def create_test_user(
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
        "message": "Ура! Користувач успішно створений у MongoDB!",
        "user_id": new_user_id
    }

@router.get("/users/", response_model=List[UserResponse])
async def get_all_users(
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.PATIENT]))
):
    repo = UserRepository(db)
    return await repo.get_all_users()

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN]))
):
    repo = UserRepository(db)
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return user