from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from app.config import templates
from app.users.dependencies import get_current_hospital_staff
from app.users.models import User
from app.hospital_staff.dao import HospitalStaffDAO
from app.hospital.dao import HospitalDAO
from app.blood_request.dao import BloodRequestDAO
from sqlalchemy import desc
from app.common.enums import RequestStatus, BloodType
from datetime import datetime, timedelta

router = APIRouter(prefix="/pages/hospital_staff", tags=["Hospital Staff Pages"])

@router.get("/dashboard", name="hospital_staff_dashboard")
async def hospital_staff_dashboard(
    request: Request, 
    current_user: User = Depends(get_current_hospital_staff)
):
    """Render the hospital staff dashboard page"""
    
    # Get staff profile with hospital information
    staff_profile = await HospitalStaffDAO.find_one_or_none(
        user_id=current_user.id,
    )
    
    if not staff_profile:
        raise HTTPException(status_code=404, detail="Hospital staff profile not found")
    
    # Get hospital details
    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)
    
    # Get recent blood requests for this hospital (limit to 5)
    recent_requests = await BloodRequestDAO.find_all(
        hospital_id=staff_profile.hospital_id,
        order_by=[desc(BloodRequestDAO.model.request_date)],
        limit=5
    )
    
    # Get blood request stats for this hospital
    pending_count = await BloodRequestDAO.count(
        hospital_id=staff_profile.hospital_id,
        status=RequestStatus.PENDING
    )
    
    approved_count = await BloodRequestDAO.count(
        hospital_id=staff_profile.hospital_id,
        status=RequestStatus.APPROVED
    )
    
    fulfilled_count = await BloodRequestDAO.count(
        hospital_id=staff_profile.hospital_id,
        status=RequestStatus.FULFILLED
    )
    
    critical_count = await BloodRequestDAO.count_by_min_urgency(
        hospital_id=staff_profile.hospital_id,
        urgency_min=4,
        status_list=[RequestStatus.PENDING, RequestStatus.APPROVED]
    )
    
    # Calculate stats for last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    requests_last_30_days = await BloodRequestDAO.count(
        hospital_id=staff_profile.hospital_id,
        request_date_after=thirty_days_ago
    )
    
    fulfilled_last_30_days = await BloodRequestDAO.count(
        hospital_id=staff_profile.hospital_id,
        status=RequestStatus.FULFILLED,
        request_date_after=thirty_days_ago
    )
    
    # Calculate fulfillment rate
    fulfillment_rate = 0
    if requests_last_30_days > 0:
        fulfillment_rate = round((fulfilled_last_30_days / requests_last_30_days) * 100)
    
    # Get request counts by blood type
    blood_type_counts = {}
    for blood_type in BloodType:
        count = await BloodRequestDAO.count(
            hospital_id=staff_profile.hospital_id,
            blood_type=blood_type,
            status_list=[RequestStatus.PENDING, RequestStatus.APPROVED]
        )
        blood_type_counts[blood_type.value] = count
    
    return templates.TemplateResponse(
        "hospital_staff/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "staff": staff_profile,
            "hospital": hospital,
            "recent_requests": recent_requests,
            "stats": {
                "pending_count": pending_count,
                "approved_count": approved_count,
                "fulfilled_count": fulfilled_count,
                "critical_count": critical_count,
                "requests_last_30_days": requests_last_30_days,
                "fulfilled_last_30_days": fulfilled_last_30_days,
                "fulfillment_rate": fulfillment_rate,
                "blood_type_counts": blood_type_counts
            },
            "blood_types": [bt.value for bt in BloodType]
        }
    )

@router.get("/create-blood-request", name="create_blood_request_page")
async def create_blood_request_page(
    request: Request,
    current_user: User = Depends(get_current_hospital_staff)
):
    """Render the create blood request page"""
    
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    if not staff_profile:
        raise HTTPException(status_code=404, detail="Hospital staff profile not found")
    
    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)
    
    return templates.TemplateResponse(
        "hospital_staff/create_request.html",
        {
            "request": request,
            "user": current_user,
            "staff": staff_profile,
            "hospital": hospital,
            "blood_types": [bt.value for bt in BloodType]
        }
    )

@router.get("/blood-requests", name="blood_requests_page")
async def blood_requests_page(
    request: Request,
    current_user: User = Depends(get_current_hospital_staff)
):
    """Render the blood requests management page"""
    
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    if not staff_profile:
        raise HTTPException(status_code=404, detail="Hospital staff profile not found")
    
    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)
    
    return templates.TemplateResponse(
        "hospital_staff/blood_requests.html",
        {
            "request": request,
            "user": current_user,
            "staff": staff_profile,
            "hospital": hospital,
            "statuses": [status.value for status in RequestStatus],
            "blood_types": [bt.value for bt in BloodType]
        }
    )

