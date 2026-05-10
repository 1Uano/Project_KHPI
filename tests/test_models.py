import pytest
from pydantic import ValidationError
from app.models.user import UserCreate, UserRole, DoctorSpecialization


class TestUserCreateValidation:
    """Тести для валідаційних правил моделі UserCreate."""

    def test_valid_patient_creation(self):
        """Пацієнт зі всіма правильними полями створюється без помилок."""
        user = UserCreate(
            email="patient@hospital.com",
            full_name="Іван Петренко",
            role=UserRole.PATIENT,
            password="Password1",
        )
        assert user.email == "patient@hospital.com"
        assert user.role == UserRole.PATIENT

    def test_valid_doctor_requires_specialization(self):
        """Лікар із вказаною спеціалізацією успішно проходить валідацію."""
        user = UserCreate(
            email="doctor@hospital.com",
            full_name="Ольга Коваль",
            role=UserRole.DOCTOR,
            password="SecurePass1",
            specialization=DoctorSpecialization.CARDIOLOGIST,
        )
        assert user.specialization == DoctorSpecialization.CARDIOLOGIST

    def test_doctor_without_specialization_raises_error(self):
        """Лікар без спеціалізації (або зі значенням NONE) не пройде валідацію."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="doc@hospital.com",
                full_name="Тест Лікар",
                role=UserRole.DOCTOR,
                password="Password1",
                specialization=DoctorSpecialization.NONE,
            )
        assert "Спеціалізація є обов'язковою" in str(exc_info.value)

    def test_password_too_short_raises_error(self):
        """Пароль коротший за 8 символів не приймається."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="user@hospital.com",
                full_name="Тест",
                role=UserRole.PATIENT,
                password="P1a",
            )

    def test_password_without_digit_raises_error(self):
        """Пароль без цифри не проходить валідацію."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="user@hospital.com",
                full_name="Тест",
                role=UserRole.PATIENT,
                password="PasswordOnly",
            )
        assert "цифру" in str(exc_info.value)

    def test_password_without_uppercase_raises_error(self):
        """Пароль без великої літери не проходить валідацію."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="user@hospital.com",
                full_name="Тест",
                role=UserRole.PATIENT,
                password="password1",
            )
        assert "велику літеру" in str(exc_info.value)

    def test_password_without_lowercase_raises_error(self):
        """Пароль без маленької літери не проходить валідацію."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="user@hospital.com",
                full_name="Тест",
                role=UserRole.PATIENT,
                password="PASSWORD1",
            )
        assert "маленьку літеру" in str(exc_info.value)

    def test_invalid_email_raises_error(self):
        """Невалідний email не приймається Pydantic."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                full_name="Тест",
                role=UserRole.PATIENT,
                password="ValidPass1",
            )
