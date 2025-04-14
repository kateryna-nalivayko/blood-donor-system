from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.users.dependencies import get_current_user
from app.users.models import User
from app.dao.tables import TablesDAO

router = APIRouter(
    prefix="/tables",
    tags=["tables"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/{table_name}", response_model=Dict[str, Any])
async def get_table_data(
    table_name: str,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    search: Optional[str] = None
):
    """
    Get paginated data from a specific database table.
    Only hospital staff and admins can access this endpoint.
    """
    if not (current_user.is_hospital_staff or current_user.is_admin):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this data"
        )
    
    allowed_tables = [
        "users", "donors", "hospitals",
        "hospital_staff", "blood_requests", "donations"
    ]
    
    if table_name not in allowed_tables:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid table name. Must be one of: {', '.join(allowed_tables)}"
        )
    
    data = await TablesDAO.get_table_data(
        table_name=table_name,
        page=page,
        limit=limit,
        search=search
    )
    
    return data