@router.get("/blood-requests/{request_id}", name="blood_request_detail_page")
async def blood_request_detail_page(
    request: Request,
    request_id: int,
    current_user: User = Depends(get_current_hospital_staff)
):
    """View details of a specific blood request"""
    # Get hospital staff profile
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    
    if not staff_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital staff profile not found"
        )
    
    # Get hospital details separately to avoid detached instance error
    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)
    
    blood_request = await BloodRequestDAO.find_one_with_all_relations(request_id)
    
    if not blood_request or blood_request.hospital_id != staff_profile.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    return templates.TemplateResponse(
        "hospital_staff/request_detail.html",
        {
            "request": request,
            "user": current_user,
            "staff": staff_profile,
            "hospital": hospital,
            "blood_request": blood_request,
            "donations": blood_request.donations if blood_request.donations else []
        }
    )


@router.get("/edit-blood-request/{request_id}", name="edit_blood_request_page")
async def edit_blood_request_page(
    request: Request,
    request_id: int,
    current_user: User = Depends(get_current_hospital_staff)
):
    """Edit a specific blood request"""
    staff_profile = await HospitalStaffDAO.find_one_or_none(user_id=current_user.id)
    
    if not staff_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital staff profile not found"
        )
    
    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)
    
    blood_request = await BloodRequestDAO.find_one_or_none(id=request_id)
    
    if not blood_request or blood_request.hospital_id != staff_profile.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    if blood_request.status not in ["pending", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit a blood request with status '{blood_request.status}'"
        )
    
    return templates.TemplateResponse(
        "hospital_staff/edit_request.html",
        {
            "request": request,
            "user": current_user,
            "staff": staff_profile,
            "hospital": hospital,
            "blood_request": blood_request,
            "blood_types": [bt.value for bt in BloodType]
        }
    )



@router.get("/custom-queries", name="Custom queries")
async def custom_queries_page(
    request: Request,
    current_user: User = Depends(get_current_hospital_staff)
):
    staff_profile = await HospitalStaffDAO.find_one_or_none(
        user_id=current_user.id,
    )

    if not staff_profile:
        raise HTTPException(status_code=404, detail="Hospital staff profile not found")

    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)

    return templates.TemplateResponse(
        "hospital_staff/custom_queries.html", 
        {
            "request": request,
            "user": current_user,
            "staff": staff_profile,
            "hospital": hospital,
        }
    )


@router.get(
    "/advanced-analytics", 
    response_class=HTMLResponse,
    summary="Advanced analytics dashboard",
    description="View advanced analytics and complex queries for blood donation system"
)
async def get_advanced_analytics_page(
    request: Request,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Serves the advanced analytics page for hospital staff.
    This page contains complex parameterized queries for blood donation analysis.
    """
    staff = await HospitalStaffDAO.find_one_or_none(
        user_id=current_user.id,
    )
        
    hospital = await HospitalDAO.find_one_or_none(id=staff.hospital_id)
    
    # Get all hospitals for dropdowns
    all_hospitals = await HospitalDAO.get_all_hospitals(200)
    
    # Get blood types for filtering
    blood_types = [bt.value for bt in BloodType]
    
    return templates.TemplateResponse(
        "hospital_staff/advanced_analytics.html",
        {
            "request": request,
            "user": current_user,
            "staff": staff,
            "hospital": hospital,
            "all_hospitals": all_hospitals,
            "blood_types": blood_types
        }
    )



@router.get("/all-tables", response_class=HTMLResponse)
async def hospital_staff_all_tables(request: Request):
    """Page for viewing all database tables."""
    return templates.TemplateResponse(
        "hospital_staff/all_tables.html",
        {"request": request}
    )


@router.get(
    "/multiple-comparison-analytics", 
    response_class=HTMLResponse,
    name="multiple_comparison_analytics",  
    summary="Multiple Comparison Analytics Dashboard",
    description="View analytics with multiple comparison queries for the blood donation system"
)
async def get_multiple_comparison_analytics_page(
    request: Request,
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Render the multiple comparison analytics dashboard with complex queries
    that compare multiple sets and relationships between entities.
    """
    # Отримуємо профіль персоналу лікарні
    staff_profile = await HospitalStaffDAO.find_one_or_none(
        user_id=current_user.id,
    )
    
    if not staff_profile:
        raise HTTPException(status_code=404, detail="Hospital staff profile not found")
    
    # Отримуємо інформацію про лікарню
    hospital = await HospitalDAO.find_one_or_none(id=staff_profile.hospital_id)
    
    # Отримуємо дані для випадаючих списків
    all_hospitals = await HospitalDAO.get_all_hospitals()
    regions = await HospitalDAO.get_unique_regions()
    blood_types = list(BloodType)
    
    return templates.TemplateResponse(
        "hospital_staff/multiple_comparison_analytics.html",
        {
            "request": request,
            "user": current_user,  # Змінено з "current_user" на "user"
            "staff": staff_profile,  # Додано staff_profile
            "hospital": hospital,    # Додано hospital
            "all_hospitals": all_hospitals,
            "regions": regions, 
            "blood_types": blood_types,
            "page_title": "Аналітика з множинними порівняннями"
        }
    )