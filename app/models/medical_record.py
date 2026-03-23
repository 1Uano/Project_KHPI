from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class RecordStatus(str, Enum):
    ACTIVE = "ACTIVE"         
    DISCHARGED = "DISCHARGED" 

class MedicalRecordBase(BaseModel):
    patient_id: str
    doctor_id: str
    diagnosis: str
    status: RecordStatus = RecordStatus.ACTIVE
    admission_date: datetime = Field(default_factory=datetime.utcnow)
    discharge_date: Optional[datetime] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordResponse(MedicalRecordBase):
    id: str = Field(..., alias="_id")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }