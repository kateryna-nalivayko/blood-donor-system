from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timedelta
from app.blood_request.schemas import (
    BloodRequestCreate, 
    BloodRequestResponse, 
    BloodRequestUpdate, 
    BloodRequestStatusUpdate,
    BloodRequestSummary,
    BloodShortageQueryParams,
    BloodShortageResponse,
    HighVolumeRequestParams,
    HighVolumeRequestResponse
)
from app.blood_request.dao import BloodRequestDAO
from app.donation.dao import DonationDAO
from app.hospital_staff.dao import HospitalStaffDAO
from app.users.dependencies import get_current_admin_user, get_current_hospital_staff, get_admin_or_hospital_staff
from app.users.models import User


router = APIRouter(prefix='/blood-requests', tags=['Blood Requests'])


@router.post("/", 
            response_model=BloodRequestResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new blood request")
async def create_blood_request(
    request_data: BloodRequestCreate,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Create a new blood request.
    
    This endpoint is only accessible to hospital staff and automatically
    populates the hospital_id and staff_id from the authenticated user's profile.
    
    Args:
        request_data: Blood request details
        
    Returns:
        The created blood request
    """
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    
    if not staff_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital staff profile not found for current user"
        )
    
    blood_request_data = request_data.model_dump()
    blood_request_data["hospital_id"] = staff_profile.hospital_id
    blood_request_data["staff_id"] = staff_profile.id
    blood_request_data["status"] = "pending"  
    blood_request_data["request_date"] = datetime.now()
    
    if not blood_request_data.get("needed_by_date"):
        days = 1 if blood_request_data["urgency_level"] >= 4 else 7
        blood_request_data["needed_by_date"] = datetime.now() + timedelta(days=days)
    
    blood_request = await BloodRequestDAO.add(**blood_request_data)
    
    return blood_request


@router.get("/", 
           response_model=List[BloodRequestResponse],
           summary="Get all blood requests")
async def get_blood_requests(
    hospital_id: Optional[int] = None,
    status: Optional[str] = None,
    blood_type: Optional[str] = None,
    urgency_min: Optional[int] = None,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Get all blood requests with optional filtering.
    
    Args:
        hospital_id: Filter by hospital ID
        status: Filter by request status
        blood_type: Filter by blood type
        urgency_min: Filter by minimum urgency level (1-5)
        
    Returns:
        List of blood requests matching the filter criteria
    """
    filters = {}
    
    if not current_user.is_admin:
        staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
        if not staff_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital staff profile not found"
            )
        filters["hospital_id"] = staff_profile.hospital_id
    elif hospital_id:
        filters["hospital_id"] = hospital_id
    
    if status:
        filters["status"] = status
        
    if blood_type:
        filters["blood_type"] = blood_type
    
    if urgency_min is not None:
        if urgency_min < 1 or urgency_min > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Urgency level must be between 1 and 5"
            )
            
        blood_requests = await BloodRequestDAO.find_by_min_urgency(
            urgency_min=urgency_min, 
            **filters
        )
    else:
        blood_requests = await BloodRequestDAO.find_all(**filters)
    
    return blood_requests


@router.get("/my-hospital", 
           response_model=List[BloodRequestResponse],
           summary="Get blood requests for my hospital")
async def get_my_hospital_blood_requests(
    status: Optional[str] = None,
    urgency_min: Optional[int] = None,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Get all blood requests for the staff member's hospital.
    
    Args:
        status: Filter by request status
        urgency_min: Filter by minimum urgency level (1-5)
        
    Returns:
        List of blood requests for the user's hospital
    """
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    
    if not staff_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital staff profile not found"
        )
    
    filters = {"hospital_id": staff_profile.hospital_id}
    
    if status:
        filters["status"] = status
    
    if urgency_min is not None:
        if urgency_min < 1 or urgency_min > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Urgency level must be between 1 and 5"
            )
        blood_requests = await BloodRequestDAO.find_by_min_urgency(
            urgency_min=urgency_min, 
            **filters
        )
    else:
        blood_requests = await BloodRequestDAO.find_all(**filters)
    
    return blood_requests


@router.get("/summary", 
           response_model=BloodRequestSummary,
           summary="Get blood request statistics")
async def get_blood_request_summary(
    hospital_id: Optional[int] = None,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Get summary statistics for blood requests.
    
    Args:
        hospital_id: Filter by hospital ID (admins only)
        
    Returns:
        Summary statistics about blood requests
    """
    if not current_user.is_admin and hospital_id:
        staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
        if staff_profile and hospital_id != staff_profile.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view statistics for your own hospital"
            )
    
    if not current_user.is_admin and not hospital_id:
        staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
        if not staff_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital staff profile not found"
            )
        hospital_id = staff_profile.hospital_id
    
    summary = await BloodRequestDAO.get_summary(hospital_id)
    
    return summary


@router.get("/{request_id}", 
           response_model=BloodRequestResponse,
           summary="Get blood request by ID")
