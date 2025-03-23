from sqlalchemy import ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
from enum import Enum as PyEnum
from app.database import Base, int_pk, created_at, updated_at
from app.common.enums import StaffRole, Department

class HospitalStaff(Base):
    __tablename__ = "hospital_staff"
    
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))

    role: Mapped[str] = mapped_column(SQLEnum(StaffRole), default=StaffRole.DOCTOR, nullable=True)
    department: Mapped[str] = mapped_column(SQLEnum(Department), nullable=True)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    

    user: Mapped["User"] = relationship("User", back_populates="hospital_staff_profile")
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="staff")
    blood_requests: Mapped[List["BloodRequest"]] = relationship("BloodRequest", back_populates="staff")
    
    def __repr__(self):
        return f"HospitalStaff(id={self.id}, user_id={self.user_id}, hospital_id={self.hospital_id})"