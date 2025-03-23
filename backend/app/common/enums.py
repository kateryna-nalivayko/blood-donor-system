from enum import Enum

class BloodType(str, Enum):
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"


class StaffRole(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class Department(str, Enum):
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    CARDIOLOGY = "cardiology"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    ADMINISTRATION = "administration"


class HospitalType(str, Enum):
    GENERAL = "general"
    SPECIALIZED = "specialized"
    UNIVERSITY = "university"
    PRIVATE = "private"
    CLINIC = "clinic"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"


class DonationStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELED = "canceled"
    REJECTED = "rejected"