from sqlalchemy import ForeignKey, Text, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional
from app.database import Base, int_pk, created_at, updated_at
from app.common.enums import BloodType, DonationStatus



class Donation(Base):
    __tablename__ = "donations"
    
    id: Mapped[int_pk]
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id"))
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    blood_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("blood_requests.id"), nullable=True
    )
    
    blood_amount_ml: Mapped[int] = mapped_column(
        CheckConstraint("blood_amount_ml BETWEEN 100 AND 1000", name="valid_blood_amount"),
        nullable=False,
        comment="Amount of blood donated in milliliters (100-1000ml)"
    )
    blood_type: Mapped[BloodType] = mapped_column(SQLEnum(BloodType), nullable=False)
    donation_date: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(),
        nullable=False
    )
    
    status: Mapped[DonationStatus] = mapped_column(
        SQLEnum(DonationStatus), 
        default=DonationStatus.SCHEDULED
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    
    donor: Mapped["Donor"] = relationship("Donor", back_populates="donations")
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="donations")
    blood_request: Mapped[Optional["BloodRequest"]] = relationship(
        "BloodRequest", back_populates="donations"
    )
    
    def __repr__(self):
        return f"Donation(id={self.id}, donor_id={self.donor_id}, status={self.status})"
    
    def complete(self) -> bool:
        """Mark donation as completed if it's in scheduled state."""
        if self.status == DonationStatus.SCHEDULED:
            self.status = DonationStatus.COMPLETED
            return True
        return False
    
    def cancel(self, reason: Optional[str] = None) -> bool:
        """Cancel the donation if it's scheduled."""
        if self.status == DonationStatus.SCHEDULED:
            self.status = DonationStatus.CANCELED
            if reason:
                self.notes = f"Canceled: {reason}"
            return True
        return False
    
    @property
    def is_completed(self) -> bool:
        """Check if donation has been completed."""
        return self.status == DonationStatus.COMPLETED