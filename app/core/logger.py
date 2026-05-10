"""
Централізована конфігурація системи логування.

Надає дві публічні функції:
- setup_logging(): викликається один раз при старті застосунку в main.py
- get_logger(name): повертає налаштований логер для будь-якого модуля

Особливості:
- SensitiveDataFormatter маскує JWT токени та паролі у виводі
- StreamHandler виводить логи в stdout (видно в Docker logs)
- RotatingFileHandler зберігає логи у logs/app.log з ротацією
- propagate=False на кожному модульному логері запобігає дублюванню
- Шумні бібліотеки (motor, pymongo, watchfiles) зафільтровані
"""

import logging
import logging.handlers
import re
import sys
from pathlib import Path


class SensitiveDataFormatter(logging.Formatter):
    """
    Кастомний форматер логів, що автоматично маскує чутливі дані.

    Маскує JWT токени та значення полів password/token/secret
    перед записом у лог, захищаючи від витоку credentials.
    """

    _PATTERNS = [
        re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
        re.compile(
            r"(password|access_token|refresh_token|secret_key|token)"
            r"(['\"]?\s*[:=]\s*['\"]?)([^'\",}\s\\]+)(['\"]?)",
            re.IGNORECASE,
        ),
    ]

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in self._PATTERNS:
            if pattern.groups == 4:
                msg = pattern.sub(r"\g<1>\g<2>***\g<4>", msg)
            else:
                msg = pattern.sub("***MASKED_TOKEN***", msg)
        return msg


_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Бібліотеки, що генерують надмірно детальні логи — встановлюємо WARNING
_NOISY_LOGGERS = [
    "motor",
    "pymongo",
    "watchfiles",
    "uvicorn.access",
    "httpcore",
    "httpx",
]

_setup_done = False


def setup_logging() -> None:
    """
    Ініціалізує систему логування застосунку.

    Повинна викликатись один раз при старті (у main.py перед усім іншим).
    Налаштовує кореневий логер, StreamHandler для stdout та
    RotatingFileHandler для збереження логів у файл.

    Повторний виклик ігнорується завдяки прапорцю _setup_done.
    """
    global _setup_done
    if _setup_done:
        return
    _setup_done = True

    from app.core.config import settings

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = SensitiveDataFormatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    for lib_name in _NOISY_LOGGERS:
        lib_logger = logging.getLogger(lib_name)
        lib_logger.setLevel(logging.WARNING)
        lib_logger.propagate = True

    root_logger.info(
        f"Логування ініціалізовано. Рівень: {settings.LOG_LEVEL}. "
        f"Файл логів: {logs_dir / 'app.log'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Повертає налаштований логер для вказаного модуля.

    Встановлює propagate=False щоб уникнути дублювання записів
    через кореневий логер, якщо до модульного логера додавались
    обробники раніше.

    :param name: Ім'я логера, зазвичай передається __name__ модуля.
    :return: Налаштований екземпляр logging.Logger.
    """
    logger = logging.getLogger(name)
    logger.propagate = True
    return logger
