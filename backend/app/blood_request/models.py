from sqlalchemy import ForeignKey, Text, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import Base, int_pk, created_at, updated_at
from app.common.enums import BloodType, RequestStatus


class BloodRequest(Base):
    __tablename__ = "blood_requests"
    
    id: Mapped[int_pk]
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    staff_id: Mapped[int] = mapped_column(ForeignKey("hospital_staff.id"))
    
    blood_type: Mapped[BloodType] = mapped_column(SQLEnum(BloodType), nullable=False)
    amount_needed_ml: Mapped[int] = mapped_column(
        CheckConstraint("amount_needed_ml BETWEEN 100 AND 10000", name="valid_blood_amount"),
        nullable=False,
        comment="Amount of blood needed in milliliters"
    )

    patient_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urgency_level: Mapped[int] = mapped_column(
        CheckConstraint("urgency_level BETWEEN 1 AND 5", name="valid_urgency_level"),
        default=3,
        comment="Urgency scale: 1 (low) to 5 (critical)"
    )
    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(RequestStatus), 
        default=RequestStatus.PENDING
    )
    
    request_date: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now().replace(tzinfo=None)
    )
    needed_by_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    

    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="blood_requests")
    staff: Mapped["HospitalStaff"] = relationship("HospitalStaff", back_populates="blood_requests")
    donations: Mapped[List["Donation"]] = relationship(
        "Donation", 
        primaryjoin="BloodRequest.id==Donation.blood_request_id",
        back_populates="blood_request"
    )
    
    def __repr__(self):
        return f"BloodRequest(id={self.id}, blood_type={self.blood_type}, status={self.status})"
    
    @property
    def is_fulfilled(self) -> bool:
        """Check if the request has been fulfilled."""
        return self.status == RequestStatus.FULFILLED
    
    @property
    def days_until_needed(self) -> Optional[int]:
        """Calculate days remaining until blood is needed."""
        if not self.needed_by_date:
            return None
        return (self.needed_by_date - datetime.now()).days
    
    @property
    def collected_amount_ml(self) -> int:
        """Calculate the total amount of blood collected for this request."""
        return sum(donation.blood_amount_ml for donation in self.donations 
                  if donation.status == "completed")
    
    @property
    def fulfillment_percentage(self) -> float:
        """Calculate what percentage of the requested blood has been collected."""
        if self.amount_needed_ml == 0:
            return 0
        return min(100.0, (self.collected_amount_ml / self.amount_needed_ml) * 100)