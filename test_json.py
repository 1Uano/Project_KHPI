from app.models.user import UserCreate
from pydantic import ValidationError
from fastapi.responses import JSONResponse
import asyncio

async def test():
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
    except ValidationError as e:
        try:
            resp = JSONResponse(
                status_code=422,
                content={"detail": "Передані дані мають невірний формат", "errors": e.errors()},
            )
            print("JSONResponse created successfully:", resp.body)
        except Exception as json_e:
            print("JSONResponse Failed:", type(json_e), str(json_e))

asyncio.run(test())
