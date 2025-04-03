from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.users.router import router as router_users
from app.donor.router import router as router_donors
from app.hospital_staff.router import router as router_hospitall_staff
from app.donation.router import router as router_donation
from app.blood_request.router import router as blood_request_router

from app.pages.common import router as common_pages_router


app = FastAPI(
    title="Blood Donor System",
    description="API for managing blood donations, donors, and blood request.",
    version="0.1.0",
)


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


app.include_router(router_users)
app.include_router(router_donors)
app.include_router(router_hospitall_staff)
app.include_router(router_donation)
app.include_router(blood_request_router)

app.include_router(common_pages_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)