from app.dao.base import BaseDAO
from app.hospital.models import Hospital

class HospitalDAO(BaseDAO):
    model = Hospital