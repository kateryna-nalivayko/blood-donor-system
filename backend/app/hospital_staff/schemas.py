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


class StaffPerformanceParams(BaseModel):
    min_requests: int = Field(5, description="Minimum number of requests created", ge=1)
    min_fulfillment_rate: float = Field(70.0, description="Minimum fulfillment rate percentage", ge=0.0, le=100.0)
    months: int = Field(6, description="Look back period in months", ge=1)
    limit: int = Field(50, description="Maximum number of results", le=1000)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "min_requests": 5,
                "min_fulfillment_rate": 70.0,
                "months": 6,
                "limit": 50
            }
        }
    }

class StaffPerformanceResponse(BaseModel):
    staff_id: int
    user_id: int
    first_name: str
    last_name: str
    email: str
    role: str
    hospital_id: int
    hospital_name: str
    total_requests: int
    fulfilled_requests: int
    fulfillment_rate: float
    blood_type_count: int
    blood_types: Optional[str] = None