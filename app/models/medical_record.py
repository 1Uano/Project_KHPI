from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class RecordStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISCHARGED = "DISCHARGED"
    DEACTIVATED = "DEACTIVATED"

class MedicalRecordBase(BaseModel):
    patient_id: str
    doctor_id: str
    diagnosis: str
    secondary_diagnoses: list[str] = []
    status: RecordStatus = RecordStatus.ACTIVE
    admission_date: datetime = Field(default_factory=datetime.utcnow)
    discharge_date: Optional[datetime] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordDiagnosesUpdate(BaseModel):
    diagnosis: str  # Primary
    secondary_diagnoses: list[str]

class MedicalRecordDischarge(BaseModel):
    final_diagnosis: str
    discharge_date: datetime

class MedicalRecordResponse(MedicalRecordBase):
    id: PyObjectId = Field(default=None, alias="_id")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }