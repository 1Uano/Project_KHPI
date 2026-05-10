import pytest
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
import jwt


class TestPasswordHashing:
    """Тести для функцій хешування паролів."""

    def test_hash_is_not_plain_text(self):
        """Хеш пароля не повинен збігатися з оригінальним паролем."""
        password = "SecretPass1"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_hash_starts_with_bcrypt_prefix(self):
        """bcrypt хеші завжди починаються з '$2b$'."""
        hashed = get_password_hash("MyPassword9")
        assert hashed.startswith("$2b$")

    def test_two_hashes_of_same_password_are_different(self):
        """Через salt кожен хеш унікальний, навіть для однакового пароля."""
        password = "SamePass1"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

    def test_verify_correct_password_returns_true(self):
        """Правильний пароль успішно верифікується відносно свого хешу."""
        password = "ValidPass1"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password_returns_false(self):
        """Невірний пароль повертає False при верифікації."""
        hashed = get_password_hash("CorrectPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_verify_empty_password_returns_false(self):
        """Порожній рядок не верифікується відносно непустого хешу."""
        hashed = get_password_hash("SomePassword1")
        assert verify_password("", hashed) is False


class TestJwtTokenCreation:
    """Тести для функції генерації JWT токенів."""

    def test_token_is_a_string(self):
        """Функція повертає рядок."""
        token = create_access_token({"sub": "user@example.com"})
        assert isinstance(token, str)

    def test_token_contains_correct_subject(self):
        """Декодований токен містить правильне поле 'sub'."""
        email = "doctor@hospital.com"
        token = create_access_token({"sub": email})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email

    def test_token_contains_expiry(self):
        """Токен містить поле 'exp' (час спливання)."""
        token = create_access_token({"sub": "test@test.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_invalid_secret_raises_error(self):
        """Декодування токена з неправильним ключем генерує виняток."""
        token = create_access_token({"sub": "test@test.com"})
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            jwt.decode(token, "wrong_secret", algorithms=[settings.ALGORITHM])

    def test_custom_data_preserved_in_token(self):
        """Довільні дані в payload зберігаються після кодування/декодування."""
        token = create_access_token({"sub": "a@b.com", "role": "DOCTOR"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == "DOCTOR"
