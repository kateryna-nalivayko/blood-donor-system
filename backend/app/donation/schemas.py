from enum import Enum
from pydantic import BaseModel, Field, field_validator
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

class DonationStatisticsParams(BaseModel):
    min_donations: int = Field(10, description="Minimum number of donations received", ge=1)
    min_total_ml: int = Field(5000, description="Minimum total blood volume collected in ml", ge=500)
    blood_type: Optional[str] = Field(None, description="Optional blood type filter")
    months: int = Field(3, description="Look back period in months", ge=1)
    limit: int = Field(50, description="Maximum number of results", le=1000)
    
    @field_validator('blood_type')
    def validate_blood_type(cls, v):
        if v is None:
            return v
        try:
            BloodType(v)
            return v
        except ValueError:
            valid_types = [t.value for t in BloodType]
            raise ValueError(f"Invalid blood type. Must be one of: {', '.join(valid_types)}")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "min_donations": 10,
                "min_total_ml": 5000,
                "blood_type": "O+",
                "months": 3,
                "limit": 50
            }
        }
    }

class DonationStatisticsResponse(BaseModel):
    region: str
    blood_type: str
    region_donation_count: int
    region_collected_ml: int
    hospital_count: int
    avg_donation_ml: float
    total_donors: int
    hospitals: str


class DemographicChoices(str, Enum):
    AGE_GROUP = "age_group"
    GENDER = "gender"
    BLOOD_TYPE = "blood_type"
    REGION = "region"

class DonationDemographicsParams(BaseModel):
    min_age: int = Field(18, description="Minimum donor age", ge=18)
    max_age: int = Field(65, description="Maximum donor age", le=100)
    min_donations: int = Field(3, description="Minimum number of donations per person", ge=1)
    months: int = Field(12, description="Look back period in months", ge=1)
    group_by: DemographicChoices = Field(DemographicChoices.AGE_GROUP, description="Demographic grouping")
    limit: int = Field(50, description="Maximum number of results", le=1000)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "min_age": 18,
                "max_age": 65,
                "min_donations": 3,
                "months": 12,
                "group_by": "age_group",
                "limit": 50
            }
        }
    }

class DonationDemographicsResponse(BaseModel):
    demographic_group: str
    donor_count: int
    total_donations: int
    avg_donations_per_donor: float
    avg_donation_ml: float
    max_donations_by_donor: int
    total_donated_ml: int
    avg_days_between_donations: float