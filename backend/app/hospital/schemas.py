from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List
from app.common.enums import HospitalType

class HospitalBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Hospital name")
    hospital_type: HospitalType = Field(default=HospitalType.GENERAL, description="Type of hospital")
    address: Optional[str] = Field(None, description="Full address of the hospital")
    city: Optional[str] = Field(None, description="City where the hospital is located")
    region: Optional[str] = Field(None, description="Region/state where the hospital is located")
    country: str = Field("Ukraine", description="Country where the hospital is located")
    phone_number: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email address")
    website: Optional[str] = Field(None, description="Hospital website URL", pattern=r"^https?://.*")

class HospitalCreate(HospitalBase):
    """Schema for creating a new hospital"""
    pass

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Обласна клінічна лікарня",
                "hospital_type": "GENERAL",
                "address": "вул. Шевченка, 100",
                "city": "Київ",
                "region": "Київська область",
                "country": "Ukraine",
                "phone_number": "+380441234567",
                "email": "info@okl.ua",
                "website": "https://okl.ua"
            }
        }

class HospitalUpdate(BaseModel):
    """Schema for updating an existing hospital"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    hospital_type: Optional[HospitalType] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Оновлена назва лікарні",
                "address": "вул. Нова, 200",
                "phone_number": "+380441234567"
            }
        }

class HospitalResponse(HospitalBase):
    """Schema for hospital response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HospitalListResponse(BaseModel):
    """Schema for paginated list of hospitals"""
    items: List[HospitalResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "Обласна клінічна лікарня",
                        "hospital_type": "GENERAL",
                        "address": "вул. Шевченка, 100",
                        "city": "Київ",
                        "region": "Київська область",
                        "country": "Ukraine",
                        "phone_number": "+380441234567",
                        "email": "info@okl.ua",
                        "website": "https://okl.ua",
                        "created_at": "2023-01-01T12:00:00",
                        "updated_at": "2023-01-01T12:00:00"
                    }
                ],
                "total": 10,
                "page": 1,
                "size": 10,
                "pages": 1
            }
        }

class HospitalStatsResponse(BaseModel):
    """Schema for hospital statistics"""
    id: int
    name: str
    staff_count: int = 0
    blood_requests_count: int = 0
    active_requests: int = 0
    scheduled_donations: int = 0
    completed_donations: int = 0
    

class IdenticalNeedsRequest(BaseModel):
    reference_hospital_id: int = Field(..., description="ID of the reference hospital", example=1)
    time_period_days: int = Field(30, description="Look at requests from the past N days", ge=1, le=365)
    min_shortage_percent: float = Field(25.0, description="Minimum shortage percentage to consider", ge=0, le=100)
    limit: int = Field(50, description="Maximum number of results", ge=1, le=100)

class IdenticalNeedsResponse(BaseModel):
    hospital_id: int
    hospital_name: str
    city: Optional[str] = None
    region: Optional[str] = None
    blood_types_str: str
    blood_type_count: int
    reference_hospital_name: str
    reference_city: Optional[str] = None
    reference_region: Optional[str] = None
    reference_blood_types: str