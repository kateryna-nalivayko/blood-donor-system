from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from app.donor.schemas import DonorEligibilityUpdate, DonorProfileCreate, DonorProfileResponse
from app.donor.dao import DonorDAO
from app.users.dao import UsersDAO
from app.users.models import User
from app.users.dependencies import get_admin_or_hospital_staff, get_current_admin_user, get_current_user


router = APIRouter(prefix='/donors', tags=['Donors'])


@router.post("/register-donor-profile/", 
            response_model=DonorProfileResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register as a donor")
async def create_donor_profile(
    profile_data: DonorProfileCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a donor profile for the current user.
    This also sets the donor role for the user.
    """
    updated_user = await UsersDAO.set_single_role(current_user.id, "donor")
    
    donor = await DonorDAO.ensure_donor_profile(
        user_id=current_user.id,
        blood_type=profile_data.blood_type,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        weight=profile_data.weight,
        height=profile_data.height
    )
    
    return donor


@router.get("/my-profile/", 
           response_model=DonorProfileResponse,
           status_code=status.HTTP_200_OK,
           summary="Get my donor profile")
async def get_my_donor_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve the donor profile for the currently authenticated user.
    
    Returns the complete donor profile information including blood type,
    gender, date of birth, weight, and height.
    
    Raises:
        404: If the user doesn't have a donor profile
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
    
    return donor


@router.get("/{donor_id}/", 
           response_model=DonorProfileResponse,
           status_code=status.HTTP_200_OK,
           summary="Get donor profile by ID",
           dependencies=[Depends(get_current_admin_user)])
async def get_donor_profile(donor_id: int):
    """
    Retrieve a donor profile by ID (admin only).
    
    Args:
        donor_id: The ID of the donor profile to retrieve
        
    Returns:
        The donor profile information
        
    Raises:
        404: If the donor profile doesn't exist
    """
    donor = await DonorDAO.find_one_or_none(id=donor_id)
    
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor profile not found"
        )
    
    return donor


@router.put("/my-profile/", 
           response_model=DonorProfileResponse,
           status_code=status.HTTP_200_OK,
           summary="Update my donor profile")
async def update_my_donor_profile(
    profile_data: DonorProfileCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Update the donor profile for the currently authenticated user.
    
    Args:
        profile_data: The updated profile information
        
    Returns:
        The updated donor profile
        
    Raises:
        404: If the user doesn't have a donor profile
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
    

    updated_donor = await DonorDAO.update(
        donor.id,
        blood_type=profile_data.blood_type,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        weight=profile_data.weight,
        height=profile_data.height
    )
    
    return updated_donor


@router.patch("/{donor_id}/eligibility", 
             response_model=DonorProfileResponse,
             status_code=status.HTTP_200_OK,
             summary="Update donor eligibility status",
             dependencies=[Depends(get_admin_or_hospital_staff)])
async def update_donor_eligibility(
    donor_id: int, 
    eligibility_data: DonorEligibilityUpdate
):
    """
    Update eligibility status for a donor (admin only) & (hospital_staff).
    
    This endpoint allows administrators to update a donor's eligibility status,
    set a future date when they'll be eligible again (for temporary deferrals),
    and record health notes or reasons for deferral.
    
    Args:
        donor_id: The ID of the donor profile to update
        eligibility_data: Updated eligibility information
        
    Returns:
        The updated donor profile
        
    Raises:
        404: If the donor profile doesn't exist
    """

    donor = await DonorDAO.find_one_or_none(id=donor_id)
    
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor profile not found"
        )
    

    update_data = {
        "is_eligible": eligibility_data.is_eligible,
        "health_notes": eligibility_data.health_notes,
        "ineligible_until": eligibility_data.ineligible_until
    }
    

    if eligibility_data.is_eligible:
        update_data["health_notes"] = None
        update_data["ineligible_until"] = None
    
    updated_donor = await DonorDAO.update(donor_id, **update_data)
    
    return updated_donor


@router.get("/my-eligibility", 
           status_code=status.HTTP_200_OK,
           summary="Check my donation eligibility")
async def check_my_eligibility(current_user: User = Depends(get_current_user)):
    """
    Check your own eligibility to donate blood.
    
    Returns information about your current eligibility status,
    including deferral information and when you'll be eligible again.
    
    Raises:
        403: If you don't have a donor role
        404: If your donor profile doesn't exist
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
    

    today = date.today()
    

    age_eligible = 18 <= donor.age <= 65
    time_eligible = True
    days_until_eligible = 0
    
    if donor.last_donation_date:
        days_since_donation = (today - donor.last_donation_date).days
        time_eligible = days_since_donation >= 56
        if not time_eligible:
            days_until_eligible = 56 - days_since_donation
    

    deferral_eligible = donor.is_eligible
    deferral_days = 0
    
    if not deferral_eligible and donor.ineligible_until:
        deferral_days = (donor.ineligible_until - today).days
    

    can_donate = donor.can_donate
    
    message = ""
    if not can_donate:
        if not age_eligible:
            if donor.age < 18:
                message = "You are too young to donate. Donors must be at least 18 years old."
            else:
                message = "You are over the maximum donation age of 65."
        elif not time_eligible:
            message = f"You donated too recently. You can donate again in {days_until_eligible} days."
        elif not deferral_eligible:
            if donor.ineligible_until:
                message = f"You are temporarily deferred from donating. You can donate again in {deferral_days} days on {donor.ineligible_until.strftime('%B %d, %Y')}."
                if donor.health_notes:
                    message += f" Reason: {donor.health_notes}"
            else:
                message = "You are currently ineligible to donate blood."
                if donor.health_notes:
                    message += f" Reason: {donor.health_notes}"
    else:
        message = "You are eligible to donate blood."
    
    response = {
        "can_donate": can_donate,
        "is_eligible": donor.is_eligible,
        "age_eligible": age_eligible,
        "time_since_last_donation_eligible": time_eligible,
        "ineligible_until": donor.ineligible_until,
        "health_notes": donor.health_notes,
        "message": message
    }
    
    return response