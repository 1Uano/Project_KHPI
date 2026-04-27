from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.db import get_database
from app.core.security import verify_password, create_access_token
from app.core.exceptions import InvalidCredentialsException
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    repo = UserRepository(db)
    user_dict = await repo.collection.find_one({"email": form_data.username})
    if not user_dict or not verify_password(form_data.password, user_dict.get("password")):
        raise InvalidCredentialsException()

    access_token = create_access_token(
        data={"sub": user_dict["email"], "role": user_dict.get("role"), "id": str(user_dict["_id"])}
    )
    return {"access_token": access_token, "token_type": "bearer"}
