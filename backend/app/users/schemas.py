from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional


class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    phone_number: str = Field(..., description="User's phone number in E.164 format")
    password: str = Field(..., min_length=8, description="User password")
    
    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format - using Ukrainian format as an example"""
        pattern = r'^\+?380\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in Ukrainian format (+380XXXXXXXXX)')
        return v
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        """Validate that password has sufficient complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
            
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
            
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
            
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "+380123456789",
                "password": "SecurePass123"
            }
        }


class UserAuth(BaseModel):
    email: EmailStr = Field(..., description="Your email")
    password: str = Field(..., min_length=8, max_length=50, description="Your password (min 8 characters, max 50 characters)")