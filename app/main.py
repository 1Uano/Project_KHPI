from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logger import setup_logging, get_logger
from app.database.db import db
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.records import router as records_router
from app.api.prescription import router as precription_router

setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = db.client[settings.DATABASE_NAME]
    logger.info(f"🚀 Connected to MongoDB: {settings.DATABASE_NAME}")

    existing_collections = await database.list_collection_names()

    for collection_name in ["users", "medical_records", "prescriptions", "token_blacklist"]:
        if collection_name not in existing_collections:
            await database.create_collection(collection_name)
            logger.info(f"📦 Created collection: {collection_name}")

    from app.repositories.user_repository import UserRepository
    from app.models.user import UserCreate, UserRole
    from app.core.security import get_password_hash

    repo = UserRepository(database)
    admin_user = await repo.collection.find_one({"email": "admin@hospital.com"})
    if not admin_user:
        logger.info("🌱 Creating default admin user...")
        hashed_password = get_password_hash("admin123")
        new_admin = UserCreate(
            email="admin@hospital.com",
            full_name="System Admin",
            role=UserRole.ADMIN,
            password=hashed_password,
            is_active=True
        )
        user_dict = new_admin.model_dump()
        user_dict["password"] = hashed_password
        await repo.collection.insert_one(user_dict)
        logger.info("✅ Default admin created.")
    else:
        logger.info("⚡ Default admin already exists.")

    yield
    db.client.close()
    logger.info("💤 MongoDB connection closed.")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.responses import HTMLResponse

def get_error_html(status_code: int, message: str) -> str:
    titles = {
        400: "Невірний запит",
        403: "Доступ заборонено",
        404: "Сторінку не знайдено",
        422: "Помилка валідації",
        500: "Внутрішня помилка сервера"
    }
    title = titles.get(status_code, "Помилка")
    
    return f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Помилка {status_code} | Hospital System</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f5f8; color: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .error-card {{ background: white; padding: 50px 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; max-width: 450px; width: 100%; border-top: 5px solid #e74c3c; }}
            .error-code {{ font-size: 80px; font-weight: 800; color: #e74c3c; margin: 0; line-height: 1; letter-spacing: -2px; }}
            .error-title {{ font-size: 24px; font-weight: 600; margin: 20px 0 10px; color: #34495e; }}
            .error-message {{ font-size: 16px; color: #7f8c8d; margin-bottom: 30px; line-height: 1.6; }}
            .btn-home {{ display: inline-block; background: #3498db; color: white; text-decoration: none; padding: 12px 25px; border-radius: 6px; font-weight: 600; font-size: 15px; transition: background 0.3s; }}
            .btn-home:hover {{ background: #2980b9; }}
        </style>
    </head>
    <body>
        <div class="error-card">
            <h1 class="error-code">{status_code}</h1>
            <h2 class="error-title">{title}</h2>
            <p class="error-message">{message}</p>
            <a href="/" class="btn-home">Повернутися на головну</a>
        </div>
    </body>
    </html>
    """

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(status_code=exc.status_code, content=get_error_html(exc.status_code, exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP Exception {exc.status_code}: {exc.detail}")
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(status_code=exc.status_code, content=get_error_html(exc.status_code, str(exc.detail)))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Необроблена помилка сервера: {str(exc)}", exc_info=True)
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(status_code=500, content=get_error_html(500, "Нажаль, сталася внутрішня помилка сервера. Ми вже працюємо над її вирішенням."))
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера"},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Передані дані мають невірний формат", "errors": jsonable_encoder(exc.errors())},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(precription_router)
app.include_router(records_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "database": settings.DATABASE_NAME}
