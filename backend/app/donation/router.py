from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime

from app.donation.schemas import DonationCreate, DonationResponse, DonationUpdate, DonationStatusUpdate
from app.donation.dao import DonationDAO
from app.donor.dao import DonorDAO
from app.hospital.dao import HospitalDAO
from app.blood_request.dao import BloodRequestDAO
from app.users.dependencies import get_current_user, get_current_admin_user, get_admin_or_hospital_staff
from app.users.models import User


router = APIRouter(prefix='/donations', tags=['Donations'])


@router.post("/", 
            response_model=DonationResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Schedule a new blood donation",
            dependencies=[Depends(get_admin_or_hospital_staff)])
async def create_donation(donation_data: DonationCreate):
    """
    Schedule a new blood donation.
    
    This endpoint allows hospital staff to schedule a new blood donation,
    either for a specific blood request or as a general donation.
    
    Args:
        donation_data: Details of the donation including donor, hospital, and blood type
        
    Returns:
        The created donation record
        
    Raises:
        404: If the donor, hospital, or blood request doesn't exist
    """
    donor = await DonorDAO.find_one_or_none(id=donation_data.donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor with ID {donation_data.donor_id} not found"
        )
        
    if not donor.is_eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Donor is currently not eligible to donate blood"
        )
    
    hospital = await HospitalDAO.find_one_or_none(id=donation_data.hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {donation_data.hospital_id} not found"
        )
    
    if donation_data.blood_request_id:
        blood_request = await BloodRequestDAO.find_one_or_none(id=donation_data.blood_request_id)
        if not blood_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blood request with ID {donation_data.blood_request_id} not found"
            )
    
    donation = await DonationDAO.create_donation(**donation_data.dict())
    
    return donation


@router.get("/{donation_id}", 
           response_model=DonationResponse,
           summary="Get donation by ID",
           dependencies=[Depends(get_admin_or_hospital_staff)])
async def get_donation(donation_id: int):
    """
    Retrieve a specific donation by ID.
    
    Args:
        donation_id: ID of the donation to retrieve
        
    Returns:
        The donation details
        
    Raises:
        404: If the donation doesn't exist
    """
    donation = await DonationDAO.find_one_or_none(id=donation_id)
    
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID {donation_id} not found"
        )
    
    return donation


@router.get("/", 
           response_model=List[DonationResponse],
           summary="Get all donations with optional filtering",
           dependencies=[Depends(get_admin_or_hospital_staff)])
async def get_donations(
    donor_id: Optional[int] = None,
    hospital_id: Optional[int] = None,
    blood_request_id: Optional[int] = None,
    status: Optional[str] = None
):
    """
    Get all donations with optional filtering by donor, hospital, blood request, or status.
    
    Args:
        donor_id: Filter by donor ID
        hospital_id: Filter by hospital ID
        blood_request_id: Filter by blood request ID
        status: Filter by donation status
        
    Returns:
        List of donations matching the filter criteria
    """
    filters = {}
    
    if donor_id:
        filters["donor_id"] = donor_id
        
    if hospital_id:
        filters["hospital_id"] = hospital_id
        
    if blood_request_id:
        filters["blood_request_id"] = blood_request_id
        
    if status:
        filters["status"] = status
    
    donations = await DonationDAO.find_all(**filters)
    
    return donations


@router.put("/{donation_id}", 
           response_model=DonationResponse,
           summary="Update donation details",
           dependencies=[Depends(get_admin_or_hospital_staff)])
async def update_donation(donation_id: int, donation_data: DonationUpdate):
    """
    Update the details of an existing donation.
    
    Only specific fields can be updated, and only if the donation
    is still in 'scheduled' status.
    
    Args:
        donation_id: ID of the donation to update
        donation_data: Updated donation details
        
    Returns:
        The updated donation
        
    Raises:
        404: If the donation doesn't exist
        400: If the donation can't be updated due to its current status
    """
    donation = await DonationDAO.find_one_or_none(id=donation_id)
    
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID {donation_id} not found"
        )
    
    if donation.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled donations can be updated"
        )
    
    update_data = {k: v for k, v in donation_data.dict().items() if v is not None}
    
    updated_donation = await DonationDAO.update(donation_id, **update_data)
    
    return updated_donation


@router.patch("/{donation_id}/status", 
             response_model=DonationResponse,
             summary="Update donation status",
             dependencies=[Depends(get_admin_or_hospital_staff)])
async def update_donation_status(donation_id: int, status_data: DonationStatusUpdate):
    """
    Update the status of a donation.
    
    This endpoint allows changing a donation's status, for example
    marking it as completed or cancelled.
    
    Args:
        donation_id: ID of the donation to update
        status_data: New status and optional reason
        
    Returns:
        The updated donation
        
    Raises:
        404: If the donation doesn't exist
        400: If the status transition is not allowed
    """
    donation = await DonationDAO.find_one_or_none(id=donation_id)
    
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID {donation_id} not found"
        )
    
    if status_data.status == "completed":
        if not donation.complete():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This donation cannot be marked as completed (must be in scheduled status)"
            )
    elif status_data.status == "cancelled":
        if not donation.cancel(status_data.reason):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This donation cannot be cancelled (must be in scheduled status)"
            )
    else:
        donation = await DonationDAO.update_status(
            donation_id,
            status_data.status,
            status_data.reason
        )
    
    await DonationDAO.update(donation_id, status=donation.status, notes=donation.notes)
    
    return donation


@router.get("/donor/{donor_id}", 
           response_model=List[DonationResponse],
           summary="Get all donations for a donor",
           dependencies=[Depends(get_admin_or_hospital_staff)])
async def get_donor_donations(donor_id: int):
    """
    Get all donations for a specific donor.
    
    Args:
        donor_id: ID of the donor
        
    Returns:
        List of donations for the donor
        
    Raises:
        404: If the donor doesn't exist
    """
    donor = await DonorDAO.find_one_or_none(id=donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor with ID {donor_id} not found"
        )
    
    donations = await DonationDAO.get_donor_donations(donor_id)
    
    return donations


@router.get("/my-donations", 
           response_model=List[DonationResponse],
           summary="Get my donation history")
async def get_my_donations(current_user: User = Depends(get_current_user)):
    """
    Get all donations for the currently authenticated user.
    
    Returns:
        List of the user's donations
        
    Raises:
        403: If the user is not a donor
        404: If the donor profile doesn't exist
    """
    if not current_user.is_donor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have a donor role"
        )
    
    donor = await DonorDAO.find_one_or_none(user_id=current_user.id)
    
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor profile not found"
        )
    
    donations = await DonationDAO.get_donor_donations(donor.id)
    
    return donations