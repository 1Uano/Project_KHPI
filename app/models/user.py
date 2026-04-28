from enum import Enum
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, BeforeValidator, field_validator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    PATIENT = "PATIENT"

class DoctorSpecialization(str, Enum):
    THERAPIST = "THERAPIST"
    PEDIATRICIAN = "PEDIATRICIAN"
    SURGEON = "SURGEON"
    ORTHOPEDIST = "ORTHOPEDIST"
    CARDIOLOGIST = "CARDIOLOGIST"
    NEUROLOGIST = "NEUROLOGIST"
    NONE = "NONE"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool = True
    specialization: Optional[DoctorSpecialization] = DoctorSpecialization.NONE
    category: Optional[str] = None
    birth_date: Optional[date] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError('Пароль має містити щонайменше одну цифру')
        if not any(char.isupper() for char in v):
            raise ValueError('Пароль має містити щонайменше одну велику літеру')
        if not any(char.islower() for char in v):
            raise ValueError('Пароль має містити щонайменше одну маленьку літеру')
        return v

class UserResponse(UserBase):
    id: PyObjectId = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }