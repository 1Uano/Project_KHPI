"""
Патерн Фабрика (Factory) для централізованого створення сервісів.

Замість прямого виклику конструктора в кожному роутері
(AuthService(db), UserService(db) і т.д.),
ServiceFactory надає єдину точку доступу до сервісів.

Переваги:
- Зміна конфігурації або ін'єкція залежностей в одному місці
- Спрощення тестування (можна підмінити фабрику)
- Консистентне створення сервісів з однаковими залежностями
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.record_service import MedicalRecordService
from app.services.prescription_service import PrescriptionService


class ServiceFactory:
    """
    Фабрика для створення екземплярів сервісів бізнес-логіки.

    Централізує створення сервісів та управління їх залежностями.
    Всі методи є статичними — фабрика не зберігає стан.
    """

    @staticmethod
    def create_auth_service(db: AsyncIOMotorDatabase) -> AuthService:
        """
        Створює та повертає екземпляр AuthService.

        :param db: Асинхронне підключення до MongoDB.
        :return: Ініціалізований AuthService.
        """
        return AuthService(db)

    @staticmethod
    def create_user_service(db: AsyncIOMotorDatabase) -> UserService:
        """
        Створює та повертає екземпляр UserService.

        :param db: Асинхронне підключення до MongoDB.
        :return: Ініціалізований UserService.
        """
        return UserService(db)

    @staticmethod
    def create_record_service(db: AsyncIOMotorDatabase) -> MedicalRecordService:
        """
        Створює та повертає екземпляр MedicalRecordService.

        :param db: Асинхронне підключення до MongoDB.
        :return: Ініціалізований MedicalRecordService.
        """
        return MedicalRecordService(db)

    @staticmethod
    def create_prescription_service(db: AsyncIOMotorDatabase) -> PrescriptionService:
        """
        Створює та повертає екземпляр PrescriptionService.

        :param db: Асинхронне підключення до MongoDB.
        :return: Ініціалізований PrescriptionService.
        """
        return PrescriptionService(db)
