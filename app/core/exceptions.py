from fastapi import status

class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class UserAlreadyExistsException(AppException):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Користувач з email {email} вже існує"
        )

class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний логін або пароль"
        )

class NotAuthenticatedException(AppException):
    def __init__(self, detail="Не авторизовано"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class PermissionDeniedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас немає прав для виконання цієї дії"
        )
