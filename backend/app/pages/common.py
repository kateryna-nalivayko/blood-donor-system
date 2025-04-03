from fastapi import APIRouter, Request, Depends, HTTPException
from app.config import templates
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(tags=["Pages"])


@router.get("/", name="home")
async def home(request: Request):
    return templates.TemplateResponse("index.html",
                                      {
                                          "request": request
                                      })