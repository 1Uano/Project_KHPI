from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.core.exceptions import AppException
from app.database.db import db
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.records import router as records_router
from app.api.prescription import router as precription_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = db.client[settings.DATABASE_NAME]
    print(f"🚀 Connected to MongoDB: {settings.DATABASE_NAME}")

    existing_collections = await database.list_collection_names()

    for collection_name in ["users", "medical_records", "prescriptions"]:
        if collection_name not in existing_collections:
            await database.create_collection(collection_name)
            print(f"📦 Created collection: {collection_name}")

    from app.repositories.user_repository import UserRepository
    from app.models.user import UserCreate, UserRole
    from app.core.security import get_password_hash

    repo = UserRepository(database)
    admin_user = await repo.collection.find_one({"email": "admin@hospital.com"})
    if not admin_user:
        print("🌱 Creating default admin user...")
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
        print("✅ Default admin created.")
    else:
        print("⚡ Default admin already exists.")

    yield
    db.client.close()
    print("💤 MongoDB connection closed.")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
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
