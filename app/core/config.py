from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hospital Management System"
    DEBUG: bool = False

    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = "hospital_db"

    SECRET_KEY: str = "super_secret_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()