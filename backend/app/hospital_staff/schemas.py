from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.common.enums import StaffRole, Department


class HospitalStaffProfileCreate(BaseModel):
    hospital_id: int = Field(..., description="ID of the hospital") 
    role: StaffRole = Field(..., description="Role of hospital staff")
    department: Department = Field(..., description="Department of hospital staff")

    model_config = {
        "json_schema_extra": {
            "example": {
                "hospital_id": 1,
                "role": "doctor",
                "department": "hematology"
            }
        }
    }


class HospitalStaffProfileResponse(BaseModel):
    id: int
    user_id: int
    hospital_id: int
    role: str
    department: str
    created_at: datetime
    updated_at: datetime
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 42,
                "hospital_id": 1,
                "role": "doctor",
                "department": "hematology",
                "created_at": "2025-03-25T10:30:00",
                "updated_at": "2025-03-25T10:30:00"
            }
        }
    }