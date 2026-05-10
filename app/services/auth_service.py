from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.user_repository import UserRepository, TokenBlacklistRepository
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.exceptions import InvalidCredentialsException, NotAuthenticatedException
from app.core.events import event_bus, SystemEvent
from app.core.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    """Сервіс автентифікації та управління токенами."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = UserRepository(db)
        self.blacklist = TokenBlacklistRepository(db)

    async def authenticate_user(self, email: str, password: str) -> dict:
        """
        Автентифікує користувача та повертає пару JWT токенів.

        :param email: Електронна пошта користувача.
        :param password: Пароль у відкритому вигляді.
        :return: Словник з access_token та refresh_token.
        :raises InvalidCredentialsException: Якщо дані невірні.
        :raises HTTPException 403: Якщо акаунт деактивовано.
        """
        logger.info(f"Спроба входу для користувача: {email}")
        user_dict = await self.repo.collection.find_one({"email": email})

        if not user_dict or not verify_password(password, user_dict.get("password")):
            logger.error(f"Невдала спроба входу для користувача: {email}")
            event_bus.publish(SystemEvent.USER_LOGIN_FAILED, {"email": email})
            raise InvalidCredentialsException()

        if user_dict.get("is_active") is False:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Акаунт деактивовано")

        token_data = {
            "sub": user_dict["email"],
            "role": user_dict.get("role"),
            "id": str(user_dict["_id"]),
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": user_dict["email"]})

        logger.info(f"Користувач {email} успішно авторизувався.")
        event_bus.publish(SystemEvent.USER_LOGIN, {
            "email": email,
            "user_id": str(user_dict["_id"]),
            "role": user_dict.get("role"),
        })
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Видає новий access_token на основі дійсного refresh_token.

        :param refresh_token: Токен оновлення, отриманий при логіні.
        :return: Словник з новим access_token.
        :raises NotAuthenticatedException: Якщо токен недійсний або прострочений.
        """
        from app.core.security import decode_token
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise NotAuthenticatedException(detail="Недійсний refresh токен")

        email: str = payload.get("sub")
        user_dict = await self.repo.collection.find_one({"email": email})
        if not user_dict or not user_dict.get("is_active", True):
            raise NotAuthenticatedException(detail="Користувача не знайдено або деактивовано")

        token_data = {
            "sub": user_dict["email"],
            "role": user_dict.get("role"),
            "id": str(user_dict["_id"]),
        }
        new_access_token = create_access_token(data=token_data)
        logger.info(f"Токен оновлено для користувача: {email}")
        event_bus.publish(SystemEvent.TOKEN_REFRESHED, {"email": email})
        return {"access_token": new_access_token, "token_type": "bearer"}

    async def logout(self, token: str) -> None:
        """
        Виконує вихід користувача, додаючи поточний токен до чорного списку.

        :param token: JWT access_token, який потрібно анулювати.
        """
        from app.core.security import decode_token
        payload = decode_token(token)
        email = payload.get("sub") if payload else "unknown"
        await self.blacklist.add_to_blacklist(token)
        logger.info(f"Користувач {email} вийшов із системи")
        event_bus.publish(SystemEvent.USER_LOGOUT, {"email": email})

