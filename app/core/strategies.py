"""
Патерн Стратегія (Strategy) для виконання медичних призначень.

Різні типи призначень мають різні правила виконання:
- Медикаменти може вводити медсестра або лікар
- Процедури може виконувати медсестра або лікар
- Операції може виконувати тільки лікар

Використання стратегій усуває розгалуження if/elif у сервісному шарі
та дозволяє додавати нові типи призначень без зміни PrescriptionService.
"""

from abc import ABC, abstractmethod
from app.models.user import UserRole, UserResponse
from app.core.exceptions import PermissionDeniedException
from app.core.logger import get_logger

logger = get_logger(__name__)


class PrescriptionExecutionStrategy(ABC):
    """Базовий клас стратегії виконання призначення."""

    @abstractmethod
    def validate_executor(self, executor: UserResponse) -> None:
        """
        Перевіряє, чи має вказаний користувач право виконати призначення.

        :param executor: Користувач, що намагається виконати призначення.
        :raises PermissionDeniedException: Якщо роль не дозволяє виконання.
        """

    @abstractmethod
    def get_execution_log_message(self, prescription_id: str, executor: UserResponse) -> str:
        """Повертає повідомлення для лога при успішному виконанні."""


class MedicationStrategy(PrescriptionExecutionStrategy):
    """
    Стратегія для медикаментозних призначень (MEDICATION).
    Можуть виконуватись як медсестрою, так і лікарем.
    """

    def validate_executor(self, executor: UserResponse) -> None:
        allowed = {UserRole.NURSE, UserRole.DOCTOR, UserRole.ADMIN}
        if executor.role not in allowed:
            logger.warning(
                f"Користувач {executor.id} (роль: {executor.role}) "
                f"не має права вводити медикаменти"
            )
            raise PermissionDeniedException()

    def get_execution_log_message(self, prescription_id: str, executor: UserResponse) -> str:
        return (
            f"Медикаментозне призначення {prescription_id} виконано "
            f"користувачем {executor.id} (роль: {executor.role})"
        )


class ProcedureStrategy(PrescriptionExecutionStrategy):
    """
    Стратегія для медичних процедур (PROCEDURE).
    Можуть виконуватись медсестрою або лікарем.
    """

    def validate_executor(self, executor: UserResponse) -> None:
        allowed = {UserRole.NURSE, UserRole.DOCTOR, UserRole.ADMIN}
        if executor.role not in allowed:
            logger.warning(
                f"Користувач {executor.id} (роль: {executor.role}) "
                f"не має права виконувати процедури"
            )
            raise PermissionDeniedException()

    def get_execution_log_message(self, prescription_id: str, executor: UserResponse) -> str:
        return (
            f"Процедура {prescription_id} виконана "
            f"користувачем {executor.id} (роль: {executor.role})"
        )


class SurgeryStrategy(PrescriptionExecutionStrategy):
    """
    Стратегія для хірургічних втручань (SURGERY).
    Можуть виконуватись тільки лікарем або адміністратором.
    Медсестра не має доступу до цього типу призначень.
    """

    def validate_executor(self, executor: UserResponse) -> None:
        if executor.role not in {UserRole.DOCTOR, UserRole.ADMIN}:
            logger.warning(
                f"Спроба виконати операцію {executor.id} з роллю {executor.role} — відхилено"
            )
            raise PermissionDeniedException()

    def get_execution_log_message(self, prescription_id: str, executor: UserResponse) -> str:
        return (
            f"Хірургічне втручання {prescription_id} виконано "
            f"лікарем {executor.id}"
        )


# Реєстр стратегій — відображає тип призначення на відповідну стратегію
_STRATEGY_REGISTRY: dict[str, PrescriptionExecutionStrategy] = {
    "MEDICATION": MedicationStrategy(),
    "PROCEDURE": ProcedureStrategy(),
    "SURGERY": SurgeryStrategy(),
}


def get_execution_strategy(prescription_type: str) -> PrescriptionExecutionStrategy:
    """
    Фабричний метод для отримання стратегії за типом призначення.

    :param prescription_type: Тип призначення ('MEDICATION', 'PROCEDURE', 'SURGERY').
    :return: Відповідна стратегія виконання.
    :raises ValueError: Якщо тип призначення не підтримується.
    """
    strategy = _STRATEGY_REGISTRY.get(prescription_type)
    if strategy is None:
        raise ValueError(f"Невідомий тип призначення: {prescription_type}")
    return strategy
