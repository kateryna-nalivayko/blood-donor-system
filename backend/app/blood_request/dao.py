from app.dao.base import BaseDAO
from app.blood_request.models import BloodRequest

class BloodRequestDAO(BaseDAO):
    model = BloodRequest