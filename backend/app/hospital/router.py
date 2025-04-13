from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from typing import List, Optional
from app.hospital.schemas import (
    HospitalCreate, 
    HospitalUpdate, 
    HospitalResponse, 
    HospitalListResponse,
    HospitalStatsResponse,
    IdenticalNeedsRequest,
    IdenticalNeedsResponse
)
from app.hospital.dao import HospitalDAO
from app.users.dependencies import get_current_admin_user, get_current_hospital_staff
from app.users.models import User
import math


router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])



@router.post("/", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
async def create_hospital(
    hospital_data: HospitalCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new hospital
    
    Requires admin privileges
    """
    existing_hospital = await HospitalDAO.find_one_or_none(name=hospital_data.name)
    if existing_hospital:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hospital with name '{hospital_data.name}' already exists"
        )
    
    new_hospital = await HospitalDAO.add(**hospital_data.model_dump())
    return new_hospital


@router.get("/", response_model=HospitalListResponse)
async def list_hospitals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for hospital name, city or region")
):
    """
    List hospitals with pagination and optional search
    """
    hospitals, total = await HospitalDAO.find_paginated(page=page, limit=size, search=search)
    
    total_pages = math.ceil(total / size) if total > 0 else 1
    
    return {
        "items": hospitals,
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: int = Path(..., ge=1, description="The ID of the hospital to retrieve")
):
    """
    Get hospital details by ID
    """
    hospital = await HospitalDAO.find_one_or_none_by_id(hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )
    
    return hospital


@router.put("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(
    hospital_data: HospitalUpdate,
    hospital_id: int = Path(..., ge=1, description="The ID of the hospital to update"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update hospital details
    
    Requires admin privileges
    """
    hospital = await HospitalDAO.find_one_or_none_by_id(hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )
    
    if hospital_data.name and hospital_data.name != hospital.name:
        existing_hospital = await HospitalDAO.find_one_or_none(name=hospital_data.name)
        if existing_hospital and existing_hospital.id != hospital_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hospital with name '{hospital_data.name}' already exists"
            )
    
    update_data = {k: v for k, v in hospital_data.model_dump().items() if v is not None}
    updated_hospital = await HospitalDAO.update(hospital_id, **update_data)
    
    return updated_hospital


@router.delete("/{hospital_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital(hospital_id: int = Path(...), current_user: User = Depends(get_current_admin_user)):
    hospital = await HospitalDAO.find_one_or_none_by_id(hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )
    
    can_delete = await HospitalDAO.can_be_deleted(hospital_id)
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete hospital with associated staff or blood requests"
        )
    
    success = await HospitalDAO.delete(hospital_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete hospital"
        )
    
    return None


@router.get("/{hospital_id}/stats", response_model=HospitalStatsResponse)
async def get_hospital_stats(
    hospital_id: int = Path(..., ge=1, description="The ID of the hospital")
):
    """
    Get hospital statistics including staff count, blood requests, and donations
    """
    stats = await HospitalDAO.get_hospital_stats(hospital_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )
    
    return stats


@router.get(
    "/analytics/identical-needs",
    response_model=List[IdenticalNeedsResponse],
    summary="Find hospitals with identical blood type needs",
    description="Finds hospitals that have exactly the same blood type shortage patterns as a reference hospital"
)
async def get_hospitals_with_identical_needs(
    query: IdenticalNeedsRequest = Depends(),
    current_user: User = Depends(get_current_hospital_staff)
):
    """
    Find hospitals with identical blood type needs as a reference hospital.
    Useful for coordinating donation campaigns across hospitals with similar shortages.
    """
    return await HospitalDAO.find_hospitals_with_identical_needs(
        reference_hospital_id=query.reference_hospital_id,
        time_period_days=query.time_period_days,
        min_shortage_percent=query.min_shortage_percent,
        limit=query.limit
    )