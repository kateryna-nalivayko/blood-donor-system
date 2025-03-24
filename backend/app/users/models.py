from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, created_at, updated_at


class User(Base):
    __tablename__ = "users"
    id: Mapped[int_pk]
    phone_number: Mapped[str_uniq]
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str_uniq]
    password: Mapped[str]

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    is_donor: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    is_hospital_staff: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    donor_profile = relationship("Donor", back_populates="user")
    hospital_staff_profile = relationship("HospitalStaff", back_populates="user")

    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"