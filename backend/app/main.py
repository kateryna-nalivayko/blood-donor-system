from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.users.router import router as router_users


app = FastAPI(
    title="Blood Donor System",
    description="API for managing blood donations, donors, and blood request.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Blood Donor System API is running"}


app.include_router(router_users)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)