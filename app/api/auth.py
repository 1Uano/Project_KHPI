from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.db import get_database
from app.core.factory import ServiceFactory

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/login", summary="Вхід в систему")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Автентифікує користувача за email та паролем.
    Повертає access_token (короткий, 30 хв) та refresh_token (довгий, 7 днів).
    """
    auth_service = ServiceFactory.create_auth_service(db)
    return await auth_service.authenticate_user(form_data.username, form_data.password)


class RefreshRequest(BaseModel):
    """Схема запиту для оновлення токена."""
    refresh_token: str


@router.post("/refresh", summary="Оновлення access токена")
async def refresh_access_token(
    body: RefreshRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Видає новий access_token на основі дійсного refresh_token.
    Refresh token не анулюється — він залишається дійсним до свого закінчення.
    """
    auth_service = ServiceFactory.create_auth_service(db)
    return await auth_service.refresh_access_token(body.refresh_token)


@router.post("/logout", summary="Вихід з системи")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Анулює поточний access_token, додаючи його до чорного списку.
    Після цього всі запити з цим токеном повернуть 401 Unauthorized.
    """
    auth_service = ServiceFactory.create_auth_service(db)
    await auth_service.logout(token)
    return {"message": "Ви успішно вийшли з системи"}
