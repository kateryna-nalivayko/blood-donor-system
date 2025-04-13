from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.hospital_staff.dao import HospitalStaffDAO
from app.hospital_staff.schemas import HospitalStaffProfileCreate, HospitalStaffProfileResponse, StaffPerformanceParams, StaffPerformanceResponse
from app.users.dao import UsersDAO
from app.users.dependencies import get_admin_or_hospital_staff, get_current_hospital_staff, get_current_user
from app.users.models import User
from app.hospital.dao import HospitalDAO


router = APIRouter(prefix='/hospital-staff', tags=['Hospital Staff'])


@router.post("/register-profile/", 
            response_model=HospitalStaffProfileResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register as hospital staff")
async def create_hospital_staff_profile(
    profile_data: HospitalStaffProfileCreate,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Create a hospital staff profile for the current user.
    This also sets the hospital_staff role for the user.
    
    Args:
        profile_data: Staff profile information including hospital, role and department
        
    Returns:
        The created hospital staff profile
        
    Raises:
        404: If the specified hospital doesn't exist
        400: If user already has a hospital staff profile
    """
    hospital = await HospitalDAO.find_one_or_none(id=profile_data.hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {profile_data.hospital_id} not found"
        )
    
    existing_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a hospital staff profile"
        )
    
    updated_user = await UsersDAO.set_single_role(current_user.id, "hospital_staff")
    
    staff = await HospitalStaffDAO.ensure_hospital_staff_profile(
        user_id=current_user.id,
        hospital_id=profile_data.hospital_id,
        role=profile_data.role,
        department=profile_data.department
    )
    
    return staff


@router.get("/my-profile/", 
           response_model=HospitalStaffProfileResponse,
           status_code=status.HTTP_200_OK,
           summary="Get my hospital staff profile")
async def get_my_hospital_staff_profile(current_user: User = Depends(get_current_hospital_staff)):
    """
    Retrieve the hospital staff profile for the currently authenticated user.
    
    Returns the complete hospital staff profile information including department, role,
    hospital ID.
    
    Raises:
        404: If the user doesn't have a hospital staff profile
    """
    
    donor = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor profile not found"
        )
    
    return donor


@router.get("/query/staff-performance", response_model=List[StaffPerformanceResponse])
async def get_staff_by_performance(
    query_params: StaffPerformanceParams = Depends(),
    current_user: User = Depends(get_admin_or_hospital_staff)
):
    """Find hospital staff by their blood request fulfillment rate"""
    
    staff = await HospitalStaffDAO.find_staff_by_performance(
        min_requests=query_params.min_requests,
        min_fulfillment_rate=query_params.min_fulfillment_rate,
        months=query_params.months,
        limit=query_params.limit
    )
    
    if not staff:
        return []
    
    return staff