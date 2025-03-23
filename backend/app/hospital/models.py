from sqlalchemy import Enum as SQLEnum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from app.database import Base, int_pk, str_uniq, created_at, updated_at
from app.common.enums import HospitalType


class Hospital(Base):
    __tablename__ = "hospitals"
    
    id: Mapped[int_pk]
    name: Mapped[str_uniq]
    hospital_type: Mapped[str] = mapped_column(SQLEnum(HospitalType), default=HospitalType.GENERAL)

    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(nullable=True)
    region: Mapped[str] = mapped_column(nullable=True)
    country: Mapped[str] = mapped_column(default="Ukraine")

    phone_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    website: Mapped[Optional[str]] = mapped_column(nullable=True)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    staff: Mapped[List["HospitalStaff"]] = relationship("HospitalStaff", back_populates="hospital")
    blood_requests = relationship("BloodRequest", back_populates="hospital")
    
    def __repr__(self):
        return f"Hospital(id={self.id}, name={self.name})"



