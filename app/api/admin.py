from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from pydantic import BaseModel

from app.models.user import UserCreate, UserRole, UserResponse
from app.database.db import get_database
from app.services.user_service import UserService
from app.api.dependencies import require_role

router = APIRouter(prefix="/admin", tags=["Admin Management"])

@router.post("/users/", summary="Create new user")
async def create_user(
        user_in: UserCreate,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN]))
):
    user_service = UserService(db)
    new_user_id = await user_service.create_user(user_in)

    return {
        "message": "Користувача успішно створено",
        "user_id": new_user_id
    }

@router.get("/users/", response_model=List[UserResponse])
async def get_all_users(
        role: Optional[UserRole] = Query(None, description="Фільтр за роллю"),
        search: Optional[str] = Query(None, description="Пошук за ім'ям"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        sort_by: Optional[str] = Query(None, description="Поле для сортування (alphabetically, birth_date, category, patients_count)"),
        sort_order: int = Query(1, description="1 для зростання, -1 для спадання"),
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.PATIENT]))
):
    user_service = UserService(db)
    return await user_service.get_all_users(
        role=role.value if role else None, 
        search=search, 
        skip=skip, 
        limit=limit, 
        sort_by=sort_by, 
        sort_order=sort_order
    )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN]))
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return user

class DeactivateRequest(BaseModel):
    new_doctor_id: Optional[str] = None

@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
        user_id: str,
        deactivate_data: DeactivateRequest = DeactivateRequest(),
        db: AsyncIOMotorDatabase = Depends(get_database),
        current_user: UserResponse = Depends(require_role([UserRole.ADMIN]))
):
    user_service = UserService(db)
    await user_service.deactivate_user(user_id, deactivate_data.new_doctor_id)
    return {"message": "Користувача успішно деактивовано"}