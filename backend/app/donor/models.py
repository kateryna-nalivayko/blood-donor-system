from sqlalchemy import ForeignKey, text, Text, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date
from typing import List, Optional
from app.database import Base, int_pk, created_at, updated_at
from app.common.enums import BloodType
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Donor(Base):
    __tablename__ = "donors"
    
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(nullable=False)

    blood_type: Mapped[str] = mapped_column(SQLEnum(BloodType), nullable=False)

    weight: Mapped[float] = mapped_column(
        CheckConstraint("weight >= 50", name="donor_min_weight_check"),
        nullable=False,
        comment="Weight in kilograms, minimum 50kg required"
    )
    height: Mapped[float] = mapped_column(
        CheckConstraint("height BETWEEN 120 AND 220", name="donor_height_range_check"),
        nullable=False,
        comment="Height in centimeters"
    )

    last_donation_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    first_donation_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    total_donations: Mapped[int] = mapped_column(default=0, server_default=text('0'))


    is_eligible: Mapped[bool] = mapped_column(default=True, server_default=text('true'))
    ineligible_until: Mapped[Optional[date]] = mapped_column(nullable=True)
    health_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    
    user: Mapped["User"] = relationship("User", back_populates="donor_profile")
    donations: Mapped[List["Donation"]] = relationship("Donation", back_populates="donor")


    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def can_donate(self) -> bool:
        today = date.today()
        age_eligible = 18 <= self.age <= 65
        
        time_eligible = True
        if self.last_donation_date:
            days_since_donation = (today - self.last_donation_date).days
            time_eligible = days_since_donation >= 56
            
        return self.is_eligible and age_eligible and time_eligible

    
    def __repr__(self):
        return f"Donor(id={self.id}, user_id={self.user_id}, blood_type={self.blood_type})"