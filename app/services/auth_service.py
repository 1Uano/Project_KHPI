from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.core.exceptions import InvalidCredentialsException
from app.core.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = UserRepository(db)

    async def authenticate_user(self, email: str, password: str) -> dict:
        logger.info(f"Спроба входу для користувача: {email}")
        user_dict = await self.repo.collection.find_one({"email": email})
        
        if not user_dict or not verify_password(password, user_dict.get("password")):
            logger.error(f"Невдала спроба входу для користувача: {email}")
            raise InvalidCredentialsException()

        access_token = create_access_token(
            data={"sub": user_dict["email"], "role": user_dict.get("role"), "id": str(user_dict["_id"])}
        )
        logger.info(f"Користувач {email} успішно авторизувався.")
        # Logging access_token intentionally here to test mask, it should be masked by custom formatter
        logger.info(f"Згенеровано access_token={access_token}")
        return {"access_token": access_token, "token_type": "bearer"}
