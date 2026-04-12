from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.database.db import get_database
from app.repositories.user_repository import UserRepository
from app.models.user import UserResponse, UserRole
from app.core.exceptions import NotAuthenticatedException, PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserResponse:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise NotAuthenticatedException()
    except InvalidTokenError:
        raise NotAuthenticatedException()

    repo = UserRepository(db)
    user_dict = await repo.collection.find_one({"email": email})
    if user_dict is None:
        raise NotAuthenticatedException()
        
    return UserResponse(**user_dict)

def require_role(allowed_roles: list[UserRole]):
    async def role_checker(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException()
        return current_user
    return role_checker
