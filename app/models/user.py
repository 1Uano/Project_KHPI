from enum import Enum
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    PATIENT = "PATIENT"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool = True
    specialization: Optional[str] = None  
    category: Optional[str] = None        
    birth_date: Optional[date] = None     


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }