import logging
import re
import sys

class SensitiveDataFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True):
        if sys.version_info >= (3, 8):
            super().__init__(fmt, datefmt, style, validate)
        else:
            super().__init__(fmt, datefmt, style)
            
        self._secrets_patterns = [
            # Mask JWT tokens
            re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
            # Mask keys containing 'password', 'token', 'secret'
            re.compile(r"(password|access_token|secret_key|token)(['\"]?\s*[:=]\s*['\"]?)([^'\",}\s\\]+)(['\"]?)", re.IGNORECASE)
        ]

    def format(self, record):
        msg = super().format(record)
        for pattern in self._secrets_patterns:
            if pattern.groups == 4:
                msg = pattern.sub(r"\g<1>\g<2>***\g<4>", msg)
            else:
                msg = pattern.sub("***MASKED_TOKEN***", msg)
        return msg

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        
        fmt_str = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        formatter = SensitiveDataFormatter(fmt=fmt_str)
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
