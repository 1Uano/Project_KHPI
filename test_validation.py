from app.models.user import UserCreate
from pydantic import ValidationError

try:
    data = {
      "email": "user@.com",
      "full_name": "string",
      "role": "ADMIN",
      "is_active": True,
      "specialization": "NONE",
      "category": "string",
      "birth_date": "2026-04-14",
      "password": "stringst"
    }
    user = UserCreate(**data)
    print("Success")
except ValidationError as e:
    import json
    print("Validation Error:", json.dumps(e.errors(), default=str))
except Exception as e:
    print("Other Error:", type(e), str(e))
