from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional
from enum import Enum 


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


class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    DONOR = "donor"
    HOSPITAL_STAFF = "hospital_staff"


class RoleUpdate(BaseModel):
    role: RoleEnum = Field(..., description="The role to set or modify")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "donor"
            }
        }

class RoleResponse(BaseModel):
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Role donor added to user with ID 1"
            }
        }

class UserRolesResponse(BaseModel):
    user_id: int = Field(..., description="User ID")
    roles: list[str] = Field(..., description="List of user's active roles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "roles": ["user", "donor"]
            }
        }


class UserUpdate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    phone_number: str = Field(..., description="User's phone number in E.164 format")
    
    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format - using Ukrainian format as an example"""
        pattern = r'^\+?380\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in Ukrainian format (+380XXXXXXXXX)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "+380123456789"
            }
        }


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    is_user: bool
    is_admin: bool
    is_super_admin: bool
    is_donor: bool
    is_hospital_staff: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str