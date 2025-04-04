import math
from typing import Optional
from fastapi import APIRouter, Query, Request, Depends, HTTPException, status
from app.common.enums import HospitalType
from app.config import templates
from app.users.dependencies import get_current_admin_user
from app.users.models import User
from app.users.dao import UsersDAO
from app.hospital.dao import HospitalDAO
from app.blood_request.dao import BloodRequestDAO
from app.donor.dao import DonorDAO

router = APIRouter(prefix="/pages/admin", tags=["Admin Pages"])


@router.get("/dashboard", name="admin_dashboard")
async def admin_dashboard(request: Request, current_user: User = Depends(get_current_admin_user)):
    """
    Render the admin dashboard main page.
    """
    user_count = await UsersDAO.count()
    hospital_count = await HospitalDAO.count() if hasattr(HospitalDAO, "count") else 0
    blood_request_count = await BloodRequestDAO.count() if hasattr(BloodRequestDAO, "count") else 0
    donor_count = await DonorDAO.count() if hasattr(DonorDAO, "count") else 0
    
    # Get recent users for dashboard display
    recent_users = await UsersDAO.find_recent(limit=5)
    
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {
            "request": request, 
            "user": current_user,
            "user_count": user_count,
            "hospital_count": hospital_count,
            "blood_request_count": blood_request_count,
            "donor_count": donor_count,
            "recent_users": recent_users
        }
    )


@router.get("/users", name="admin_users_list")
async def admin_users_list(
    request: Request, 
    current_user: User = Depends(get_current_admin_user),
    page: int = 1,
    search: str = ""
):
    """
    Render the user management page.
    """
    # Get paginated list of users
    # Assuming you have these methods in your DAO
    users_per_page = 10
    
    if search:
        users, total = await UsersDAO.search_paginated(
            search_term=search,
            page=page,
            limit=users_per_page
        )
    else:
        users, total = await UsersDAO.find_paginated(
            page=page, 
            limit=users_per_page
        )
    
    total_pages = (total + users_per_page - 1) // users_per_page
    
    return templates.TemplateResponse(
        "admin/users/list.html", 
        {
            "request": request,
            "user": current_user,
            "users": users,
            "page": page,
            "total_pages": total_pages,
            "total_users": total,
            "search": search
        }
    )


@router.get("/users/{user_id}/edit", name="admin_edit_user")
async def admin_edit_user(
    request: Request, 
    user_id: int,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Render the edit user page.
    """
    user_to_edit = await UsersDAO.find_one_or_none(id=user_id)
    
    if not user_to_edit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return templates.TemplateResponse(
        "admin/users/edit.html", 
        {
            "request": request,
            "user": current_user,
            "edit_user": user_to_edit
        }
    )


@router.get("/hospitals", name="admin_hospitals_list")
async def admin_hospitals_list(
    request: Request, 
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Render the hospitals management page.
    """
    # Get hospitals with pagination
    page_size = 10
    hospitals, total = await HospitalDAO.find_paginated(page=page, limit=page_size, search=search)
    
    # Calculate pagination data
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return templates.TemplateResponse(
        "admin/hospitals/list.html",
        {
            "request": request,
            "user": current_user,
            "hospitals": hospitals,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or ""
        }
    )



@router.get("/hospitals/create", name="hospital_create_page")
async def hospital_create_page(
    request: Request,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Render hospital creation page
    
    Requires admin privileges
    """
    return templates.TemplateResponse(
        "admin/hospitals/create.html",
        {
            "request": request,
            "user": current_user,
            "hospital_types": [e.value for e in HospitalType]
        }
    )


@router.get("/hospitals/{hospital_id}/edit", name="hospital_edit_page")
async def hospital_edit_page(
    request: Request,
    hospital_id: int,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Render hospital edit page
    
    Requires admin privileges
    """
    # Get hospital data
    hospital = await HospitalDAO.find_one_or_none_by_id(hospital_id)
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    # Get hospital stats
    stats = await HospitalDAO.get_hospital_stats(hospital_id)
    
    return templates.TemplateResponse(
        "admin/hospitals/edit.html",
        {
            "request": request,
            "user": current_user,
            "hospital": hospital,
            "stats": stats,
            "hospital_types": [e.value for e in HospitalType]
        }
    )