async def get_blood_request(
    request_id: int,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Retrieve a specific blood request by ID.
    
    Args:
        request_id: ID of the blood request to retrieve
        
    Returns:
        The blood request details
        
    Raises:
        404: If the blood request doesn't exist
        403: If user doesn't have permission to view the request
    """
    blood_request = await BloodRequestDAO.find_one_or_none(id=request_id)
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blood request with ID {request_id} not found"
        )
    
    if not current_user.is_admin:
        staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
        if not staff_profile or blood_request.hospital_id != staff_profile.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view blood requests for your own hospital"
            )
    
    return blood_request


@router.put("/{request_id}", 
           response_model=BloodRequestResponse,
           summary="Update blood request")
async def update_blood_request(
    request_id: int,
    request_data: BloodRequestUpdate,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Update an existing blood request.
    
    Only the hospital staff who created the request or an admin can update it.
    Updates are only allowed for requests with status pending or approved.
    """
    # Get the staff profile to check hospital association
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    if not staff_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital staff profile not found"
        )

    # Find the blood request
    blood_request = await BloodRequestDAO.find_one_or_none(id=request_id)
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blood request with id {request_id} not found"
        )
    
    # Check if user has permission to update this request
    if blood_request.hospital_id != staff_profile.hospital_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this blood request"
        )
    
    # Check if request can be updated based on status
    allowed_statuses = ["pending", "approved"]
    if blood_request.status.lower() not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update a blood request with status '{blood_request.status}'"
        )
    
    # Prepare update data by filtering out None values
    update_data = request_data.model_dump(exclude_unset=True, exclude_none=True)
    
    # Check if there's anything to update
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid update data provided"
        )
    
    # Update the blood request - pass the request_id directly, not a clause
    updated_request = await BloodRequestDAO.update(request_id, **update_data)
    
    if not updated_request:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update blood request"
        )
    
    return updated_request


@router.patch("/{request_id}/status", 
             response_model=BloodRequestResponse,
             summary="Update blood request status")
async def update_blood_request_status(
    request_id: int,
    status_data: BloodRequestStatusUpdate,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Update the status of a blood request.
    
    Args:
        request_id: ID of the blood request to update
        status_data: New status and optional reason
        
    Returns:
        The updated blood request
        
    Raises:
        404: If the blood request doesn't exist
        403: If user doesn't have permission to update the request
        400: If the status transition is not allowed
    """
    blood_request = await BloodRequestDAO.find_one_or_none(id=request_id)
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blood request with ID {request_id} not found"
        )
    
    if not current_user.is_admin:
        staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
        if not staff_profile or blood_request.hospital_id != staff_profile.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update blood requests for your own hospital"
            )
    
    valid_transitions = {
        "pending": ["approved", "canceled"],
        "approved": ["fulfilled", "canceled"],
        "fulfilled": [],
        "canceled": []
    }
    
    if status_data.status not in valid_transitions.get(blood_request.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change status from '{blood_request.status}' to '{status_data.status}'"
        )
    
    update_data = {"status": status_data.status}
    
    if status_data.reason:
        update_notes = status_data.reason
        if blood_request.notes:
            update_notes = f"{blood_request.notes}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {status_data.reason}"
        update_data["notes"] = update_notes
    
    updated_request = await BloodRequestDAO.update(request_id, **update_data)
    
    if status_data.status == "fulfilled":
        donations = await DonationDAO.get_request_donations(request_id)
        for donation in donations:
            if donation.status == "scheduled":
                await DonationDAO.update_status(donation.id, "completed", "Blood request fulfilled")
    
    return updated_request


@router.delete("/{request_id}", 
              status_code=status.HTTP_204_NO_CONTENT,
              summary="Delete a blood request",
              dependencies=[Depends(get_admin_or_hospital_staff)])
async def delete_blood_request(request_id: int):
    """
    Delete a blood request (admin only) & (hospitall staf).
    
    Args:
        request_id: ID of the blood request to delete
        
    Raises:
        404: If the blood request doesn't exist
    """
    blood_request = await BloodRequestDAO.find_one_or_none(id=request_id)
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sorry, we couldn't find blood request #{request_id}. Please verify the request ID and try again."
        )
    
    donations = await DonationDAO.get_request_donations(request_id)
    completed_donations = [d for d in donations if d.status == "completed"]
    
    if completed_donations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This blood request has {len(completed_donations)} completed donation(s) "
                f"and cannot be deleted. Blood requests with completed donations must be "
                f"preserved for medical records. Consider marking it as 'canceled' instead."
            )
        )
    
    scheduled_donations = [d for d in donations if d.status == "scheduled"]
    if scheduled_donations:
        print(f"Unlinking {len(scheduled_donations)} scheduled donations from request #{request_id}")
        
    for donation in scheduled_donations:
        await DonationDAO.update(donation.id, blood_request_id=None)
    
    await BloodRequestDAO.delete(id=request_id)
    
    return None



@router.get("/query/hospitals-with-shortages", response_model=List[BloodShortageResponse])
async def get_hospitals_with_blood_shortages(
    query_params: BloodShortageQueryParams = Depends(),
    current_user: User = Depends(get_current_hospital_staff)
):
    """Find hospitals with blood requests matching a specific blood type but not enough donations"""
    
    shortages = await BloodRequestDAO.find_hospitals_with_shortages(
        blood_type=query_params.blood_type,
        fulfillment_percentage=query_params.fulfillment_percentage,
        limit=query_params.limit
    )
    
    if not shortages:
        return []
    
    return shortages


@router.get("/query/high-volume-requests", response_model=List[HighVolumeRequestResponse])
async def get_high_volume_requests(
    query_params: HighVolumeRequestParams = Depends(),
    current_user: User = Depends(get_current_hospital_staff)
):
    """Find high-volume blood requests with minimum urgency level"""
    
    requests = await BloodRequestDAO.find_high_volume_requests(
        min_volume_ml=query_params.min_volume_ml,
        min_urgency=query_params.min_urgency,
        days=query_params.days,
        limit=query_params.limit
    )
    
    if not requests:
        return []
    
    return requests