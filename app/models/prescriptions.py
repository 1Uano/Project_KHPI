from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class PrescriptionType(str, Enum):
    MEDICINE = "MEDICINE"
    PROCEDURE = "PROCEDURE"
    SURGERY = "SURGERY"

class PrescriptionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"

class PrescriptionBase(BaseModel):
    record_id: str
    prescribed_by: str
    assigned_to: Optional[str] = None
    type: PrescriptionType
    description: str
    status: PrescriptionStatus = PrescriptionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionResponse(PrescriptionBase):
    id: PyObjectId = Field(default=None, alias="_id")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }