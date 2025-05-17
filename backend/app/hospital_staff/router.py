from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.hospital_staff.dao import HospitalStaffDAO
from app.hospital_staff.schemas import HospitalStaffProfileCreate, HospitalStaffProfileResponse, MatchingStaffPatternsRequest, MatchingStaffPatternsResponse, StaffPerformanceParams, StaffPerformanceResponse
from app.users.dao import UsersDAO
from app.users.dependencies import get_admin_or_hospital_staff, get_current_hospital_staff, get_current_user
from app.users.models import User
from app.hospital.dao import HospitalDAO
from app.donor.dao import DonorDAO


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


@router.get(
    "/analytics/matching-patterns",
    response_model=List[MatchingStaffPatternsResponse],
    summary="Find staff with matching request patterns",
    description="Finds pairs of hospital staff who have created the same pattern of blood type requests"
)
async def get_staff_with_matching_patterns(
    query: MatchingStaffPatternsRequest = Depends(),
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Find pairs of hospital staff who have created the same pattern of blood type requests.
    This can help identify staff with similar specialties or departments that may benefit
    from coordination or knowledge sharing.
    """
    return await HospitalStaffDAO.find_staff_with_matching_request_patterns(
        min_blood_types=query.min_blood_types,
        min_similarity_percent=query.min_similarity_percent,
        time_period_months=query.time_period_months,
        limit=query.limit
    )

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional


@router.get("/analytics/doctor-donor-supersets",
    summary="Find doctors where one's donor set is a superset of another's",
    response_model=List[Dict[str, Any]])
async def find_doctors_with_donor_supersets(
    min_donor_count: int = Query(2, description="Minimum number of donors per doctor"),
    min_similarity_percent: float = Query(50.0, description="Minimum percentage of shared donors"),
    specific_hospital_id: Optional[int] = Query(None, description="Filter by specific hospital"),
    limit: int = Query(50, description="Maximum number of results"),
    current_staff = Depends(get_current_hospital_staff)
) -> List[Dict[str, Any]]:
    """Find pairs of doctors where one doctor's donor set significantly overlaps with another's."""
    return await HospitalStaffDAO.find_doctors_with_donor_supersets(
        min_donor_count=min_donor_count,
        min_similarity_percent=min_similarity_percent,
        specific_hospital_id=specific_hospital_id,
        limit=limit
    )

@router.get("/analytics/hospital-blood-patterns")
async def find_hospitals_with_similar_blood_request_patterns(
    min_similarity_percent: float = Query(75.0, description="Minimum similarity percentage"),
    min_request_count: int = Query(5, description="Minimum number of blood requests per hospital"),
    time_period_months: int = Query(12, description="Period in months to analyze"),
    limit: int = Query(50, description="Maximum number of results"),
    current_staff = Depends(get_current_hospital_staff)
) -> List[Dict[str, Any]]:
    """Find pairs of hospitals with similar blood request patterns."""
    return await HospitalDAO.find_hospitals_with_similar_blood_request_patterns(
        min_similarity_percent=min_similarity_percent,
        min_request_count=min_request_count,
        time_period_months=time_period_months,
        limit=limit
    )

@router.get("/analytics/multi-request-donors")
async def find_donors_matching_multiple_requests(
    min_match_count: int = Query(2, description="Minimum number of requests a donor can fulfill"),
    max_distance_km: float = Query(50.0, description="Maximum distance between donor and hospital in km"),
    region: Optional[str] = Query(None, description="Filter by specific region"),
    blood_type: Optional[str] = Query(None, description="Filter by specific blood type"),
    limit: int = Query(50, description="Maximum number of results"),
    current_staff = Depends(get_current_hospital_staff)
) -> List[Dict[str, Any]]:
    """Find donors who can potentially fulfill multiple pending blood requests."""
    return await DonorDAO.find_donors_matching_multiple_requests(
        min_match_count=min_match_count,
        max_distance_km=max_distance_km,
        region=region,
        blood_type=blood_type,
        limit=limit
    )

@router.get("/analytics/seasonal-blood-patterns",
    summary="Analyze seasonal patterns in blood type requests",
    response_model=List[Dict[str, Any]])
async def find_seasonal_blood_request_patterns(
    min_request_count: int = Query(10, description="Minimum request count for inclusion"),
    analysis_years: int = Query(2, description="Number of years to analyze"),
    region: Optional[str] = Query(None, description="Filter by specific region"),
    limit: int = Query(50, description="Maximum number of results"),
    current_staff = Depends(get_current_hospital_staff)
) -> List[Dict[str, Any]]:
    """
    Analyze seasonal trends and patterns in blood type requests across regions.
    
    This endpoint helps identify which blood types are more in demand during 
    specific seasons, allowing for better planning of blood donation campaigns.
    """
    return await HospitalStaffDAO.find_seasonal_blood_request_patterns(
        min_request_count=min_request_count,
        analysis_years=analysis_years,
        region=region,
        limit=limit
    )