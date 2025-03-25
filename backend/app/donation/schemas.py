from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.common.enums import BloodType, DonationStatus


class DonationCreate(BaseModel):
    donor_id: int = Field(..., description="ID of the donor")
    hospital_id: int = Field(..., description="ID of the hospital where donation takes place")
    blood_request_id: Optional[int] = Field(None, description="ID of the related blood request, if any")
    blood_amount_ml: int = Field(
        ..., 
        ge=100, 
        le=1000, 
        description="Amount of blood donated in milliliters (100-1000ml)"
    )
    blood_type: BloodType = Field(..., description="Type of donated blood")
    donation_date: datetime = Field(
        default_factory=datetime.now,
        description="Date and time of the donation"
    )
    status: DonationStatus = Field(
        default=DonationStatus.SCHEDULED,
        description="Status of the donation"
    )
    notes: Optional[str] = Field(None, description="Additional notes about the donation")
    
    model_config = {
        "json_schema_extra":{
            "example": {
                "donor_id": 1,
                "hospital_id": 1,
                "blood_request_id": None,
                "blood_amount_ml": 450,
                "blood_type": "A+",
                "donation_date": "2025-04-15T10:00:00",
                "status": "scheduled",
                "notes": "First-time donor"
            }
        }
    }


class DonationResponse(BaseModel):
    id: int
    donor_id: int
    hospital_id: int
    blood_request_id: Optional[int] = None
    blood_amount_ml: int
    blood_type: str
    donation_date: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "donor_id": 1,
                "hospital_id": 1,
                "blood_request_id": None,
                "blood_amount_ml": 450,
                "blood_type": "A+",
                "donation_date": "2025-04-15T10:00:00",
                "status": "completed",
                "notes": "First-time donor",
                "created_at": "2025-03-25T10:30:00",
                "updated_at": "2025-04-15T10:45:00"
            }
        }
    }


class DonationUpdate(BaseModel):
    blood_amount_ml: Optional[int] = Field(
        None, 
        ge=100, 
        le=1000, 
        description="Amount of blood donated in milliliters"
    )
    blood_type: Optional[BloodType] = Field(None, description="Type of donated blood")
    donation_date: Optional[datetime] = Field(None, description="Date and time of the donation")
    notes: Optional[str] = Field(None, description="Additional notes about the donation")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "blood_amount_ml": 450,
                "notes": "Donation went smoothly"
            }
        }
    }


class DonationStatusUpdate(BaseModel):
    status: DonationStatus = Field(..., description="New status for the donation")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "reason": "Donation successfully completed"
            }
        }
    }