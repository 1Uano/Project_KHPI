import pytest
from app.core.exceptions import (
    AppException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    NotAuthenticatedException,
    PermissionDeniedException,
    NotFoundException,
    BadRequestException,
)


class TestAppExceptions:
    """Тести для кастомних класів виключень додатку."""

    def test_app_exception_stores_status_and_detail(self):
        """AppException зберігає status_code та detail."""
        exc = AppException(status_code=400, detail="Помилка")
        assert exc.status_code == 400
        assert exc.detail == "Помилка"

    def test_user_already_exists_has_409_status(self):
        """UserAlreadyExistsException повертає статус 409 Conflict."""
        exc = UserAlreadyExistsException(email="test@test.com")
        assert exc.status_code == 409
        assert "test@test.com" in exc.detail

    def test_invalid_credentials_has_401_status(self):
        """InvalidCredentialsException повертає статус 401."""
        exc = InvalidCredentialsException()
        assert exc.status_code == 401
        assert "Невірний" in exc.detail

    def test_not_authenticated_has_401_and_default_message(self):
        """NotAuthenticatedException має статус 401 та стандартне повідомлення."""
        exc = NotAuthenticatedException()
        assert exc.status_code == 401
        assert exc.detail == "Не авторизовано"

    def test_not_authenticated_accepts_custom_detail(self):
        """NotAuthenticatedException приймає кастомне повідомлення."""
        exc = NotAuthenticatedException(detail="Токен прострочено")
        assert exc.detail == "Токен прострочено"

    def test_permission_denied_has_403_status(self):
        """PermissionDeniedException повертає статус 403 Forbidden."""
        exc = PermissionDeniedException()
        assert exc.status_code == 403

    def test_not_found_has_404_status(self):
        """NotFoundException повертає статус 404 Not Found."""
        exc = NotFoundException()
        assert exc.status_code == 404

    def test_not_found_accepts_custom_detail(self):
        """NotFoundException приймає кастомний опис."""
        exc = NotFoundException(detail="Пацієнта не знайдено")
        assert exc.detail == "Пацієнта не знайдено"

    def test_bad_request_has_400_status(self):
        """BadRequestException повертає статус 400 Bad Request."""
        exc = BadRequestException()
        assert exc.status_code == 400

    def test_all_exceptions_inherit_from_app_exception(self):
        """Усі кастомні виключення є підкласами AppException."""
        for exc_class in [
            UserAlreadyExistsException,
            InvalidCredentialsException,
            NotAuthenticatedException,
            PermissionDeniedException,
            NotFoundException,
            BadRequestException,
        ]:
            assert issubclass(exc_class, AppException)
