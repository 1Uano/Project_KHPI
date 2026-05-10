"""
Патерн Спостерігач (Observer) для аудиту системних подій.

EventBus (Синглтон) приймає реєстрацію спостерігачів та розсилає їм
події при ключових діях в системі (логін, деактивація, виписка тощо).
Це дозволяє додавати нових спостерігачів (наприклад, email-нотифікації)
без зміни бізнес-логіки сервісів.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from app.core.logger import get_logger

logger = get_logger(__name__)


class EventObserver(ABC):
    """Абстрактний базовий клас для всіх спостерігачів подій."""

    @abstractmethod
    def on_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Обробляє подію системи.

        :param event_type: Тип події (наприклад, 'USER_LOGIN', 'PATIENT_DISCHARGED').
        :param data: Словник з деталями події.
        """


class AuditLogObserver(EventObserver):
    """
    Спостерігач, що записує всі системні події в журнал (лог).
    Використовується для аудиту дій у системі.
    """

    def on_event(self, event_type: str, data: dict[str, Any]) -> None:
        logger.info(f"[AUDIT] Подія: {event_type} | Дані: {data}")


class EventBus:
    """
    Шина подій — Синглтон, що керує реєстрацією спостерігачів
    та розповсюдженням подій між компонентами системи.

    Реалізує патерн Observer (Спостерігач) у поєднанні з Singleton.
    """

    _instance: EventBus | None = None
    _observers: list[EventObserver]

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._observers = []
        return cls._instance

    def subscribe(self, observer: EventObserver) -> None:
        """
        Реєструє нового спостерігача.

        :param observer: Об'єкт, що реалізує EventObserver.
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"EventBus: зареєстровано спостерігача {type(observer).__name__}")

    def unsubscribe(self, observer: EventObserver) -> None:
        """Видаляє спостерігача зі списку."""
        self._observers = [o for o in self._observers if o is not observer]

    def publish(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """
        Публікує подію всім зареєстрованим спостерігачам.

        :param event_type: Унікальний тип події.
        :param data: Дані, що описують контекст події.
        """
        payload = data or {}
        for observer in self._observers:
            try:
                observer.on_event(event_type, payload)
            except Exception as exc:
                logger.error(
                    f"EventBus: помилка у спостерігача {type(observer).__name__}: {exc}"
                )


# Глобальна шина подій — єдиний екземпляр для всього застосунку
event_bus = EventBus()
event_bus.subscribe(AuditLogObserver())


# ---------- Константи типів подій ----------

class SystemEvent:
    """Константи для стандартних системних подій."""
    USER_LOGIN = "USER_LOGIN"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    TOKEN_REFRESHED = "TOKEN_REFRESHED"
    USER_CREATED = "USER_CREATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    RECORD_CREATED = "RECORD_CREATED"
    PATIENT_DISCHARGED = "PATIENT_DISCHARGED"
    PRESCRIPTION_EXECUTED = "PRESCRIPTION_EXECUTED"
    PRESCRIPTION_CREATED = "PRESCRIPTION_CREATED"
