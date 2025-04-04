from fastapi import APIRouter, Depends, Request
from app.config import templates
from app.donor.dao import DonorDAO
from app.hospital.dao import HospitalDAO
from app.donation.dao import DonationDAO
from app.users.dao import UsersDAO
from app.database import async_session_maker
from sqlalchemy import func, select
from app.donation.models import Donation
from app.common.enums import DonationStatus
from app.users.dependencies import get_current_user_optional
from app.users.models import User

router = APIRouter(prefix="", tags=["Common Pages"])

@router.get("/", name="home_page")
async def home(request: Request, current_user: User = Depends(get_current_user_optional)):
    """
    Render the home page with statistics based on the database models.
    """
    stats = {
        "donor_count": 0,
        "hospital_count": 0,
        "donation_count": 0,
        "lives_saved": 0,
        "blood_volume_ml": 0,
        "active_requests": 0
    }
    
    try:
        if hasattr(UsersDAO, "count"):
            async with async_session_maker() as session:
                donor_count_query = select(func.count()).select_from(UsersDAO.model).where(
                    UsersDAO.model.is_donor == True
                )
                stats["donor_count"] = await session.scalar(donor_count_query) or 0
        
        if hasattr(HospitalDAO, "count"):
            stats["hospital_count"] = await HospitalDAO.count()
        
        if hasattr(DonationDAO, "count"):
            async with async_session_maker() as session:
                completed_donations_query = select(func.count()).select_from(Donation).where(
                    Donation.status == DonationStatus.COMPLETED
                )
                completed_donations = await session.scalar(completed_donations_query) or 0
                stats["donation_count"] = completed_donations
                
                blood_volume_query = select(func.sum(Donation.blood_amount_ml)).select_from(Donation).where(
                    Donation.status == DonationStatus.COMPLETED
                )
                total_blood_volume = await session.scalar(blood_volume_query) or 0
                stats["blood_volume_ml"] = total_blood_volume
                
                stats["lives_saved"] = completed_donations * 3
                
                if hasattr(session, "execute"):
                    try:
                        from app.blood_request.models import BloodRequest
                        from app.common.enums import RequestStatus
                        
                        active_requests_query = select(func.count()).select_from(BloodRequest).where(
                            BloodRequest.status == RequestStatus.ACTIVE
                        )
                        stats["active_requests"] = await session.scalar(active_requests_query) or 0
                    except (ImportError, AttributeError):
                        pass
    except Exception as e:
        print(f"Error fetching stats: {e}")
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "stats": stats, "user": current_user}
    )