from fastapi import APIRouter, Request, Depends
from app.config import templates
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/pages", tags=["Auth Pages"])


@router.get("/register", name="register_page")
async def register_page(request: Request):
    """
    Render the user registration page.
    """
    return templates.TemplateResponse("auth/register_form.html", {"request": request})


@router.get("/login", name="login_page")
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login_form.html", {"request": request})


@router.get("/profile", name="profile_page")
async def profile_page(request: Request, current_user: User = Depends(get_current_user)):
    """
    Render the user profile page.
    Requires authenticated user.
    """
    return templates.TemplateResponse("auth/profile.html", 
                                     {"request": request, 
                                      "user": current_user})
