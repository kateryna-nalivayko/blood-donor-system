from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime, timedelta
from app.common.enums import BloodType, RequestStatus


class BloodRequestCreate(BaseModel):
    """Schema for creating a new blood request"""
    blood_type: BloodType = Field(..., description="Required blood type")
    amount_needed_ml: int = Field(
        ..., 
        ge=100, 
        le=10000, 
        description="Amount of blood needed in milliliters (100-10000ml)"
    )
    patient_info: Optional[str] = Field(
        None, 
        description="Patient information (anonymized)"
    )
    urgency_level: int = Field(
        3,  
        ge=1, 
        le=5, 
        description="Urgency level: 1 (low) to 5 (critical)"
    )
    needed_by_date: Optional[datetime] = Field(
        None,
        description="Date by which blood is needed"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the request"
    )
    
    
    @field_validator('needed_by_date')
    def validate_needed_by_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Needed by date must be in the future")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "blood_type": "O+",
                "amount_needed_ml": 1000,
                "patient_info": "45-year-old male, surgery patient",
                "urgency_level": 4,
                "needed_by_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "notes": "Patient scheduled for emergency surgery"
            }
        }
    }


class BloodRequestResponse(BaseModel):
    """Schema for blood request responses"""
    id: int
    hospital_id: int
    staff_id: int
    blood_type: str
    amount_needed_ml: int
    patient_info: Optional[str] = None
    urgency_level: int
    status: str
    request_date: datetime
    needed_by_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    collected_amount_ml: int
    fulfillment_percentage: float
    days_until_needed: Optional[int] = None
    is_fulfilled: bool
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "hospital_id": 1,
                "staff_id": 2,
                "blood_type": "O+",
                "amount_needed_ml": 1000,
                "patient_info": "45-year-old male, surgery patient",
                "urgency_level": 4,
                "status": "pending",
                "request_date": "2025-03-26T10:30:00",
                "needed_by_date": "2025-03-28T10:30:00",
                "notes": "Patient scheduled for emergency surgery",
                "created_at": "2025-03-26T10:30:00",
                "updated_at": "2025-03-26T10:30:00",
                "collected_amount_ml": 250,
                "fulfillment_percentage": 25.0,
                "days_until_needed": 2,
                "is_fulfilled": False
            }
        }
    }


class BloodRequestUpdate(BaseModel):
    """Schema for updating a blood request"""
    blood_type: Optional[BloodType] = None
    amount_needed_ml: Optional[int] = Field(
        None, 
        ge=100, 
        le=10000
    )
    patient_info: Optional[str] = None
    urgency_level: Optional[int] = Field(
        None,
        ge=1, 
        le=5
    )
    needed_by_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    @field_validator('needed_by_date')
    def validate_needed_by_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Needed by date must be in the future")
        return v
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "urgency_level": 5,
                "notes": "Urgency increased due to patient condition"
            }
        }
    }


class BloodRequestStatusUpdate(BaseModel):
    """Schema for updating a blood request status"""
    status: RequestStatus = Field(
        ..., 
        description="New status for the blood request"
    )
    reason: Optional[str] = Field(
        None, 
        description="Reason for status change"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "fulfilled",
                "reason": "All required blood has been collected"
            }
        }
    }


class BloodRequestSummary(BaseModel):
    """Summary statistics for blood requests"""
    total_requests: int
    pending_requests: int
    fulfilled_requests: int
    urgent_requests: int  
    by_blood_type: dict
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_requests": 25,
                "pending_requests": 12,
                "fulfilled_requests": 10,
                "urgent_requests": 5,
                "by_blood_type": {
                    "A+": 5,
                    "O+": 8,
                    "B-": 3,
                }
            }
        }
    }


class BloodShortageQueryParams(BaseModel):
    blood_type: str = Field(..., description="Blood type to filter by")
    fulfillment_percentage: float = Field(
        50.0, 
        description="Maximum fulfillment percentage to be considered a shortage (e.g. 50 means less than 50% fulfilled)", 
        ge=0.0, 
        le=100.0
    )
    limit: int = Field(100, description="Maximum number of results", le=1000)
    
    @field_validator('blood_type')
    def validate_blood_type(cls, v):
        try:
            BloodType(v)
            return v
        except ValueError:
            valid_types = [t.value for t in BloodType]
            raise ValueError(f"Invalid blood type. Must be one of: {', '.join(valid_types)}")

    model_config = {
        "json_schema_extra": {
            "example": {
                "blood_type": "O+",
                "fulfillment_percentage": 50.0,
                "limit": 50
            }
        }
    }

class BloodShortageResponse(BaseModel):
    hospital_id: int
    hospital_name: str
    city: str
    request_id: int
    blood_type: str
    amount_needed_ml: int
    collected_ml: int
    shortage_ml: int
    needed_by_date: date
    fulfillment_percentage: float
    urgency_level: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "hospital_id": 1,
                "hospital_name": "City General Hospital",
                "city": "Kyiv",
                "request_id": 42,
                "blood_type": "A+",
                "amount_needed_ml": 2000,
                "collected_ml": 800,
                "shortage_ml": 1200,
                "needed_by_date": "2025-05-15",
                "fulfillment_percentage": 40.0,
                "urgency_level": 4
            }
        }
    }


class HighVolumeRequestParams(BaseModel):
    min_volume_ml: int = Field(1000, description="Minimum volume needed in ml", ge=100)
    min_urgency: int = Field(3, description="Minimum urgency level", ge=1, le=5)
    days: int = Field(30, description="Look ahead period in days", ge=1)
    limit: int = Field(50, description="Maximum number of results", le=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "min_volume_ml": 1000,
                "min_urgency": 3,
                "days": 30,
                "limit": 50
            }
        }
    }

class HighVolumeRequestResponse(BaseModel):
    request_id: int
    hospital_id: int
    hospital_name: str
    city: str
    region: str
    blood_type: str
    amount_needed_ml: int
    urgency_level: int
    collected_ml: int
    remaining_ml: int
    needed_by_date: date
    staff_name: str
    staff_role: str