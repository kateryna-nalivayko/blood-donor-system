from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class DonorProfileCreate(BaseModel):
    blood_type: BloodType = Field(..., description="Blood type of the donor")
    gender: Gender = Field(..., description="Gender of the donor")
    date_of_birth: date = Field(..., description="Date of birth")
    weight: float = Field(..., ge=50.0, description="Weight in kg (minimum 50kg required)")
    height: float = Field(..., ge=120.0, le=220.0, description="Height in cm (between 120-220cm)")
    
    @field_validator('date_of_birth')
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Donor must be at least 18 years old')
        if age > 65:
            raise ValueError('Donor must be 65 years old or younger')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "blood_type": "O+",
                "gender": "male",
                "date_of_birth": "1990-01-01",
                "weight": 75.5,
                "height": 180.0
            }
        }


class DonorEligibilityUpdate(BaseModel):
    is_eligible: bool = Field(
        ..., 
        description="Whether the donor is eligible to donate"
    )
    ineligible_until: Optional[date] = Field(
        None, 
        description="Date when donor becomes eligible again (for temporary deferrals)"
    )
    health_notes: Optional[str] = Field(
        None, 
        description="Health notes or reason for deferral",
        max_length=500
    )
    
    @field_validator('ineligible_until')
    def validate_deferral_date(cls, v, values):
        is_eligible = values.data.get('is_eligible')
        
        # If marked as ineligible, a date should be provided (for temporary deferrals)
        if not is_eligible and v is None:
            raise ValueError('Ineligible until date is required when marking donor as ineligible')
            
        # Date should be in the future
        if v and v <= date.today():
            raise ValueError('Ineligible until date must be in the future')
            
        # If eligible, don't set a deferral date
        if is_eligible and v is not None:
            raise ValueError('Ineligible until date should not be set for eligible donors')
            
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_eligible": False,
                "ineligible_until": "2025-09-25",
                "health_notes": "Recent medication usage"
            }
        }

class DonorBloodTypeQueryParams(BaseModel):
    blood_type: str = Field(..., description="Blood type to filter by")
    min_donations: int = Field(1, description="Minimum number of donations required", ge=1)
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
                "min_donations": 2,
                "limit": 50
            }
        }
    }


class DonorProfileResponse(BaseModel):
    id: int
    user_id: int
    blood_type: str
    gender: str
    date_of_birth: date
    weight: float
    height: float
    

    last_donation_date: Optional[date] = None
    first_donation_date: Optional[date] = None
    total_donations: int
    

    is_eligible: bool
    ineligible_until: Optional[date] = None
    health_notes: Optional[str] = None
    

    age: int
    can_donate: bool
    

    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "json_schema_extra":
         {
            "example": {
                "id": 1,
                "user_id": 42,
                "blood_type": "O+",
                "gender": "male",
                "date_of_birth": "1990-01-01",
                "weight": 75.5,
                "height": 180.0,
                "last_donation_date": "2025-01-15",
                "first_donation_date": "2024-05-10",
                "total_donations": 3,
                "is_eligible": True,
                "ineligible_until": None,
                "health_notes": None,
                "age": 35,
                "can_donate": True,
                "created_at": "2025-03-25T10:30:00",
                "updated_at": "2025-03-25T10:30:00"
            }
        }
    }


class DonorEligibilityResponse(BaseModel):
    can_donate: bool
    is_eligible: bool
    age_eligible: bool
    time_since_last_donation_eligible: bool
    ineligible_until: Optional[date] = None
    health_notes: Optional[str] = None
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "can_donate": True,
                "is_eligible": True,
                "age_eligible": True,
                "time_since_last_donation_eligible": True,
                "ineligible_until": None,
                "health_notes": None,
                "message": "You are eligible to donate blood."
            }
        }


class DonorWithDonationsResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    donor_id: int
    blood_type: str
    donation_count: int
    total_donated_ml: int
    last_donation_date: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 42,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "+380991234567",
                "donor_id": 15,
                "blood_type": "A+",
                "donation_count": 5,
                "total_donated_ml": 2250,
                "last_donation_date": "2025-03-15T14:30:00"
            }
        }
    }